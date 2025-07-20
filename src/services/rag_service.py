# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional
from src.chains.rag_chain import RAGChain
from src.storage.vector_store import VectorStoreManager
from src.utils.logger import setup_logger
from src.utils.exceptions import RAGException
from src.utils.faq_manager import FAQManager
from src.utils.metrics import start_metrics_server
from src.utils.quality_validator import academic_quality_validator

logger = setup_logger()

class RAGService:
    """Servicio RAG con templates académicos y validación de calidad"""
    
    def __init__(self):
        self.vector_store_manager = VectorStoreManager()
        self.rag_chain = RAGChain()
        self.faq_manager = FAQManager()
        self.quality_validator = academic_quality_validator
        self._initialized = False
    
    def initialize(self, force_reindex: bool = False) -> bool:
        """Inicializa el servicio RAG"""
        try:
            logger.info("Starting enhanced RAG service initialization...")
            
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
            
            self.rag_chain.create_chain()
            self._initialized = True
            logger.info("Enhanced RAG service initialized with academic templates and quality validation")
            start_metrics_server()
            return True
            
        except Exception as e:
            logger.error(f"Error initializing RAG service: {e}")
            raise RAGException(f"Failed to initialize RAG service: {e}")
    
    def _needs_indexing(self) -> bool:
        """Verifica si se necesita indexar documentos"""
        try:
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
    
    def query(self, question: str, include_sources: bool = False, 
              validate_quality: bool = True) -> Dict[str, Any]:
        """Procesa consulta con templates y validación de calidad"""
        if not self._initialized:
            raise RAGException("RAG service not initialized. Call initialize() first.")
        
        try:
            # Usar enhanced RAG chain
            result = self.rag_chain.invoke(question)
            
            # Registrar pregunta para FAQs
            self.faq_manager.log_question(question)
            
            # Preparar respuesta base
            response = {
                'answer': result.get('answer', 'No se pudo generar una respuesta.'),
                'question': question,
                'model_info': result.get('model_info', {}),
                'intent_info': result.get('intent_info', {}),
                'template_info': result.get('template_info', {})
            }
            
            # Validación de calidad si está habilitada
            if validate_quality and self._should_validate_quality(result):
                try:
                    quality_score = self._validate_response_quality(result, question)
                    response['quality_info'] = quality_score
                except Exception as e:
                    logger.warning(f"Quality validation failed: {e}")
                    response['quality_info'] = {"error": "Quality validation failed"}
            
            # Agregar fuentes si se solicita
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
    
    def _should_validate_quality(self, result: Dict[str, Any]) -> bool:
        """Determina si se debe validar calidad de la respuesta"""
        # Validar solo si se usó template especializado
        template_info = result.get('template_info', {})
        return template_info.get('template_used', False)
    
    def _validate_response_quality(self, result: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Valida calidad de la respuesta usando template metadata"""
        try:
            # Obtener información necesaria
            answer = result.get('answer', '')
            intent_info = result.get('intent_info', {})
            template_info = result.get('template_info', {})
            
            # Crear metadata básica si no está disponible
            from src.chains.prompt_templates import TemplateMetadata
            from src.utils.intent_detector import IntentType
            
            intent_type = IntentType.UNKNOWN
            if intent_info and 'intent_result_object' in intent_info:
                intent_type = intent_info['intent_result_object'].intent_type
            
            # Metadata básica para validación
            metadata = TemplateMetadata(
                sections=template_info.get('template_metadata', {}).get('sections', ['Response']),
                citation_requirements={'basic_sources': True},
                quality_criteria=['Clarity', 'Completeness', 'Academic Rigor'],
                expected_length=template_info.get('template_metadata', {}).get('expected_length', 'medium'),
                academic_rigor=template_info.get('template_metadata', {}).get('academic_rigor', 'intermediate')
            )
            
            # Validar calidad
            quality_score = self.quality_validator.validate_response(
                answer, intent_type, metadata
            )
            
            return {
                'total_score': quality_score.total_score,
                'section_scores': quality_score.section_scores,
                'quality_level': self.quality_validator.get_quality_level(quality_score.total_score).value,
                'issues_count': len(quality_score.issues_found),
                'recommendations_count': len(quality_score.recommendations),
                'validation_successful': True
            }
            
        except Exception as e:
            logger.error(f"Error in quality validation: {e}")
            return {'validation_successful': False, 'error': str(e)}
    
    def get_simple_answer(self, question: str) -> str:
        """Obtiene respuesta simple con información del modelo"""
        result = self.query(question)
        
        answer = result['answer']
        model_info = result.get('model_info', {})
        
        if model_info and model_info.get('selected_model'):
            model_name = model_info['selected_model']
            complexity = model_info.get('complexity_score', 0)
            logger.info(f"Response generated with {model_name} (complexity: {complexity:.2f})")
        
        return answer

    def get_frequent_questions(self, top_n: int = 5) -> List[str]:
        """Devuelve las preguntas más frecuentes registradas"""
        return self.faq_manager.get_top_questions(top_n)
    
    def reindex_documents(self) -> int:
        """Reindexar documentos"""
        try:
            logger.info("Starting document reindexing...")
            logger.warning("Reindexing will reset the vector database")
            
            try:
                self.vector_store_manager.delete_collection()
            except Exception as e:
                logger.warning(f"Could not clean collection, continuing: {e}")
            
            indexed_count = self.vector_store_manager.load_and_index_documents()
            
            if indexed_count > 0:
                self.rag_chain = RAGChain()
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
                'smart_selection_enabled': getattr(
                    __import__('config.settings', fromlist=['settings']),
                    'enable_smart_selection',
                    False,
                ),
                'template_support': True,
                'quality_validation': True
            }
        except Exception as e:
            return {
                'initialized': self._initialized,
                'error': str(e)
            }
    
    def get_detailed_analysis(self, question: str) -> Dict[str, Any]:
        """Obtiene análisis académico completo con validación de calidad"""
        if not self._initialized:
            raise RAGException("RAG service not initialized. Call initialize() first.")
        
        try:
            return self.rag_chain.get_academic_analysis(question)
        except Exception as e:
            logger.error(f"Error getting detailed analysis: {e}")
            raise RAGException(f"Failed to get detailed analysis: {e}")
