import sqlite3
import pytest

from config.settings import settings
from src.utils.tracing import LLMTracer, trace_llm


# Helper to initialize a temporary trace database

def setup_db(tmp_path):
    settings.trace_db_path = str(tmp_path / "traces.db")
    LLMTracer(settings.trace_db_path)


@trace_llm
def dummy_call(model_name: str = "my-model"):
    return {
        "answer": "ok",
        "tokens_input": 10,
        "tokens_output": 10,
        "model_info": {"selected_model": model_name},
    }


def test_cost_reporting_with_price_change(tmp_path):
    setup_db(tmp_path)
    settings.model_prices = {"my-model": 0.03}

    for _ in range(100):
        dummy_call()

    with sqlite3.connect(settings.trace_db_path) as conn:
        total_tokens, total_cost = conn.execute(
            "SELECT SUM(prompt_tokens + completion_tokens), SUM(cost_usd) FROM llm_traces"
        ).fetchone()

    assert total_tokens == 2000
    assert total_cost == pytest.approx(2000 / 1000 * 0.03)

    settings.model_prices["my-model"] = 0.06
    dummy_call()

    with sqlite3.connect(settings.trace_db_path) as conn:
        last_tokens, last_cost = conn.execute(
            "SELECT prompt_tokens + completion_tokens, cost_usd FROM llm_traces ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert last_tokens == 20
    assert last_cost == pytest.approx(20 / 1000 * 0.06)
