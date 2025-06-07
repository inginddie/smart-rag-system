# -*- coding: utf-8 -*-
import pytest
import tempfile
import os
from pathlib import Path
from src.services.rag_service import RAGService
from src.utils.exceptions import RAGException

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
        os.environ["DOCUMENTS_PATH"] = temp_dir
        os.environ["VECTOR_DB_PATH"] = str(Path(temp_dir) / "vector_db")
        os.environ["OPENAI_API_KEY"] = "test-key"
        
        rag_service = RAGService()
        result = rag_service.initialize()

        # La inicialización debería fallar debido a la falta de documentos
        assert result is False
    
    def test_query_without_initialization(self):
        """Test de consulta sin inicialización"""
        os.environ["OPENAI_API_KEY"] = "test-key"
        rag_service = RAGService()
        
        with pytest.raises(RAGException):
            rag_service.query("test question")
