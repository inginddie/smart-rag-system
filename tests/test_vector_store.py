# -*- coding: utf-8 -*-
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.storage.document_processor import DocumentProcessor
from src.storage.vector_store import VectorStoreManager


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
        assert documents[0].metadata["source_file"] == str(test_file)

    def test_document_processor_with_excel_file(self, temp_dir):
        """Test procesamiento de archivo Excel"""
        pd = pytest.importorskip("pandas")
        pytest.importorskip("openpyxl")  # Skip if openpyxl not available

        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        excel_path = Path(temp_dir) / "test.xlsx"
        df.to_excel(excel_path, index=False)

        processor = DocumentProcessor()
        documents = processor.load_documents(temp_dir)

        assert len(documents) == 1
        assert "a" in documents[0].page_content

    def test_load_from_postgres(self, monkeypatch):
        """Test carga de datos desde PostgreSQL"""
        pd = pytest.importorskip("pandas")
        pytest.importorskip("psycopg2")  # Skip if psycopg2 not available

        sample_df = pd.DataFrame({"text": ["fila1", "fila2"]})

        monkeypatch.setattr(
            "pandas.read_sql_query",
            lambda query, conn: sample_df,
        )

        class FakeConn:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                pass

        # Use a different approach that works with missing modules
        with patch('src.storage.document_processor.psycopg2') as mock_psycopg2:
            mock_psycopg2.connect.return_value = FakeConn()
            
            processor = DocumentProcessor()
            docs = processor.load_from_postgres("dsn", "SELECT 1")
            assert len(docs) == 1
            assert "fila1" in docs[0].page_content
