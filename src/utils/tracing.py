import os
import sqlite3
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional

from config.settings import settings


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
        tracer = LLMTracer()
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
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
            tracer.log_trace(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": model,
                    "temperature": temperature,
                    "prompt": prompt,
                    "tokens_input": tokens_input,
                    "tokens_output": tokens_output,
                    "latency_ms": latency_ms,
                    "cost_usd": cost_usd,
                    "status": "success",
                    "error": None,
                }
            )
            return result
        except Exception as exc:
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
            tracer.log_trace(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": model,
                    "temperature": temperature,
                    "prompt": prompt,
                    "tokens_input": kwargs.get("tokens_input"),
                    "tokens_output": kwargs.get("tokens_output"),
                    "latency_ms": latency_ms,
                    "cost_usd": None,
                    "status": "error",
                    "error": str(exc),
                }
            )
            raise

    return wrapper
