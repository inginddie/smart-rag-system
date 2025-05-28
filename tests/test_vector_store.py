# -*- coding: utf-8 -*-
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from src.storage.vector_store import VectorStoreManager
from src.storage.document_processor import DocumentProcessor

class TestVectorStore:
    """Tests para Vector Store"""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_document_processor_load_empty_directory(self, temp_dir):
        """Test carga de directorio vacío"""
        processor = DocumentProcessor()
        documents = processor.load_documents(temp_dir)
        assert len(documents) == 0
    
    def test_document_processor_with_text_file(self, temp_dir):
        """Test procesamiento de archivo de texto"""
        # Crear archivo de prueba
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Este es un documento de prueba para testing.")
        
        processor = DocumentProcessor()
        documents = processor.load_documents(temp_dir)
        
        assert len(documents) == 1
        assert "prueba" in documents[0].page_content
        assert documents[0].metadata['source_file'] == str(test_file)
