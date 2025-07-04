import contextvars
import os
import queue
import sqlite3
import time
import uuid
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional, Sequence

from config.settings import settings
from src.utils.exceptions import TracingException
from src.utils.logger import setup_logger
from src.utils.metrics import record_latency

logger = setup_logger()

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
        self.duration_ms: Optional[float] = None
        self.docs_count: Optional[int] = None
        self.model_name: Optional[str] = None
        self.selection_reason: Optional[str] = None

    def finish(self, status: str, error: Optional[str] = None) -> None:
        self.end_time = time.perf_counter()
        self.status = status
        self.error = error
        if self.end_time is not None:
            self.duration_ms = (self.end_time - self.start_time) * 1000


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
        """Create or migrate the llm_traces table."""
        with sqlite3.connect(self.db_path) as conn:
            columns = [row[1] for row in conn.execute("PRAGMA table_info(llm_traces)")]
            if not columns:
                conn.execute(
                    """
                    CREATE TABLE llm_traces (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        model TEXT,
                        temperature REAL,
                        prompt TEXT,
                        prompt_tokens INTEGER,
                        completion_tokens INTEGER,
                        latency_ms REAL,
                        cost_usd REAL,
                        status TEXT,
                        error TEXT
                    )
                    """
                )
            else:
                if "prompt_tokens" not in columns:
                    if "tokens_input" in columns:
                        conn.execute(
                            "ALTER TABLE llm_traces RENAME COLUMN tokens_input TO prompt_tokens"
                        )
                    else:
                        conn.execute(
                            "ALTER TABLE llm_traces ADD COLUMN prompt_tokens INTEGER"
                        )
                if "completion_tokens" not in columns:
                    if "tokens_output" in columns:
                        conn.execute(
                            "ALTER TABLE llm_traces RENAME COLUMN tokens_output TO completion_tokens"
                        )
                    else:
                        conn.execute(
                            "ALTER TABLE llm_traces ADD COLUMN completion_tokens INTEGER"
                        )
            conn.commit()

    def log_trace(self, data: Dict[str, Any]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO llm_traces (
                    timestamp, model, temperature, prompt,
                    prompt_tokens, completion_tokens, latency_ms,
                    cost_usd, status, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data.get("timestamp"),
                    data.get("model"),
                    data.get("temperature"),
                    data.get("prompt"),
                    data.get("prompt_tokens") or data.get("tokens_input"),
                    data.get("completion_tokens") or data.get("tokens_output"),
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
        span = ctx.start_span("synthesize") if ctx else None
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
                prompt_tokens = (
                    result.get("prompt_tokens")
                    or result.get("tokens_input")
                    or usage.get("prompt_tokens")
                    or usage.get("input_tokens")
                )
                completion_tokens = (
                    result.get("completion_tokens")
                    or result.get("tokens_output")
                    or usage.get("completion_tokens")
                    or usage.get("output_tokens")
                )
            else:
                prompt_tokens = kwargs.get("prompt_tokens") or kwargs.get(
                    "tokens_input"
                )
                completion_tokens = kwargs.get("completion_tokens") or kwargs.get(
                    "tokens_output"
                )
            if prompt_tokens is None:
                prompt_tokens = kwargs.get("tokens_input")
            if completion_tokens is None:
                completion_tokens = kwargs.get("tokens_output")
            cost_usd = None
            if prompt_tokens is not None or completion_tokens is not None:
                ti = prompt_tokens or 0
                to = completion_tokens or 0
                price = settings.model_prices.get(model)
                if price is not None:
                    cost_usd = (ti + to) / 1000 * price
            tracer_db.log_trace(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": model,
                    "temperature": temperature,
                    "prompt": prompt,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "latency_ms": latency_ms,
                    "cost_usd": cost_usd,
                    "status": status,
                    "error": error,
                }
            )
            record_latency("synthesize", latency_ms, settings.synthesize_sla_ms)
            if ctx and span:
                ctx.end_span(span, status, error)
        return result

    return wrapper


def trace_retrieval(func: Callable) -> Callable:
    """Decorator to trace retrieval operations."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ctx = get_current_tracer()
        span = ctx.start_span("retrieve") if ctx else None
        start = time.perf_counter()
        docs_count = 0
        status = "success"
        error: Optional[str] = None
        try:
            result = func(*args, **kwargs)
            if isinstance(result, Sequence):
                docs_count = len(result)
            return result
        except Exception as exc:
            status = "error"
            error = str(exc)
            raise
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            record_latency("search", latency_ms, settings.search_sla_ms)
            if ctx and span:
                span.docs_count = docs_count if status == "success" else 0
                ctx.end_span(span, status, error)

    return wrapper


def trace_model_selection(func: Callable) -> Callable:
    """Decorator to trace model selection operations."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ctx = get_current_tracer()
        span = ctx.start_span("select_model") if ctx else None
        start = time.perf_counter()
        status = "success"
        error: Optional[str] = None
        model_name: Optional[str] = None
        reason: Optional[str] = None
        try:
            result = func(*args, **kwargs)
            if isinstance(result, tuple) and len(result) >= 3:
                model_name = result[0]
                reason = result[2]
            return result
        except Exception as exc:
            status = "error"
            error = str(exc)
            raise
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            record_latency("model_select", latency_ms)
            if ctx and span:
                if len({settings.simple_model, settings.complex_model}) >= 2:
                    span.model_name = model_name
                    span.selection_reason = reason
                ctx.end_span(span, status, error)
            if model_name is None and settings.log_level == "DEBUG":
                logger.warning("No model selected in model selector")

    return wrapper
