import sqlite3

import pytest

from config.settings import settings
from src.utils.exceptions import TracingException
from src.utils.tracing import (
    TRACE_QUEUE,
    LLMTracer,
    Tracer,
    get_current_tracer,
    requires_tracer,
    trace_llm,
)
from src.storage.vector_store import VectorStoreManager
from src.utils.exceptions import VectorStoreException


def setup_temp_db(tmp_path):
    settings.trace_db_path = str(tmp_path / "traces.db")
    return LLMTracer(settings.trace_db_path)


def create_dummy():
    @trace_llm
    def dummy(query: str, model_name: str = "test-model"):
        return {"answer": "ok", "model_info": {"selected_model": model_name}}

    return dummy


@requires_tracer
def pipeline():
    tracer = get_current_tracer()
    root = tracer.start_span("pipeline")
    dummy = create_dummy()
    dummy("hola")
    tracer.end_span(root, "success")


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


def test_trace_table_has_token_columns(tmp_path):
    tracer = setup_temp_db(tmp_path)
    dummy = create_dummy()
    dummy("hola")
    conn = sqlite3.connect(settings.trace_db_path)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(llm_traces)").fetchall()]
    conn.close()
    assert "prompt_tokens" in cols
    assert "completion_tokens" in cols


def test_pipeline_tracing_hierarchy(tmp_path):
    setup_temp_db(tmp_path)
    while not TRACE_QUEUE.empty():
        TRACE_QUEUE.get()
    with Tracer() as t:
        pipeline()
    trace = TRACE_QUEUE.get_nowait()
    assert trace["trace_id"] == t.trace_id
    spans = trace["spans"]
    assert len(spans) == 2
    root_span = next(s for s in spans if s["parent_span_id"] is None)
    child_span = next(s for s in spans if s["parent_span_id"] == root_span["span_id"])
    assert child_span["trace_id"] == root_span["trace_id"]
    assert "duration_ms" in child_span


def test_span_records_duration(tmp_path):
    setup_temp_db(tmp_path)
    while not TRACE_QUEUE.empty():
        TRACE_QUEUE.get()
    with Tracer():
        dummy = create_dummy()
        dummy("hola")
    trace = TRACE_QUEUE.get_nowait()
    span = trace["spans"][0]
    assert span.get("duration_ms") is not None


def test_pipeline_outside_context_error():
    with pytest.raises(TracingException):
        pipeline()


class FakeCollection:
    def count(self):
        return 2


class FakeVectorStore:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self._collection = FakeCollection()

    def similarity_search(self, query: str, k: int = 5):
        if self.fail:
            raise RuntimeError("fail")
        return ["doc1", "doc2"]


def clear_queue():
    while not TRACE_QUEUE.empty():
        TRACE_QUEUE.get()


def test_trace_retrieval_success(monkeypatch):
    manager = VectorStoreManager()
    monkeypatch.setattr(
        VectorStoreManager,
        "vector_store",
        property(lambda self: FakeVectorStore()),
    )
    clear_queue()
    with Tracer():
        manager.similarity_search("hola")
    trace = TRACE_QUEUE.get_nowait()
    span = trace["spans"][0]
    assert span["status"] == "success"
    assert span.get("duration_ms") is not None
    assert span.get("docs_count", 0) > 0


def test_trace_retrieval_error(monkeypatch):
    manager = VectorStoreManager()
    monkeypatch.setattr(
        VectorStoreManager,
        "vector_store",
        property(lambda self: FakeVectorStore(fail=True)),
    )
    clear_queue()
    with Tracer():
        with pytest.raises(VectorStoreException):
            manager.similarity_search("boom")
    trace = TRACE_QUEUE.get_nowait()
    span = trace["spans"][0]
    assert span["status"] == "error"
    assert span.get("docs_count") == 0
    assert span.get("error")
