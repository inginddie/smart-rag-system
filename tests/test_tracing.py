import sqlite3

from config.settings import settings
from src.utils.tracing import LLMTracer, trace_llm


def setup_temp_db(tmp_path):
    settings.trace_db_path = str(tmp_path / "traces.db")
    return LLMTracer(settings.trace_db_path)


def create_dummy():
    @trace_llm
    def dummy(query: str, model_name: str = "test-model"):
        return {"answer": "ok", "model_info": {"selected_model": model_name}}

    return dummy


def test_trace_success_status(tmp_path):
    tracer = setup_temp_db(tmp_path)
    dummy = create_dummy()
    dummy("hola")
    conn = sqlite3.connect(settings.trace_db_path)
    row = conn.execute("SELECT status FROM llm_traces").fetchone()
    conn.close()
    assert row[0] == "success"


def test_trace_contains_prompt_and_model(tmp_path):
    tracer = setup_temp_db(tmp_path)
    dummy = create_dummy()
    dummy("mundo")
    conn = sqlite3.connect(settings.trace_db_path)
    row = conn.execute("SELECT prompt, model FROM llm_traces").fetchone()
    conn.close()
    assert row[0] == "mundo"
    assert row[1] == "test-model"
