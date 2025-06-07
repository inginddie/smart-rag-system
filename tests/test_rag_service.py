# -*- coding: utf-8 -*-
import pytest
import tempfile
import os
import logging
from pathlib import Path
from src.services.rag_service import RAGService
from src.utils.exceptions import RAGException
from config.settings import settings

class TestRAGService:
    """Tests para RAG Service"""
    
    @pytest.fixture
    def temp_dir(self):
        """Directorio temporal para tests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def sample_document(self, temp_dir):
        """Crea un documento de ejemplo"""
        doc_path = Path(temp_dir) / "test_doc.txt"
        doc_path.write_text("Este es un documento de prueba con información importante.")
        return str(doc_path)
    
    def test_initialization_without_documents(self, temp_dir):
        """Test de inicialización sin documentos"""
        # Configurar paths temporales
        settings.documents_path = temp_dir
        settings.vector_db_path = str(Path(temp_dir) / "vector_db")
        settings.openai_api_key = "test-key"

        rag_service = RAGService()
        result = rag_service.initialize()

        # La inicialización debería fallar debido a la falta de documentos
        assert result is False

    def test_initialization_without_documents_logs_warning(self, temp_dir, caplog):
        """La inicialización debe registrar advertencia cuando no hay documentos"""
        settings.documents_path = temp_dir
        settings.vector_db_path = str(Path(temp_dir) / "vector_db")
        settings.openai_api_key = "test-key"

        rag_service = RAGService()
        with caplog.at_level(logging.WARNING):
            result = rag_service.initialize()

        assert result is False
        assert any("No documents" in rec.message for rec in caplog.records)
    
    def test_query_without_initialization(self):
        """Test de consulta sin inicialización"""
        settings.openai_api_key = "test-key"
        rag_service = RAGService()

        with pytest.raises(RAGException):
            rag_service.query("test question")

    def test_initialization_with_document(self, temp_dir, sample_document, monkeypatch):
        """La inicialización debería ser exitosa cuando hay documentos"""
        settings.documents_path = temp_dir
        settings.vector_db_path = str(Path(temp_dir) / "vector_db")
        settings.openai_api_key = "test-key"

        rag_service = RAGService()

        monkeypatch.setattr(rag_service.vector_store_manager, "load_and_index_documents", lambda: 1)
        monkeypatch.setattr(rag_service, "_needs_indexing", lambda: True)
        monkeypatch.setattr(rag_service.rag_chain, "create_chain", lambda: None)

        result = rag_service.initialize()

        assert result is True

    def test_query_returns_answer_with_sources(self, monkeypatch, temp_dir):
        """La consulta debe devolver respuesta y fuentes"""
        settings.openai_api_key = "test-key"
        rag_service = RAGService()
        rag_service._initialized = True

        from src.storage.document_processor import Document

        sample_docs = [Document(page_content="Contenido de ejemplo", metadata={"source_file": "doc1.txt"})]

        def fake_invoke(question):
            return {
                "answer": "Respuesta generada",
                "context": sample_docs,
                "model_info": {
                    "selected_model": "fake-model",
                    "complexity_score": 0.4,
                    "reasoning": "mock",
                },
            }

        monkeypatch.setattr(rag_service.rag_chain, "invoke", fake_invoke)

        response = rag_service.query("Pregunta de prueba", include_sources=True)

        assert response["answer"] == "Respuesta generada"
        assert response["question"] == "Pregunta de prueba"
        assert response["model_info"]["selected_model"] == "fake-model"
        assert response["sources"][0]["metadata"]["source_file"] == "doc1.txt"
