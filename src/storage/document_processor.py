# -*- coding: utf-8 -*-
import os
from pathlib import Path
from typing import List, Optional

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    pd = None  # type: ignore
    PANDAS_AVAILABLE = False

try:
    import psycopg2
except ImportError:  # pragma: no cover - optional dependency
    psycopg2 = None  # type: ignore

try:
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import (Docx2txtLoader,
                                                      PyPDFLoader, TextLoader)
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
                        "type": "excel",
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
                        "type": "excel",
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
                        "type": "excel",
                        "error": "processing_error",
                        "error_details": str(e),
                    },
                )
            ]


import time

from config.settings import settings
from src.utils.exceptions import DocumentProcessingException
from src.utils.logger import setup_logger
from src.utils.metrics import record_latency
from src.utils.tracing import get_current_tracer

logger = setup_logger()


class DocumentProcessor:
    """Procesador de documentos con múltiples formatos y manejo robusto de dependencias"""

    def __init__(self):
        # Configurar text splitter con fallback si LangChain no está disponible
        if RecursiveCharacterTextSplitter is None:
            # Implementación simple de fallback que divide por párrafos
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
                                        metadata=doc.metadata,
                                    )
                                )
                    return chunks

            self.text_splitter = _SimpleSplitter()
            logger.info("Using simple text splitter (LangChain not available)")
        else:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
            logger.info("Using LangChain RecursiveCharacterTextSplitter")

        # ======= MAPEO DE LOADERS CON VERIFICACIÓN INTELIGENTE =======
        # Empezar con loaders básicos que siempre están disponibles
        self.loader_mapping = {
            ".txt": TextLoader,
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

        # Log final de formatos soportados
        supported_formats = list(self.loader_mapping.keys())
        logger.info(
            f"Document processor initialized with support for: {', '.join(supported_formats)}"
        )

    def _safe_load_file(self, file_path: Path, loader_class):
        """
        Carga segura de archivos con manejo comprehensivo de errores.

        Esta función implementa múltiples capas de protección para asegurar
        que un archivo problemático nunca cause falla del sistema completo.
        """
        try:
            file_size_mb = file_path.stat().st_size / 1024 / 1024
            logger.info(f"Loading file: {file_path.name} ({file_size_mb:.1f} MB)")

            # Advertencia para archivos muy grandes
            if file_size_mb > 50:
                logger.warning(
                    f"Large file detected: {file_path.name} ({file_size_mb:.1f} MB). "
                    f"Processing may take longer than usual."
                )

            # Verificar que el loader está disponible
            if loader_class is None:
                logger.error(f"No loader available for {file_path.suffix}")
                return []

            # Intentar cargar el archivo
            loader = loader_class(str(file_path))
            docs = loader.load()

            # Verificar que se extrajo contenido
            if not docs:
                logger.warning(f"No content extracted from {file_path}")
                return []

            # Verificar que los documentos tienen contenido real
            valid_docs = []
            for doc in docs:
                if doc.page_content and doc.page_content.strip():
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
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in self.loader_mapping
                    and not file_path.name.startswith(".")
                    and file_path.name != ".gitkeep"
                ):
                    supported_files.append(file_path)

            if not supported_files:
                logger.warning(f"No supported files found in {documents_path}")
                return []

            logger.info(f"Found {len(supported_files)} supported files to process")

            # Procesar cada archivo individualmente
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
                                    "file_type": file_path.suffix.lower(),
                                    "file_name": file_path.name,
                                    "processed_at": time.time(),
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
            logger.error(f"Error in document loading process: {e}")
            raise DocumentProcessingException(f"Failed to load documents: {e}")

    def split_documents(self, documents):
        """Divide documentos en chunks con monitoreo de performance"""
        tracer = get_current_tracer()
        span = tracer.start_span("chunk") if tracer else None
        start = time.perf_counter()

        try:
            if not documents:
                logger.warning("No documents to split")
                return []

            logger.info(f"Splitting {len(documents)} documents into chunks...")

            # Procesar en lotes para manejar memoria eficientemente
            all_chunks = []
            batch_size = 10
            total_batches = (len(documents) + batch_size - 1) // batch_size

            for i in range(0, len(documents), batch_size):
                batch_num = (i // batch_size) + 1
                batch = documents[i : i + batch_size]

                try:
                    logger.debug(f"Processing batch {batch_num}/{total_batches}")
                    batch_chunks = self.text_splitter.split_documents(batch)
                    all_chunks.extend(batch_chunks)
                    logger.debug(
                        f"Batch {batch_num} produced {len(batch_chunks)} chunks"
                    )

                except Exception as e:
                    logger.error(f"Error processing batch {batch_num}: {e}")
                    continue

            logger.info(f"Total chunks created: {len(all_chunks)}")

            # Filtrar chunks vacíos
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
        finally:
            duration = (time.perf_counter() - start) * 1000
            record_latency("chunk", duration, settings.chunk_sla_ms)
            if tracer and span:
                tracer.end_span(span, "success")

    def load_from_postgres(self, conn_str: str, query: str) -> List[Document]:
        """Carga datos desde PostgreSQL con manejo de dependencias"""
        if psycopg2 is None or not PANDAS_AVAILABLE:
            raise DocumentProcessingException(
                "PostgreSQL support requires psycopg2 and pandas. "
                "Install with: pip install psycopg2-binary pandas"
            )
        try:
            logger.info("Loading data from PostgreSQL...")
            with psycopg2.connect(conn_str) as conn:
                df = pd.read_sql_query(query, conn)
            text = df.astype(str).fillna("").agg(" ".join, axis=1).str.cat(sep="\n")
            return [Document(page_content=text, metadata={"source": "postgres"})]
        except Exception as e:
            logger.error(f"Error loading data from PostgreSQL: {e}")
            raise DocumentProcessingException(
                f"Failed to load data from PostgreSQL: {e}"
            )

    def process_documents(self, path: Optional[str] = None):
        """Pipeline completo de procesamiento con logging detallado"""
        try:
            logger.info("Starting document processing pipeline...")
            pipeline_start = time.perf_counter()

            # Fase 1: Cargar documentos
            logger.info("Phase 1: Loading documents from filesystem...")
            documents = self.load_documents(path)
            if not documents:
                logger.warning(
                    "No documents loaded - pipeline completed with empty result"
                )
                return []

            # Fase 2: Dividir en chunks
            logger.info("Phase 2: Splitting documents into chunks...")
            chunks = self.split_documents(documents)
            if not chunks:
                logger.warning("No chunks created from documents")
                return []

            # Resumen final
            pipeline_duration = (time.perf_counter() - pipeline_start) * 1000
            logger.info(f"Document processing pipeline completed successfully:")
            logger.info(f"  - Processing time: {pipeline_duration:.1f}ms")
            logger.info(f"  - Input documents: {len(documents)}")
            logger.info(f"  - Output chunks: {len(chunks)}")
            logger.info(
                f"  - Average chunks per document: {len(chunks)/len(documents):.1f}"
            )

            return chunks

        except Exception as e:
            logger.error(f"Error in document processing pipeline: {e}")
            raise DocumentProcessingException(f"Document processing failed: {e}")

    def get_file_info(self, path: Optional[str] = None) -> dict:
        """Obtiene información detallada sobre archivos en el directorio"""
        documents_path = Path(path or settings.documents_path)

        if not documents_path.exists():
            return {"error": "Directory does not exist", "path": str(documents_path)}

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
