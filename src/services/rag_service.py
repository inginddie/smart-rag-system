# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional
from src.chains.rag_chain import RAGChain  # ← Importación corregida
from src.storage.vector_store import VectorStoreManager
from src.utils.logger import setup_logger
from src.utils.exceptions import RAGException
from src.utils.faq_manager import FAQManager
from src.utils.metrics import start_metrics_server

logger = setup_logger()

class RAGService:
    """Servicio principal para operaciones RAG con selección inteligente de modelos"""
    
    def __init__(self):
        self.vector_store_manager = VectorStoreManager()
        self.rag_chain = RAGChain()
        self.faq_manager = FAQManager()
        self._initialized = False
    
    def initialize(self, force_reindex: bool = False) -> bool:
        """Inicializa el servicio RAG"""
        try:
            logger.info("Starting RAG service initialization...")
            
            # Verificar si hay documentos en la base vectorial
            needs_indexing = force_reindex or self._needs_indexing()
            
            if needs_indexing:
                logger.info("Indexing documents...")
                indexed_count = self.vector_store_manager.load_and_index_documents()
                if indexed_count == 0:
                    logger.warning("No documents were indexed")
                    return False
                logger.info(f"Successfully indexed {indexed_count} documents")
            else:
                logger.info("Using existing indexed documents")
            
            # Crear la cadena RAG
            self.rag_chain.create_chain()
            self._initialized = True
            logger.info("RAG service initialized successfully with smart model selection")
            start_metrics_server()
            return True
            
        except Exception as e:
            logger.error(f"Error initializing RAG service: {e}")
            raise RAGException(f"Failed to initialize RAG service: {e}")
    
    def _needs_indexing(self) -> bool:
        """Verifica si se necesita indexar documentos"""
        try:
            # Verificar si la colección tiene documentos
            info = self.vector_store_manager.get_collection_info()
            doc_count = info.get('document_count', 0)
            
            if doc_count == 0:
                logger.info("No documents found in collection, indexing needed")
                return True
            else:
                logger.info(f"Found {doc_count} documents in collection")
                return False
                
        except Exception as e:
            logger.info(f"Could not check collection status: {e}, assuming indexing needed")
            return True
    
    def query(self, question: str, include_sources: bool = False) -> Dict[str, Any]:
        """Procesa una consulta y devuelve la respuesta con información del modelo usado"""
        if not self._initialized:
            raise RAGException("RAG service not initialized. Call initialize() first.")
        
        try:
            result = self.rag_chain.invoke(question)

            # Registrar la pregunta para generar FAQs dinámicas
            self.faq_manager.log_question(question)
            
            response = {
                'answer': result.get('answer', 'No se pudo generar una respuesta.'),
                'question': question,
                'model_info': result.get('model_info', {})  # Información del modelo usado
            }
            
            if include_sources:
                sources = []
                for doc in result.get('context', []):
                    source_info = {
                        'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        'metadata': doc.metadata
                    }
                    sources.append(source_info)
                response['sources'] = sources
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise RAGException(f"Failed to process query: {e}")
    
    def get_simple_answer(self, question: str) -> str:
        """Obtiene una respuesta simple (solo texto) con información del modelo"""
        result = self.query(question)
        
        # Incluir información del modelo en la respuesta si está disponible
        answer = result['answer']
        model_info = result.get('model_info', {})
        
        if model_info and model_info.get('selected_model'):
            model_name = model_info['selected_model']
            complexity = model_info.get('complexity_score', 0)
            logger.info(f"Response generated with {model_name} (complexity: {complexity:.2f})")
        
        return answer

    def get_frequent_questions(self, top_n: int = 5) -> List[str]:
        """Devuelve las preguntas más frecuentes registradas."""
        return self.faq_manager.get_top_questions(top_n)
    
    def reindex_documents(self) -> int:
        """Reindexar documentos - SOLO usar si es necesario"""
        try:
            logger.info("Starting document reindexing...")
            logger.warning("Reindexing will reset the vector database")
            
            # Solo limpiar si realmente es necesario
            try:
                self.vector_store_manager.delete_collection()
            except Exception as e:
                logger.warning(f"Could not clean collection, continuing: {e}")
            
            # Reindexar
            indexed_count = self.vector_store_manager.load_and_index_documents()
            
            if indexed_count > 0:
                # Recrear la cadena RAG
                self.rag_chain = RAGChain()  # Crear nueva instancia
                self.rag_chain.create_chain()
                logger.info(f"Reindexed {indexed_count} documents successfully")
            else:
                logger.warning("No documents were reindexed")
            
            return indexed_count
            
        except Exception as e:
            logger.error(f"Error reindexing documents: {e}")
            raise RAGException(f"Failed to reindex documents: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del servicio"""
        try:
            collection_info = self.vector_store_manager.get_collection_info()
            return {
                'initialized': self._initialized,
                'collection_status': collection_info.get('status', 'unknown'),
                'document_count': collection_info.get('document_count', 0),
                'persist_directory': collection_info.get('persist_directory', 'unknown'),
                # Import settings lazily to avoid circular dependencies
                'smart_selection_enabled': getattr(
                    __import__('config.settings', fromlist=['settings']),
                    'enable_smart_selection',
                    False,
                )
            }
        except Exception as e:
            return {
                'initialized': self._initialized,
                'error': str(e)
            }
    
    def get_detailed_analysis(self, question: str) -> Dict[str, Any]:
        """Obtiene análisis detallado incluyendo información del modelo"""
        if not self._initialized:
            raise RAGException("RAG service not initialized. Call initialize() first.")
        
        try:
            # Usar el método get_academic_analysis del RAGChain
            return self.rag_chain.get_academic_analysis(question)
        except Exception as e:
            logger.error(f"Error getting detailed analysis: {e}")
            raise RAGException(f"Failed to get detailed analysis: {e}")
