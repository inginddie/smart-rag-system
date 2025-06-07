# -*- coding: utf-8 -*-
import os
from typing import List, Optional
from pathlib import Path

try:
    import pandas as pd
except ImportError:  # pragma: no cover - optional dependency
    pd = None  # type: ignore

try:
    import psycopg2
except ImportError:  # pragma: no cover - optional dependency
    psycopg2 = None  # type: ignore
try:
    from langchain_community.document_loaders import (
        TextLoader,
        PyPDFLoader,
        Docx2txtLoader,
    )
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
except ImportError:  # pragma: no cover - optional dependency
    TextLoader = PyPDFLoader = Docx2txtLoader = None  # type: ignore
    RecursiveCharacterTextSplitter = None  # type: ignore
    from dataclasses import dataclass

    @dataclass
    class Document:
        page_content: str
        metadata: dict

    class TextLoader:
        def __init__(self, path: str):
            self.path = path

        def load(self):
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read()
            return [Document(page_content=content, metadata={})]

    class ExcelLoader:
        def __init__(self, path: str):
            self.path = path

        def load(self):
            if pd is None:
                raise ImportError("pandas is required for Excel loading")
            df = pd.read_excel(self.path, engine="openpyxl")
            text = (
                df.astype(str)
                .fillna("")
                .agg(" ".join, axis=1)
                .str.cat(sep="\n")
            )
            return [Document(page_content=text, metadata={})]
from config.settings import settings
from src.utils.logger import setup_logger
from src.utils.exceptions import DocumentProcessingException

logger = setup_logger()

class DocumentProcessor:
    """Procesador de documentos con múltiples formatos"""
    
    def __init__(self):
        if RecursiveCharacterTextSplitter is None:
            class _SimpleSplitter:
                def split_documents(self, docs):
                    chunks = []
                    for doc in docs:
                        text = doc.page_content
                        for part in text.split("\n\n"):
                            chunks.append(Document(page_content=part, metadata=doc.metadata))
                    return chunks

            self.text_splitter = _SimpleSplitter()
        else:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
        
        # Mapeo de extensiones a loaders
        self.loader_mapping = {
            '.txt': TextLoader,
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.xls': ExcelLoader,
            '.xlsx': ExcelLoader,
        }
    
    def _safe_load_file(self, file_path: Path, loader_class):
        """Carga segura de archivos con manejo de errores"""
        try:
            logger.info(f"Loading file: {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.1f} MB)")

            # Para PDFs grandes, usar configuración especial
            if file_path.suffix.lower() == '.pdf' and file_path.stat().st_size > 10 * 1024 * 1024:  # > 10MB
                logger.warning(f"Large PDF detected: {file_path.name}. Processing with special handling...")

            if loader_class is None:
                logger.error(f"No loader available for {file_path.suffix}")
                return []

            loader = loader_class(str(file_path))
            docs = loader.load()
            
            if not docs:
                logger.warning(f"No content extracted from {file_path}")
                return []
            
            logger.info(f"Successfully loaded {len(docs)} pages from {file_path.name}")
            return docs
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {str(e)[:200]}...")
            return []
    
    def load_documents(self, path: Optional[str] = None):
        """Carga documentos desde un directorio"""
        documents_path = Path(path or settings.documents_path)
        
        if not documents_path.exists():
            logger.warning(f"Documents path does not exist: {documents_path}")
            return []
        
        try:
            all_documents = []
            
            # Obtener todos los archivos soportados
            supported_files = []
            for file_path in documents_path.rglob("*"):
                if (file_path.is_file() and 
                    file_path.suffix.lower() in self.loader_mapping and
                    not file_path.name.startswith('.') and
                    file_path.name != '.gitkeep'):
                    supported_files.append(file_path)
            
            if not supported_files:
                logger.warning("No supported files found")
                return []
            
            logger.info(f"Found {len(supported_files)} supported files")
            
            # Procesar archivos uno por uno
            for file_path in supported_files:
                logger.info(f"Processing: {file_path.name}")
                
                loader_class = self.loader_mapping[file_path.suffix.lower()]
                docs = self._safe_load_file(file_path, loader_class)
                
                if docs:
                    # Agregar metadata a cada documento
                    for doc in docs:
                        doc.metadata.update({
                            'source_file': str(file_path),
                            'file_type': file_path.suffix.lower(),
                            'file_name': file_path.name
                        })
                    
                    all_documents.extend(docs)
                    logger.info(f"Added {len(docs)} documents from {file_path.name}")
                else:
                    logger.warning(f"Skipped {file_path.name} (no content extracted)")
            
            logger.info(f"Total documents loaded: {len(all_documents)}")
            return all_documents
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            raise DocumentProcessingException(f"Failed to load documents: {e}")
    
    def split_documents(self, documents):
        """Divide documentos en chunks"""
        try:
            if not documents:
                logger.warning("No documents to split")
                return []
            
            logger.info(f"Splitting {len(documents)} documents into chunks...")
            
            # Procesar documentos en lotes para evitar problemas de memoria
            all_chunks = []
            batch_size = 10
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                try:
                    batch_chunks = self.text_splitter.split_documents(batch)
                    all_chunks.extend(batch_chunks)
                    logger.info(f"Processed batch {i//batch_size + 1}: {len(batch_chunks)} chunks")
                except Exception as e:
                    logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                    continue
            
            logger.info(f"Total chunks created: {len(all_chunks)}")
            
            # Verificar que los chunks no están vacíos
            valid_chunks = [chunk for chunk in all_chunks if chunk.page_content.strip()]
            
            if len(valid_chunks) != len(all_chunks):
                logger.warning(f"Removed {len(all_chunks) - len(valid_chunks)} empty chunks")
            
            return valid_chunks
            
        except Exception as e:
            logger.error(f"Error splitting documents: {e}")
            raise DocumentProcessingException(f"Failed to split documents: {e}")

    def load_from_postgres(self, conn_str: str, query: str) -> List[Document]:
        """Carga datos desde una base de datos PostgreSQL"""
        if psycopg2 is None or pd is None:
            raise DocumentProcessingException(
                "PostgreSQL support requires psycopg2 and pandas"
            )
        try:
            logger.info("Loading data from PostgreSQL...")
            with psycopg2.connect(conn_str) as conn:
                df = pd.read_sql_query(query, conn)
            text = (
                df.astype(str)
                .fillna("")
                .agg(" ".join, axis=1)
                .str.cat(sep="\n")
            )
            return [Document(page_content=text, metadata={"source": "postgres"})]
        except Exception as e:
            logger.error(f"Error loading data from PostgreSQL: {e}")
            raise DocumentProcessingException(
                f"Failed to load data from PostgreSQL: {e}"
            )
    
    def process_documents(self, path: Optional[str] = None):
        """Pipeline completo de procesamiento"""
        try:
            logger.info("Starting document processing pipeline...")
            
            # Cargar documentos
            documents = self.load_documents(path)
            if not documents:
                logger.warning("No documents to process")
                return []
            
            # Dividir en chunks
            chunks = self.split_documents(documents)
            if not chunks:
                logger.warning("No chunks created from documents")
                return []
            
            logger.info(f"Document processing completed: {len(chunks)} chunks ready for indexing")
            return chunks
            
        except Exception as e:
            logger.error(f"Error in document processing pipeline: {e}")
            raise DocumentProcessingException(f"Document processing failed: {e}")
    
    def get_file_info(self, path: Optional[str] = None) -> dict:
        """Obtiene información sobre los archivos en el directorio"""
        documents_path = Path(path or settings.documents_path)
        
        if not documents_path.exists():
            return {"error": "Directory does not exist"}
        
        files_info = []
        total_size = 0
        
        for file_path in documents_path.rglob("*"):
            if (file_path.is_file() and 
                file_path.suffix.lower() in self.loader_mapping and
                not file_path.name.startswith('.') and
                file_path.name != '.gitkeep'):
                
                size_mb = file_path.stat().st_size / 1024 / 1024
                total_size += size_mb
                
                files_info.append({
                    'name': file_path.name,
                    'type': file_path.suffix.lower(),
                    'size_mb': round(size_mb, 2)
                })
        
        return {
            'total_files': len(files_info),
            'total_size_mb': round(total_size, 2),
            'files': files_info
        }