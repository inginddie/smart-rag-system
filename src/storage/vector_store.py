# -*- coding: utf-8 -*-
import os
import shutil
from typing import List, Optional
from pathlib import Path
try:
    from langchain_chroma import Chroma
    from langchain.schema import Document
    import chromadb
except ImportError:  # pragma: no cover - optional dependency
    Chroma = None  # type: ignore
    Document = None  # type: ignore
    chromadb = None  # type: ignore
from config.settings import settings
from src.models.embeddings import EmbeddingManager
from src.storage.document_processor import DocumentProcessor
from src.utils.logger import setup_logger
from src.utils.exceptions import VectorStoreException
from src.utils.metrics import record_latency
from src.utils.tracing import get_current_tracer, trace_retrieval
import time

logger = setup_logger()

class VectorStoreManager:
    """Maneja la base de datos vectorial"""
    
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or settings.vector_db_path
        self.embedding_manager = EmbeddingManager()
        self.document_processor = DocumentProcessor()
        self._vector_store = None
        self._collection_name = "langchain"
        
        # Crear directorio si no existe
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
    
    def _reset_vector_store(self):
        """Reinicia la base de datos vectorial completamente"""
        try:
            logger.info("Resetting vector store...")
            
            # Cerrar vector store actual si existe
            if self._vector_store:
                try:
                    self._vector_store.delete_collection()
                except:
                    pass
                self._vector_store = None
            
            # Eliminar directorio completo
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
                logger.info(f"Removed existing vector store at: {self.persist_directory}")
            
            # Recrear directorio
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created new vector store directory: {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Error resetting vector store: {e}")
            raise VectorStoreException(f"Failed to reset vector store: {e}")
    
    def _initialize_chroma_client(self):
        """Inicializa el cliente Chroma directamente"""
        try:
            if chromadb is None:
                raise VectorStoreException(
                    "chromadb dependency is required but not installed"
                )
            # Crear cliente Chroma persistente
            client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Intentar obtener o crear colección
            try:
                collection = client.get_collection(name=self._collection_name)
                logger.info(f"Found existing collection: {self._collection_name}")
            except:
                # Si no existe, crear nueva colección
                collection = client.create_collection(
                    name=self._collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Created new collection: {self._collection_name}")
            
            return client
            
        except Exception as e:
            logger.error(f"Error initializing Chroma client: {e}")
            raise VectorStoreException(f"Failed to initialize Chroma client: {e}")
    
    @property
    def vector_store(self):
        """Lazy loading de vector store con inicialización robusta"""
        if Chroma is None:
            raise VectorStoreException(
                "langchain-chroma dependency is required but not installed"
            )
        if self._vector_store is None:
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Initializing vector store (attempt {attempt + 1}/{max_retries})")
                    
                    # Inicializar cliente Chroma primero
                    client = self._initialize_chroma_client()
                    
                    # Crear vector store de LangChain
                    self._vector_store = Chroma(
                        client=client,
                        collection_name=self._collection_name,
                        embedding_function=self.embedding_manager.embeddings,
                        persist_directory=self.persist_directory
                    )
                    
                    # Verificar que funciona haciendo una operación simple
                    try:
                        # Probar que la colección responde
                        self._vector_store._collection.count()
                        logger.info(f"Vector store initialized successfully at: {self.persist_directory}")
                        break
                        
                    except Exception as e:
                        logger.warning(f"Vector store test failed: {e}")
                        raise e
                        
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        logger.info("Resetting and retrying...")
                        self._reset_vector_store()
                        self._vector_store = None
                    else:
                        logger.error("All initialization attempts failed")
                        raise VectorStoreException(f"Failed to initialize vector store after {max_retries} attempts: {e}")
        
        return self._vector_store
    
    def add_documents(self, documents):
        """Agrega documentos a la base vectorial"""
        if not documents:
            logger.warning("No documents to add")
            return []

        tracer = get_current_tracer()
        span = tracer.start_span("embed") if tracer else None
        start = time.perf_counter()

        try:
            # Asegurar que el vector store está inicializado
            vs = self.vector_store
            
            # Verificar que la colección está lista
            if not hasattr(vs, '_collection') or vs._collection is None:
                raise VectorStoreException("Collection not properly initialized")
            
            logger.info(f"Adding {len(documents)} documents to vector store...")
            
            # Agregar documentos en lotes para evitar problemas de memoria
            batch_size = 20  # Reducido para mayor estabilidad
            all_ids = []
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                try:
                    logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
                    
                    # Limpiar contenido de documentos vacíos
                    clean_batch = []
                    for doc in batch:
                        if doc.page_content and doc.page_content.strip():
                            clean_batch.append(doc)
                    
                    if clean_batch:
                        ids = vs.add_documents(clean_batch)
                        all_ids.extend(ids)
                        logger.info(f"Successfully added batch: {len(clean_batch)} documents")
                    else:
                        logger.warning(f"Skipped empty batch {i//batch_size + 1}")
                        
                except Exception as e:
                    logger.error(f"Error adding batch {i//batch_size + 1}: {e}")
                    # Continuar con el siguiente lote en lugar de fallar completamente
                    continue
            
            if all_ids:
                logger.info(f"Successfully added {len(all_ids)} documents to vector store")
                
                # Forzar persistencia
                try:
                    if hasattr(vs, 'persist'):
                        vs.persist()
                except:
                    pass  # Algunas versiones no tienen persist()
                    
            else:
                logger.warning("No documents were successfully added")
            
            return all_ids

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise VectorStoreException(f"Failed to add documents: {e}")
        finally:
            duration = (time.perf_counter() - start) * 1000
            record_latency("embed", duration, settings.embed_sla_ms)
            if tracer and span:
                tracer.end_span(span, "success")

    def index_postgres_query(self, conn_str: str, query: str) -> int:
        """Carga datos desde PostgreSQL e indexa en la base vectorial"""
        try:
            docs = self.document_processor.load_from_postgres(conn_str, query)
            if not docs:
                logger.warning("No data retrieved from PostgreSQL")
                return 0
            chunks = self.document_processor.split_documents(docs)
            if not chunks:
                logger.warning("No chunks created from PostgreSQL data")
                return 0
            ids = self.add_documents(chunks)
            return len(ids)
        except Exception as e:
            logger.error(f"Error indexing PostgreSQL data: {e}")
            raise VectorStoreException(f"Failed to index PostgreSQL data: {e}")
    
    def load_and_index_documents(self, documents_path: Optional[str] = None) -> int:
        """Carga e indexa documentos desde un directorio"""
        tracer = get_current_tracer()
        span = tracer.start_span("ingest") if tracer else None
        start = time.perf_counter()
        try:
            logger.info("Starting document loading and indexing...")
            
            # Verificar que existen documentos
            docs_path = Path(documents_path or settings.documents_path)
            if not docs_path.exists():
                logger.error(f"Documents directory does not exist: {docs_path}")
                return 0
            
            # Obtener información de archivos
            file_info = self.document_processor.get_file_info(documents_path)
            logger.info(f"Found {file_info.get('total_files', 0)} files ({file_info.get('total_size_mb', 0):.1f} MB total)")
            
            if file_info.get('total_files', 0) == 0:
                logger.warning("No supported documents found")
                return 0
            
            # Procesar documentos
            documents = self.document_processor.process_documents(documents_path)
            if not documents:
                logger.error("No documents were processed successfully")
                return 0
            
            logger.info(f"Processed {len(documents)} document chunks")
            
            # Agregar a la base vectorial
            ids = self.add_documents(documents)
            
            if ids:
                logger.info("Document indexing completed successfully")
                return len(documents)
            else:
                logger.error("Failed to add any documents to vector store")
                return 0
            
        except Exception as e:
            logger.error(f"Error loading and indexing documents: {e}")
            raise VectorStoreException(f"Failed to load and index documents: {e}")
        finally:
            duration = (time.perf_counter() - start) * 1000
            record_latency("ingest", duration, settings.ingest_sla_ms)
            if tracer and span:
                tracer.end_span(span, "success")
    
    @trace_retrieval
    def similarity_search(self, query: str, k: int = 5):
        """Búsqueda por similitud"""
        try:
            vs = self.vector_store

            # Verificar que hay documentos en la colección
            try:
                count = vs._collection.count()
                if count == 0:
                    logger.warning("No documents in collection for similarity search")
                    return []
            except Exception:
                pass

            results = vs.similarity_search(query, k=k)
            logger.debug(f"Found {len(results)} similar documents for query")
            return results

        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            raise VectorStoreException(f"Similarity search failed: {e}")
    
    def get_retriever(self, search_kwargs: Optional[dict] = None):
        """Obtiene un retriever configurado"""
        search_kwargs = search_kwargs or {"k": settings.max_documents}
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)
    
    def delete_collection(self):
        """Elimina la colección vectorial"""
        try:
            logger.info("Deleting vector collection...")
            self._reset_vector_store()
            logger.info("Vector collection deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise VectorStoreException(f"Failed to delete collection: {e}")
    
    def get_collection_info(self) -> dict:
        """Obtiene información sobre la colección"""
        try:
            vs = self.vector_store
            count = vs._collection.count() if hasattr(vs, '_collection') and vs._collection else 0
            return {
                'document_count': count,
                'persist_directory': self.persist_directory,
                'collection_name': self._collection_name,
                'status': 'ready'
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                'document_count': 0,
                'persist_directory': self.persist_directory,
                'collection_name': self._collection_name,
                'status': f'error: {str(e)}'
            }