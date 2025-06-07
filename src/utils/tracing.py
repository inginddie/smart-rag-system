import contextvars
import os
import queue
import sqlite3
import time
import uuid
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional

from config.settings import settings
from src.utils.exceptions import TracingException

TRACE_QUEUE: "queue.Queue" = queue.Queue()
_current_tracer: "contextvars.ContextVar[Optional['Tracer']]" = contextvars.ContextVar(
    "current_tracer", default=None
)


class Span:
    """Simple span representation for tracing"""

    def __init__(self, name: str, trace_id: str, parent_span_id: Optional[str]) -> None:
        self.span_id = uuid.uuid4().hex
        self.trace_id = trace_id
        self.parent_span_id = parent_span_id
        self.name = name
        self.start_time = time.perf_counter()
        self.end_time: Optional[float] = None
        self.status: Optional[str] = None
        self.error: Optional[str] = None

    def finish(self, status: str, error: Optional[str] = None) -> None:
        self.end_time = time.perf_counter()
        self.status = status
        self.error = error


class Tracer:
    """Context manager to group spans into a single trace."""

    def __init__(self) -> None:
        self.trace_id = uuid.uuid4().hex
        self._spans: list[Span] = []
        self._stack: list[str] = []
        self._token: Optional[contextvars.Token] = None

    def __enter__(self) -> "Tracer":
        self._token = _current_tracer.set(self)
        return self

    def start_span(self, name: str) -> Span:
        parent_id = self._stack[-1] if self._stack else None
        span = Span(name, self.trace_id, parent_id)
        self._spans.append(span)
        self._stack.append(span.span_id)
        return span

    def end_span(self, span: Span, status: str, error: Optional[str] = None) -> None:
        span.finish(status, error)
        if self._stack:
            self._stack.pop()

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._token is not None:
            _current_tracer.reset(self._token)
        TRACE_QUEUE.put(
            {"trace_id": self.trace_id, "spans": [vars(s) for s in self._spans]}
        )
        return False


def get_current_tracer() -> Optional[Tracer]:
    """Return the active tracer if any."""
    return _current_tracer.get()


def requires_tracer(func: Callable) -> Callable:
    """Ensure that the wrapped function is executed within a tracer context."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if get_current_tracer() is None:
            raise TracingException("Pipeline executed outside tracer context")
        return func(*args, **kwargs)

    return wrapper


class LLMTracer:
    """Simple tracer that stores LLM calls in a SQLite database."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or settings.trace_db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    model TEXT,
                    temperature REAL,
                    prompt TEXT,
                    tokens_input INTEGER,
                    tokens_output INTEGER,
                    latency_ms REAL,
                    cost_usd REAL,
                    status TEXT,
                    error TEXT
                )
                """
            )
            conn.commit()

    def log_trace(self, data: Dict[str, Any]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO llm_traces (
                    timestamp, model, temperature, prompt,
                    tokens_input, tokens_output, latency_ms,
                    cost_usd, status, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data.get("timestamp"),
                    data.get("model"),
                    data.get("temperature"),
                    data.get("prompt"),
                    data.get("tokens_input"),
                    data.get("tokens_output"),
                    data.get("latency_ms"),
                    data.get("cost_usd"),
                    data.get("status"),
                    data.get("error"),
                ),
            )
            conn.commit()


def trace_llm(func: Callable) -> Callable:
    """Decorator to trace LLM calls."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tracer_db = LLMTracer()
        start = time.perf_counter()
        ctx = get_current_tracer()
        span = ctx.start_span(func.__name__) if ctx else None
        try:
            result = func(*args, **kwargs)
            status = "success"
            error = None
        except Exception as exc:
            status = "error"
            error = str(exc)
            result = None
            raise
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            prompt = kwargs.get("query")
            if prompt is None:
                if len(args) == 1:
                    prompt = args[0]
                elif len(args) >= 2:
                    prompt = args[1]
            temperature = kwargs.get("temperature")
            self_obj = args[0] if args else None
            if temperature is None and hasattr(self_obj, "temperature"):
                temperature = getattr(self_obj, "temperature")
            model = kwargs.get("model_name") or kwargs.get("model")
            if isinstance(result, dict):
                model = model or result.get("model")
                model = model or result.get("model_info", {}).get("selected_model")
                usage = (
                    result.get("usage", {})
                    if isinstance(result.get("usage"), dict)
                    else {}
                )
                tokens_input = (
                    result.get("tokens_input")
                    or usage.get("prompt_tokens")
                    or usage.get("input_tokens")
                )
                tokens_output = (
                    result.get("tokens_output")
                    or usage.get("completion_tokens")
                    or usage.get("output_tokens")
                )
            else:
                tokens_input = kwargs.get("tokens_input")
                tokens_output = kwargs.get("tokens_output")
            if tokens_input is None:
                tokens_input = kwargs.get("tokens_input")
            if tokens_output is None:
                tokens_output = kwargs.get("tokens_output")
            cost_usd = None
            if tokens_input is not None or tokens_output is not None:
                ti = tokens_input or 0
                to = tokens_output or 0
                cost_usd = (ti + to) / 1000 * 0.002
            tracer_db.log_trace(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": model,
                    "temperature": temperature,
                    "prompt": prompt,
                    "tokens_input": tokens_input,
                    "tokens_output": tokens_output,
                    "latency_ms": latency_ms,
                    "cost_usd": cost_usd,
                    "status": status,
                    "error": error,
                }
            )
            if ctx and span:
                ctx.end_span(span, status, error)
        return result

    return wrapper
