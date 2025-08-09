# -*- coding: utf-8 -*-
import os
from typing import List, Optional
from pathlib import Path
from functools import partial

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
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

# ======= DEFINICIÓN CONDICIONAL CORRECTA DE ExcelLoader =======
class ExcelLoader:
    """
    Loader para archivos Excel que maneja dependencias opcionales de manera elegante.

    Esta clase siempre existe independientemente de si pandas está instalado,
    pero su comportamiento cambia según la disponibilidad de dependencias.
    """

    def __init__(self, path: str):
        self.path = path

    def load(self):
        """
        Carga archivos Excel si pandas está disponible, sino retorna error informativo.

        Este approach asegura que el sistema nunca falle por dependencias faltantes,
        pero proporciona feedback claro sobre qué se necesita para habilitar la funcionalidad.
        """
        if not PANDAS_AVAILABLE:
            # En lugar de fallar, retornamos un documento que explica la situación
            error_msg = (
                f"Cannot process Excel file {self.path}: pandas is not installed. "
                f"To enable Excel support, install pandas and openpyxl: "
                f"pip install pandas openpyxl"
            )
            return [
                Document(
                    page_content=error_msg,
                    metadata={
                        "source": self.path,
                        "doc_type": "excel",
                        "error": "missing_dependency",
                        "required_packages": ["pandas", "openpyxl"],
                    },
                )
            ]

        try:
            # pandas está disponible, intentar procesar el archivo
            df = pd.read_excel(self.path, engine="openpyxl")

            # Convertir DataFrame a texto preservando estructura
            if df.empty:
                content = f"Excel file {self.path} is empty"
            else:
                # Crear representación textual del DataFrame
                content = f"Excel file: {self.path}\n\n"
                content += f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n\n"

                # Agregar headers si existen
                if not df.columns.empty:
                    content += f"Columns: {', '.join(df.columns.astype(str))}\n\n"

                # Convertir datos a texto línea por línea
                text_rows = []
                for index, row in df.iterrows():
                    row_text = " | ".join(row.astype(str).fillna(""))
                    text_rows.append(row_text)

                content += "\n".join(text_rows)

            return [
                Document(
                    page_content=content,
                    metadata={
                        "source": self.path,
                        "doc_type": "excel",
                        "rows": df.shape[0] if not df.empty else 0,
                        "columns": df.shape[1] if not df.empty else 0,
                    },
                )
            ]

        except Exception as e:
            # Error procesando el archivo específico
            error_msg = f"Error processing Excel file {self.path}: {str(e)}"
            return [
                Document(
                    page_content=error_msg,
                    metadata={
                        "source": self.path,
                        "doc_type": "excel",
                        "error": "processing_error",
                        "error_details": str(e),
                    },
                )
            ]


class ParserLoader:
    """Loader that delegates to :mod:`document_parser` for OCR processing."""

    def __init__(self, path: str, parser, lang: str):
        self.path = path
        self.parser = parser
        self.lang = lang

    def load(self):
        return self.parser.parse(self.path, lang=self.lang)


import time

from config.settings import settings
from src.utils.logger import setup_logger
from src.utils.exceptions import DocumentProcessingException
from src.storage import document_parser as DocumentParser

logger = setup_logger()

class DocumentProcessor:
    """Procesador de documentos con múltiples formatos"""

    def __init__(self, parser=None, ocr_lang: str = "spa+eng"):
        self.parser = parser or DocumentParser
        self.ocr_lang = ocr_lang

        if RecursiveCharacterTextSplitter is None:
            class _SimpleSplitter:
                def split_documents(self, docs):
                    chunks = []
                    for doc in docs:
                        text = doc.page_content
                        # Dividir por párrafos dobles primero, luego por párrafos simples
                        paragraphs = text.split("\n\n")
                        for paragraph in paragraphs:
                            if paragraph.strip():  # Solo agregar párrafos no vacíos
                                chunks.append(
                                    Document(
                                        page_content=paragraph.strip(),
                                        metadata=doc.metadata.copy(),
                                    )
                                )
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

        # Agregar loaders opcionales según disponibilidad
        if PyPDFLoader is not None:
            self.loader_mapping[".pdf"] = PyPDFLoader
            logger.debug("PDF support enabled")
        else:
            logger.warning("PDF support disabled (PyPDFLoader not available)")

        if Docx2txtLoader is not None:
            self.loader_mapping[".docx"] = Docx2txtLoader
            logger.debug("DOCX support enabled")
        else:
            logger.warning("DOCX support disabled (Docx2txtLoader not available)")

        # ExcelLoader siempre está disponible, pero su comportamiento depende de pandas
        self.loader_mapping[".xls"] = ExcelLoader
        self.loader_mapping[".xlsx"] = ExcelLoader

        if PANDAS_AVAILABLE:
            logger.info("Excel support fully enabled (pandas available)")
        else:
            logger.warning(
                "Excel support limited (pandas not available). "
                "Excel files will generate informative error messages. "
                "Install pandas and openpyxl to enable full Excel processing."
            )

        parser_loader = partial(ParserLoader, parser=self.parser, lang=self.ocr_lang)
        self.loader_mapping[".jpg"] = parser_loader
        self.loader_mapping[".jpeg"] = parser_loader
        self.loader_mapping[".png"] = parser_loader
        self.loader_mapping[".tiff"] = parser_loader

        # Log final de formatos soportados
        supported_formats = list(self.loader_mapping.keys())
        logger.info(
            f"Document processor initialized with support for: {', '.join(supported_formats)}"
        )

    def _infer_doc_type(self, suffix: str) -> str:
        """Map file suffix to a standardized document type."""
        suffix = suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif"}:
            return "image"
        if suffix == ".pdf":
            return "pdf"
        if suffix in {".xls", ".xlsx"}:
            return "excel"
        if suffix == ".docx":
            return "docx"
        if suffix == ".txt":
            return "text"
        return suffix.lstrip('.')

    def _safe_load_file(self, file_path: Path, loader_class):
        """
        Carga segura de archivos con manejo comprehensivo de errores.

        Esta función implementa múltiples capas de protección para asegurar
        que un archivo problemático nunca cause falla del sistema completo.
        """
        try:
            logger.info(f"Loading file: {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.1f} MB)")

            # Para PDFs grandes, usar configuración especial
            if file_path.suffix.lower() == '.pdf' and file_path.stat().st_size > 10 * 1024 * 1024:  # > 10MB
                logger.warning(f"Large PDF detected: {file_path.name}. Processing with special handling...")

            use_ocr = (
                file_path.suffix.lower() == '.pdf'
                and self.parser.needs_ocr(str(file_path))
            )

            if use_ocr:
                logger.info(f"OCR required for {file_path.name}, using parser")
                docs = self.parser.parse(str(file_path), lang=self.ocr_lang)
            else:
                if loader_class is None:
                    logger.error(f"No loader available for {file_path.suffix}")
                    return []

                loader = loader_class(str(file_path))
                docs = loader.load()
            
            if not docs:
                logger.warning(f"No content extracted from {file_path}")
                return []

            # Verificar que los documentos tienen contenido real
            valid_docs = []
            for doc in docs:
                if doc.page_content and doc.page_content.strip():
                    if use_ocr:
                        doc.metadata.setdefault("ocr", True)
                        doc.metadata.setdefault("ocr_lang", self.ocr_lang)
                    else:
                        doc.metadata.setdefault("ocr", False)

                    # Ensure standard metadata fields
                    doc.metadata.setdefault(
                        "doc_type", self._infer_doc_type(file_path.suffix.lower())
                    )
                    doc.metadata.setdefault(
                        "page_number", doc.metadata.get("page", 1)
                    )
                    doc.metadata.pop("page", None)
                    doc.metadata.setdefault("section_title", None)

                    valid_docs.append(doc)
                else:
                    logger.debug(f"Skipping empty document from {file_path}")

            if valid_docs:
                logger.info(
                    f"Successfully loaded {len(valid_docs)} documents from {file_path.name}"
                )
                return valid_docs
            else:
                logger.warning(f"All documents from {file_path} were empty")
                return []

        except Exception as e:
            # Log detallado del error para debugging
            error_msg = str(e)
            logger.error(f"Error loading {file_path}: {error_msg[:200]}...")

            # Para archivos Excel, el ExcelLoader ya maneja errores internamente
            # Para otros tipos, retornamos lista vacía para continuar procesamiento
            return []
    
    def load_documents(self, path: Optional[str] = None):
        """
        Carga documentos desde un directorio con procesamiento robusto.

        Esta función implementa un approach de "mejor esfuerzo" donde problemas
        con archivos individuales no impiden el procesamiento del resto.
        """
        documents_path = Path(path or settings.documents_path)
        
        if not documents_path.exists():
            logger.warning(f"Documents path does not exist: {documents_path}")
            return []
        
        try:
            all_documents = []
            skipped_files = []

            # Buscar todos los archivos soportados
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
                try:
                    logger.debug(f"Processing: {file_path.name}")

                    loader_class = self.loader_mapping[file_path.suffix.lower()]
                    docs = self._safe_load_file(file_path, loader_class)

                    if docs:
                        # Enriquecer metadata de cada documento
                        for doc in docs:
                            doc.metadata.update(
                                {
                                    "source_file": str(file_path),
                                    "doc_type": doc.metadata.get(
                                        "doc_type", self._infer_doc_type(file_path.suffix.lower())
                                    ),
                                    "file_name": file_path.name,
                                    "processed_at": time.time(),
                                    "page_number": doc.metadata.get("page_number", 1),
                                    "section_title": doc.metadata.get("section_title"),
                                }
                            )

                        all_documents.extend(docs)
                        logger.info(
                            f"✓ Added {len(docs)} documents from {file_path.name}"
                        )
                    else:
                        skipped_files.append(file_path.name)
                        logger.warning(
                            f"✗ Skipped {file_path.name} (no content extracted)"
                        )

                except Exception as e:
                    skipped_files.append(file_path.name)
                    logger.error(f"✗ Failed to process {file_path.name}: {e}")
                    continue

            # Resumen final del procesamiento
            logger.info(f"Document loading completed:")
            logger.info(
                f"  - Successfully processed: {len(supported_files) - len(skipped_files)} files"
            )
            logger.info(f"  - Total documents loaded: {len(all_documents)}")
            if skipped_files:
                logger.info(
                    f"  - Skipped files: {len(skipped_files)} ({', '.join(skipped_files[:3])}{'...' if len(skipped_files) > 3 else ''})"
                )

            
            return all_documents
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            raise DocumentProcessingException(f"Failed to load documents: {e}")
    
    def split_documents(self, documents):
        """Divide documentos en chunks con monitoreo de performance"""
        try:
            if not documents:
                logger.warning("No documents to split")
                return []
            
            logger.info(f"Splitting {len(documents)} documents into chunks...")
            
            # Procesar documentos en lotes para evitar problemas de memoria
            all_chunks = []
            batch_size = 10
            
            for i in range(0, len(documents), batch_size):
                batch_num = (i // batch_size) + 1
                batch = documents[i : i + batch_size]

                
                try:
                    batch_chunks = self.text_splitter.split_documents(batch)
                    # Ensure metadata propagation
                    for chunk in batch_chunks:
                        chunk.metadata.setdefault("doc_type", chunk.metadata.get("doc_type"))
                        chunk.metadata.setdefault(
                            "page_number", chunk.metadata.get("page_number", 1)
                        )
                        chunk.metadata.setdefault(
                            "section_title", chunk.metadata.get("section_title")
                        )
                    all_chunks.extend(batch_chunks)
                    logger.debug(
                        f"Batch {batch_num} produced {len(batch_chunks)} chunks"
                    )

                    
                except Exception as e:
                    logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                    continue
            
            logger.info(f"Total chunks created: {len(all_chunks)}")
            
            # Verificar que los chunks no están vacíos
            valid_chunks = [chunk for chunk in all_chunks if chunk.page_content.strip()]
            
            if len(valid_chunks) != len(all_chunks):
                removed_count = len(all_chunks) - len(valid_chunks)
                logger.info(f"Removed {removed_count} empty chunks")

            logger.info(
                f"Document splitting completed: {len(valid_chunks)} valid chunks ready"
            )
            
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
                logger.warning(
                    "No documents loaded - pipeline completed with empty result"
                )
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
        
        supported_count = 0
        unsupported_count = 0
        
        for file_path in documents_path.rglob("*"):
            if (
                file_path.is_file()
                and not file_path.name.startswith(".")
                and file_path.name != ".gitkeep"
            ):
                size_mb = file_path.stat().st_size / 1024 / 1024
                total_size += size_mb

                is_supported = file_path.suffix.lower() in self.loader_mapping
                if is_supported:
                    supported_count += 1
                else:
                    unsupported_count += 1

                files_info.append(
                    {
                        "name": file_path.name,
                        "type": file_path.suffix.lower(),
                        "size_mb": round(size_mb, 2),
                        "supported": is_supported,
                    }
                )

        return {
            "total_files": len(files_info),
            "supported_files": supported_count,
            "unsupported_files": unsupported_count,
            "total_size_mb": round(total_size, 2),
            "supported_formats": list(self.loader_mapping.keys()),
            "files": files_info,
            "pandas_available": PANDAS_AVAILABLE,
        }
