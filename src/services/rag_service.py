# -*- coding: utf-8 -*-
"""
Enhanced RAG Service with HU5 Query Preprocessing & Validation Integration
MODIFICATION of existing src/services/rag_service.py
"""

from typing import List, Dict, Any, Optional, Tuple
from src.chains.rag_chain import RAGChain
from src.storage.vector_store import VectorStoreManager
from src.utils.logger import setup_logger
from src.utils.exceptions import RAGException
from src.utils.faq_manager import FAQManager
from src.utils.metrics import start_metrics_server
from src.utils.quality_validator import academic_quality_validator
from config.settings import settings

# Existing Query Advisor and Analytics (HU4)
from src.utils.query_advisor import query_advisor
from src.utils.usage_analytics import usage_analytics
from src.utils.intent_detector import IntentType

# ======= NEW IMPORTS FOR HU5 =======
from src.utils.query_validator import query_validator, ValidationResult
from src.utils.refinement_suggester import refinement_suggester, RefinementResult

# ======= AGENT SYSTEM IMPORTS =======
from src.agents.base.registry import AgentRegistry
from src.agents.specialized.document_search import create_document_search_agent
from src.agents.base.fallback import AgentFallbackManager

# ======= ADMIN SYSTEM IMPORTS =======
from src.admin.keyword_manager import KeywordManager

# ======= MEMORY SYSTEM IMPORTS =======
from src.memory.manager import MemoryManager

logger = setup_logger()

class RAGService:
    """RAG Service con Query Preprocessing (HU5), Query Advisor, Analytics y Sistema de Agentes"""
    
    def __init__(self):
        self.vector_store_manager = VectorStoreManager()
        self.rag_chain = RAGChain()
        self.faq_manager = FAQManager()
        self.quality_validator = academic_quality_validator
        
        # HU4 Components
        self.query_advisor = query_advisor
        self.usage_analytics = usage_analytics
        
        # ======= NEW HU5 COMPONENTS =======
        self.query_validator = query_validator
        self.refinement_suggester = refinement_suggester
        
        # ======= AGENT SYSTEM =======
        self.agent_registry = AgentRegistry()
        self.fallback_manager = None  # Se inicializa después
        self.use_agents = True  # Flag para habilitar/deshabilitar agentes
        
        # ======= ADMIN SYSTEM =======
        self.keyword_manager = KeywordManager()  # Gestor de keywords
        
        # ======= MEMORY SYSTEM =======
        self.memory_manager = MemoryManager(
            max_conversation_length=50,
            max_semantic_memories=100,
            conversation_ttl_days=30
        )
        
        self._initialized = False
    
    def initialize(self, force_reindex: bool = False) -> bool:
        """Inicializa el servicio RAG"""
        try:
            logger.info("Starting enhanced RAG service initialization with HU5 preprocessing...")
            
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
            
            # ======= INITIALIZE AGENT SYSTEM =======
            self._setup_agents()
            
            self._initialized = True
            logger.info("Enhanced RAG service initialized with HU5 Query Preprocessing, Query Advisor, Analytics and Agent System")
            start_metrics_server()
            return True
            
        except Exception as e:
            logger.error(f"Error initializing RAG service: {e}")
            raise RAGException(f"Failed to initialize RAG service: {e}")
    
    def _setup_agents(self):
        """Configura el sistema de agentes especializados"""
        try:
            logger.info("Setting up agent system...")
            
            # Crear DocumentSearchAgent
            doc_agent = create_document_search_agent(
                vector_store_manager=self.vector_store_manager,
                rag_chain=self.rag_chain
            )
            
            # Asignar memory manager al agente
            doc_agent.memory_manager = self.memory_manager
            
            # Registrar agente
            self.agent_registry.register_agent(doc_agent)
            
            # Registrar ComparisonAgent (HU3)
            from src.agents.specialized.comparison import create_comparison_agent
            comparison_agent = create_comparison_agent(self.vector_store_manager)
            comparison_agent.memory_manager = self.memory_manager
            self.agent_registry.register_agent(comparison_agent)
            
            # Inicializar fallback manager
            self.fallback_manager = AgentFallbackManager(rag_service=self)
            
            # Inicializar orquestador (HU5)
            from src.agents.orchestration.orchestrator import AgentOrchestrator
            self.orchestrator = AgentOrchestrator(
                agent_registry=self.agent_registry,
                confidence_threshold=0.7,
                enable_multi_agent=False  # Por ahora deshabilitado
            )
            
            logger.info(f"Agent system ready: {len(self.agent_registry.get_all_agents())} agent(s) registered")
            logger.info("Memory system integrated with all agents")
            logger.info("Agent orchestrator initialized (HU5)")
            
        except Exception as e:
            logger.warning(f"Could not setup agents: {e}. Continuing without agent system.")
            self.use_agents = False
    
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
              validate_quality: bool = True, include_advisor: bool = True,
              enable_preprocessing: bool = True) -> Dict[str, Any]:
        """
        Procesa consulta con HU5 Query Preprocessing + Query Advisor y Analytics
        
        ENHANCED METHOD - now includes HU5 preprocessing BEFORE main pipeline
        
        Args:
            question: User query
            include_sources: Include source documents in response
            validate_quality: Validate response quality
            include_advisor: Include Query Advisor analysis
            enable_preprocessing: Enable HU5 query preprocessing (NEW)
        """
        if not self._initialized:
            raise RAGException("RAG service not initialized. Call initialize() first.")
        
        try:
            # ======= HU5 QUERY PREPROCESSING (NEW) =======
            preprocessing_info = None
            final_query = question  # Default: use original query
            
            if enable_preprocessing and settings.enable_query_preprocessing:
                logger.debug(f"HU5: Starting query preprocessing for: {question[:50]}...")
                
                try:
                    # Step 1: Validate the query
                    validation_result = self.query_validator.validate_query(question)
                    
                    # Step 2: Generate refinement suggestions if needed
                    refinement_result = None
                    if not validation_result.validation_passed:
                        refinement_result = self.refinement_suggester.generate_refinements(
                            question, validation_result
                        )
                    
                    # Step 3: Prepare preprocessing info for response
                    preprocessing_info = {
                        'preprocessing_enabled': True,
                        'validation_result': {
                            'is_valid': validation_result.is_valid,
                            'confidence_score': validation_result.confidence_score,
                            'issues_count': len(validation_result.issues),
                            'should_show_modal': validation_result.should_show_modal,
                            'validation_passed': validation_result.validation_passed,
                            'processing_time_ms': validation_result.processing_time_ms,
                            'issues': validation_result.issues  # Detailed issues for UI
                        },
                        'refinement_suggestions': None,
                        'preprocessing_time_ms': validation_result.processing_time_ms
                    }
                    
                    # Add refinement suggestions if available
                    if refinement_result and refinement_result.suggestions_available:
                        preprocessing_info['refinement_suggestions'] = {
                            'available': True,
                            'suggestions_count': len(refinement_result.suggestions),
                            'suggestions': [
                                {
                                    'suggested_query': s.suggested_query,
                                    'reason': s.reason,
                                    'confidence': s.confidence,
                                    'expected_improvement': s.expected_improvement,
                                    'strategy': s.strategy.value,
                                    'priority': s.priority
                                } for s in refinement_result.suggestions
                            ],
                            'quick_fixes': refinement_result.quick_fixes,
                            'processing_time_ms': refinement_result.processing_time_ms
                        }
                    else:
                        preprocessing_info['refinement_suggestions'] = {'available': False}
                    
                    # Step 4: Determine if we should proceed with original query or suggest alternatives
                    # For HU5 implementation, we continue with original query but provide suggestions
                    # In production, this could be enhanced to wait for user choice
                    
                    logger.info(f"HU5: Query preprocessing completed - confidence: {validation_result.confidence_score:.3f}, suggestions: {refinement_result.suggestions_available if refinement_result else False}")
                    
                except Exception as e:
                    logger.error(f"HU5: Error in query preprocessing: {e}")
                    # Graceful fallback - continue with original query
                    preprocessing_info = {
                        'preprocessing_enabled': True,
                        'error': f'Preprocessing failed: {str(e)}',
                        'fallback_used': True
                    }
            
            # ======= AGENT ORCHESTRATION (HU5) =======
            agent_used = None
            if self.use_agents and hasattr(self, 'orchestrator') and self.orchestrator:
                try:
                    # Use orchestrator for intelligent agent selection
                    import asyncio
                    
                    # Define fallback handler
                    def fallback_handler(query):
                        return self.rag_chain.invoke(query)
                    
                    # Orchestrate agent execution
                    orchestration_result = asyncio.run(
                        self.orchestrator.orchestrate(
                            query=final_query,
                            context={'include_sources': include_sources},
                            fallback_handler=fallback_handler
                        )
                    )
                    
                    # Extract result
                    result = {
                        'answer': orchestration_result.get('answer', ''),
                        'model_info': {
                            'selected_model': 'agent' if not orchestration_result.get('metadata', {}).get('fallback') else 'classic',
                            'agent_name': orchestration_result.get('agent_name', 'unknown'),
                            'agent_confidence': orchestration_result.get('confidence', 0.0)
                        },
                        'intent_info': {},
                        'template_info': {'agent_used': not orchestration_result.get('metadata', {}).get('fallback', False)},
                        'orchestration_info': orchestration_result.get('orchestration', {})
                    }
                    agent_used = orchestration_result.get('agent_name')
                    logger.info(f"Orchestration completed: agent={agent_used}")
                    
                except Exception as e:
                    logger.warning(f"Orchestration failed: {e}, falling back to classic RAG")
                    import traceback
                    traceback.print_exc()
                    result = self.rag_chain.invoke(final_query)
            else:
                # ======= CORE RAG PROCESSING (Existing Pipeline) =======
                result = self.rag_chain.invoke(final_query)
            
            # Registrar pregunta para FAQs
            self.faq_manager.log_question(question)
            
            # Preparar respuesta base
            response = {
                'answer': result.get('answer', 'No se pudo generar una respuesta.'),
                'question': question,
                'final_query_used': final_query,
                'model_info': result.get('model_info', {}),
                'intent_info': result.get('intent_info', {}),
                'template_info': result.get('template_info', {}),
                'agent_info': {'agent_used': agent_used} if agent_used else None
            }
            
            # ======= HU5 PREPROCESSING INFO (NEW) =======
            if preprocessing_info:
                response['preprocessing_info'] = preprocessing_info
            
            # ======= QUERY ADVISOR INTEGRATION (Existing HU4) =======
            if include_advisor:
                try:
                    # Extract intent result for advisor
                    intent_result = None
                    intent_info = result.get('intent_info', {})
                    if intent_info:
                        intent_result = intent_info.get('intent_result_object')
                    
                    # Analyze query effectiveness
                    effectiveness = self.query_advisor.analyze_query_effectiveness(
                        query=question,
                        result=result,
                        intent_result=intent_result
                    )
                    
                    # Track analytics BEFORE generating suggestions
                    intent_type = intent_result.intent_type if intent_result else IntentType.UNKNOWN
                    processing_time = (
                        intent_info.get('processing_time_ms', 0) +
                        result.get('template_info', {}).get('processing_time_ms', 0) +
                        result.get('expansion_info', {}).get('processing_time_ms', 0)
                    )
                    
                    suggestion_shown = effectiveness.score < self.query_advisor.effectiveness_threshold
                    
                    self.usage_analytics.track_query_outcome(
                        query=question,
                        intent_type=intent_type,
                        effectiveness_score=effectiveness.score,
                        processing_time_ms=processing_time,
                        suggestion_shown=suggestion_shown
                    )
                    
                    # Generate suggestions if needed
                    suggestions = []
                    contextual_tips = []
                    
                    if effectiveness.score < self.query_advisor.effectiveness_threshold:
                        suggestions = self.query_advisor.generate_suggestions(
                            query=question,
                            intent_result=intent_result,
                            effectiveness=effectiveness
                        )
                        
                        complexity_score = result.get('model_info', {}).get('complexity_score', 0.5)
                        contextual_tips = self.query_advisor.get_contextual_tips(
                            intent_type=intent_type,
                            complexity_score=complexity_score
                        )
                    
                    # Add advisor info to response
                    response['advisor_info'] = {
                        'effectiveness_score': effectiveness.score,
                        'effectiveness_reasoning': effectiveness.reasoning,
                        'improvement_areas': effectiveness.improvement_areas,
                        'suggestions': [
                            {
                                'reformulated_query': s.reformulated_query,
                                'reason': s.reason,
                                'expected_improvement': s.expected_improvement,
                                'priority': s.priority
                            } for s in suggestions
                        ],
                        'contextual_tips': [
                            {
                                'tip_text': t.tip_text,
                                'category': t.category,
                                'example': t.example
                            } for t in contextual_tips
                        ],
                        'suggestion_shown': suggestion_shown
                    }
                    
                    logger.debug(f"Query advisor analysis: effectiveness={effectiveness.score:.3f}, suggestions={len(suggestions)}")
                    
                except Exception as e:
                    logger.error(f"Error in query advisor integration: {e}")
                    # Don't fail the entire query for advisor errors
                    response['advisor_info'] = {
                        'error': 'Advisor analysis failed',
                        'suggestion_shown': False
                    }
            
            # ======= QUALITY VALIDATION (Existing) =======
            if validate_quality and self._should_validate_quality(result):
                try:
                    quality_score = self._validate_response_quality(result, question)
                    response['quality_info'] = quality_score
                except Exception as e:
                    logger.warning(f"Quality validation failed: {e}")
                    response['quality_info'] = {"error": "Quality validation failed"}
            
            # ======= SOURCES (Existing) =======
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
    
    def validate_query_only(self, question: str) -> Dict[str, Any]:
        """
        NEW METHOD - Only validate query without processing (for UI modal use)
        
        Args:
            question: User query to validate
            
        Returns:
            Dict with validation result and suggestions
        """
        try:
            if not settings.enable_query_preprocessing:
                return {
                    'preprocessing_enabled': False,
                    'message': 'Query preprocessing is disabled'
                }
            
            # Validate the query
            validation_result = self.query_validator.validate_query(question)
            
            # Generate suggestions if validation failed
            refinement_result = None
            if not validation_result.validation_passed:
                refinement_result = self.refinement_suggester.generate_refinements(
                    question, validation_result
                )
            
            return {
                'preprocessing_enabled': True,
                'validation': {
                    'is_valid': validation_result.is_valid,
                    'confidence_score': validation_result.confidence_score,
                    'validation_passed': validation_result.validation_passed,
                    'should_show_modal': validation_result.should_show_modal,
                    'issues': validation_result.issues,
                    'processing_time_ms': validation_result.processing_time_ms
                },
                'suggestions': {
                    'available': refinement_result.suggestions_available if refinement_result else False,
                    'suggestions': [
                        {
                            'suggested_query': s.suggested_query,
                            'reason': s.reason,
                            'confidence': s.confidence,
                            'expected_improvement': s.expected_improvement,
                            'strategy': s.strategy.value,
                            'priority': s.priority
                        } for s in (refinement_result.suggestions if refinement_result else [])
                    ],
                    'quick_fixes': refinement_result.quick_fixes if refinement_result else [],
                    'processing_time_ms': refinement_result.processing_time_ms if refinement_result else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error in query validation: {e}")
            return {
                'preprocessing_enabled': True,
                'error': str(e),
                'validation': {'is_valid': True, 'confidence_score': 0.5}  # Fail-open
            }
    
    def apply_refinement_suggestion(self, original_query: str, suggested_query: str, 
                                   include_sources: bool = False, validate_quality: bool = True,
                                   include_advisor: bool = True) -> Dict[str, Any]:
        """
        NEW METHOD - Apply a refinement suggestion and process the improved query
        
        Args:
            original_query: Original user query
            suggested_query: Improved query from refinement suggester
            Other params: Same as main query method
        """
        try:
            # Track that a suggestion was applied
            self.usage_analytics.track_suggestion_adoption(original_query, adopted=True)
            
            # Process the refined query with preprocessing disabled (already validated)
            result = self.query(
                question=suggested_query,
                include_sources=include_sources,
                validate_quality=validate_quality,
                include_advisor=include_advisor,
                enable_preprocessing=False  # Skip preprocessing for refined queries
            )
            
            # Add refinement metadata
            result['refinement_applied'] = {
                'original_query': original_query,
                'suggested_query': suggested_query,
                'suggestion_adopted': True
            }
            
            logger.info(f"HU5: Applied refinement suggestion - original: '{original_query[:50]}...', refined: '{suggested_query[:50]}...'")
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying refinement suggestion: {e}")
            raise RAGException(f"Failed to apply refinement: {e}")
    
    def track_suggestion_adoption(self, original_query: str, adopted: bool = True) -> None:
        """Track when user adopts/rejects a suggestion (existing HU4 method)"""
        try:
            self.usage_analytics.track_suggestion_adoption(original_query, adopted)
            logger.debug(f"Suggestion {'adopted' if adopted else 'rejected'} for query: {original_query[:50]}...")
        except Exception as e:
            logger.error(f"Error tracking suggestion adoption: {e}")
    
    def track_refinement_suggestion_adoption(self, original_query: str, suggested_query: str, adopted: bool = True) -> None:
        """
        NEW METHOD - Track HU5 refinement suggestion adoption
        """
        try:
            # Track in analytics with additional refinement metadata
            self.usage_analytics.track_suggestion_adoption(original_query, adopted)
            
            # Could be extended to track specific refinement strategies if needed
            logger.debug(f"HU5: Refinement suggestion {'adopted' if adopted else 'rejected'} - original: '{original_query[:30]}...', suggested: '{suggested_query[:30]}...'")
            
        except Exception as e:
            logger.error(f"Error tracking refinement suggestion adoption: {e}")
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary for admin dashboard (existing HU4 method)"""
        try:
            return self.usage_analytics.get_analytics_summary()
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_improvement_recommendations(self) -> List[Dict]:
        """Get improvement recommendations based on analytics (existing HU4 method)"""
        try:
            return self.usage_analytics.get_improvement_recommendations()
        except Exception as e:
            logger.error(f"Error getting improvement recommendations: {e}")
            return []
    
    def get_preprocessing_stats(self) -> Dict[str, Any]:
        """
        NEW METHOD - Get HU5 preprocessing performance statistics
        """
        try:
            validation_stats = self.query_validator.get_validation_stats()
            suggestion_stats = self.refinement_suggester.get_suggestion_stats()
            
            return {
                'preprocessing_enabled': settings.enable_query_preprocessing,
                'validation_stats': validation_stats,
                'suggestion_stats': suggestion_stats,
                'configuration': settings.get_preprocessing_config()
            }
            
        except Exception as e:
            logger.error(f"Error getting preprocessing stats: {e}")
            return {"status": "error", "message": str(e)}
    
    def _should_validate_quality(self, result: Dict[str, Any]) -> bool:
        """Determina si se debe validar calidad de la respuesta (existing method)"""
        # Validar solo si se usó template especializado
        template_info = result.get('template_info', {})
        return template_info.get('template_used', False)
    
    def _validate_response_quality(self, result: Dict[str, Any], question: str) -> Dict[str, Any]:
        """Valida calidad de la respuesta usando template metadata (existing method)"""
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
        """Obtiene respuesta simple con información del modelo (existing method)"""
        result = self.query(question)
        
        answer = result['answer']
        model_info = result.get('model_info', {})
        
        if model_info and model_info.get('selected_model'):
            model_name = model_info['selected_model']
            complexity = model_info.get('complexity_score', 0)
            logger.info(f"Response generated with {model_name} (complexity: {complexity:.2f})")
        
        return answer

    def get_frequent_questions(self, top_n: int = 5) -> List[str]:
        """Devuelve las preguntas más frecuentes registradas (existing method)"""
        return self.faq_manager.get_top_questions(top_n)
    
    def reindex_documents(self) -> int:
        """Reindexar documentos (existing method)"""
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
        """Obtiene el estado del servicio con información HU5 + advisor (enhanced method)"""
        try:
            collection_info = self.vector_store_manager.get_collection_info()
            analytics_summary = self.get_analytics_summary()
            preprocessing_stats = self.get_preprocessing_stats()
            
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
                'quality_validation': True,
                
                # HU4 Status Info
                'query_advisor_enabled': True,
                'usage_analytics_enabled': True,
                'total_queries_processed': analytics_summary.get('total_queries', 0),
                'avg_effectiveness': analytics_summary.get('avg_effectiveness', 0),
                'suggestion_adoption_rate': analytics_summary.get('suggestion_adoption_rate', 0),
                
                # ======= NEW HU5 STATUS INFO =======
                'query_preprocessing_enabled': settings.enable_query_preprocessing,
                'validation_before_processing': settings.validation_before_processing,
                'preprocessing_stats': preprocessing_stats,
                'preprocessing_sla_compliance': True  # Could be calculated from stats
            }
        except Exception as e:
            return {
                'initialized': self._initialized,
                'error': str(e)
            }
    
    def get_detailed_analysis(self, question: str) -> Dict[str, Any]:
        """Obtiene análisis académico completo con información del advisor (existing method)"""
        if not self._initialized:
            raise RAGException("RAG service not initialized. Call initialize() first.")
        
        try:
            # Get full analysis with advisor info
            full_result = self.query(question, include_sources=True, include_advisor=True)
            
            # Enhance with detailed academic analysis
            academic_analysis = self.rag_chain.get_academic_analysis(question)
            
            # Combine both
            full_result.update(academic_analysis)
            
            return full_result
            
        except Exception as e:
            logger.error(f"Error getting detailed analysis: {e}")
            raise RAGException(f"Failed to get detailed analysis: {e}")

    # ======= AGENT SYSTEM METHODS =======
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de agentes"""
        if not self.use_agents or not self.agent_registry:
            return {'agents_enabled': False}
        
        try:
            all_agents = self.agent_registry.get_all_agents()
            health = self.agent_registry.health_check()
            
            total_queries = sum(agent.stats.total_queries for agent in all_agents)
            
            return {
                'agents_enabled': True,
                'total_agents': len(all_agents),
                'active_agents': len([a for a in all_agents if a.stats.total_queries > 0]),
                'total_queries': total_queries,
                'agents_health': health,
                'capability_coverage': self.agent_registry.get_capability_coverage()
            }
        except Exception as e:
            logger.error(f"Error getting agent stats: {e}")
            import traceback
            traceback.print_exc()
            return {'agents_enabled': True, 'error': str(e)}
    
    def toggle_agents(self, enabled: bool):
        """Habilita o deshabilita el sistema de agentes"""
        self.use_agents = enabled
        logger.info(f"Agent system {'enabled' if enabled else 'disabled'}")
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Obtiene lista de agentes disponibles"""
        if not self.agent_registry:
            return []
        
        agents = self.agent_registry.get_all_agents()
        return [
            {
                'name': agent.name,
                'agent_id': agent.agent_id,
                'capabilities': [cap.value for cap in agent.get_capabilities()],
                'stats': {
                    'total_queries': agent.stats.total_queries,
                    'success_rate': agent.stats.success_rate,
                    'avg_confidence': agent.stats.avg_confidence
                }
            }
            for agent in agents
        ]

    # ======= KEYWORD MANAGEMENT METHODS (HU2) =======
    
    def get_keyword_manager(self) -> KeywordManager:
        """Obtiene el gestor de keywords"""
        return self.keyword_manager
    
    def test_query_activation(self, query: str) -> Dict[str, Any]:
        """Prueba qué agentes se activarían con una query"""
        return self.keyword_manager.test_query_activation(query)
    
    def add_agent_keyword(self, agent_name: str, capability: str, keyword: str) -> bool:
        """Agrega una keyword a un agente"""
        return self.keyword_manager.add_keyword(agent_name, capability, keyword)
    
    def remove_agent_keyword(self, agent_name: str, capability: str, keyword: str) -> bool:
        """Elimina una keyword de un agente"""
        return self.keyword_manager.remove_keyword(agent_name, capability, keyword)
    
    def update_agent_threshold(self, agent_name: str, threshold: float) -> bool:
        """Actualiza el threshold de activación de un agente"""
        return self.keyword_manager.update_threshold(agent_name, threshold)
    
    def get_keyword_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de keywords"""
        return self.keyword_manager.get_system_stats()
    
    def export_keyword_config(self) -> Dict[str, Any]:
        """Exporta configuración de keywords"""
        return self.keyword_manager.export_config()
    
    def import_keyword_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Importa configuración de keywords"""
        return self.keyword_manager.import_config(config)
    
    def reset_keywords_to_default(self) -> bool:
        """Resetea keywords a configuración por defecto"""
        return self.keyword_manager.reset_to_defaults()

    # ======= MEMORY MANAGEMENT METHODS (HU4) =======
    
    def add_conversation_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Agrega un mensaje a la conversación"""
        self.memory_manager.add_message(session_id, role, content, metadata)
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Obtiene el historial de conversación"""
        return self.memory_manager.get_conversation_history(session_id, limit)
    
    def get_conversation_context(self, session_id: str, max_messages: int = 5) -> str:
        """Obtiene contexto reciente de la conversación"""
        return self.memory_manager.get_recent_context(session_id, max_messages)
    
    def clear_conversation(self, session_id: str) -> bool:
        """Limpia una conversación específica"""
        return self.memory_manager.clear_session(session_id)
    
    def get_all_conversations(self) -> List[str]:
        """Obtiene lista de todas las conversaciones activas"""
        return self.memory_manager.get_all_sessions()
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Obtiene resumen de una conversación"""
        return self.memory_manager.get_session_summary(session_id)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema de memoria"""
        return self.memory_manager.get_stats()
    
    def search_agent_memories(self, query: str, agent_id: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        """Busca en las memorias de los agentes"""
        return self.memory_manager.search_memories(query, agent_id, top_k)
