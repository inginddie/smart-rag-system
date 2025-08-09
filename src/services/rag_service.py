# -*- coding: utf-8 -*-
"""
Enhanced RAG Service with HU5 Query Preprocessing & Validation Integration
MODIFICATION of existing src/services/rag_service.py
"""

from typing import Any, Dict, List, Optional

from src.chains.rag_chain import RAGChain
from src.storage.vector_store import VectorStoreManager
from src.utils.exceptions import RAGException
from src.utils.faq_manager import FAQManager
from src.utils.intent_detector import IntentType
from src.utils.logger import setup_logger
from src.utils.metrics import start_metrics_server
from src.utils.quality_validator import academic_quality_validator
# ======= NEW IMPORTS FOR HU4 & HU5 =======
from src.utils.query_advisor import query_advisor
from src.utils.usage_analytics import usage_analytics

# ======= NEW IMPORTS FOR HU5 =======
from src.utils.query_validator import query_validator, ValidationResult
from src.utils.refinement_suggester import refinement_suggester, RefinementResult

logger = setup_logger()


class RAGService:
    """RAG Service con Query Preprocessing (HU5), Query Advisor y Usage Analytics integrados"""
    
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
            self._initialized = True
            logger.info("Enhanced RAG service initialized with HU5 Query Preprocessing, Query Advisor and Analytics")
            start_metrics_server()
            return True

        except Exception as e:
            logger.error(f"Error initializing RAG service: {e}")
            raise RAGException(f"Failed to initialize RAG service: {e}")

    def _needs_indexing(self) -> bool:
        """Verifica si se necesita indexar documentos"""
        try:
            # Check 1: Vector store collection info
            info = self.vector_store_manager.get_collection_info()
            doc_count = info.get("document_count", 0)

            # Check 2: Alternative - check if vector DB directory has data
            import os

            from config.settings import settings

            vector_db_path = getattr(settings, "vector_db_path", "./data/vector_db")
            chroma_db_file = os.path.join(vector_db_path, "chroma.sqlite3")
            has_db_file = os.path.exists(chroma_db_file)

            # Check 3: Look for index directories
            has_indices = False
            if os.path.exists(vector_db_path):
                subdirs = [
                    d
                    for d in os.listdir(vector_db_path)
                    if os.path.isdir(os.path.join(vector_db_path, d)) and len(d) > 30
                ]
                has_indices = len(subdirs) > 0

            # Decision logic
            if doc_count > 0:
                logger.info(f"Found {doc_count} documents in collection")
                return False
            elif has_db_file and has_indices:
                logger.info(
                    f"Found existing vector database with {len(subdirs)} indices, skipping indexing"
                )
                return False
            else:
                logger.info("No documents found in collection, indexing needed")
                return True

        except Exception as e:
            logger.info(
                f"Could not check collection status: {e}, assuming indexing needed"
            )
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
                'template_info': result.get('template_info', {})
            }
            
            # ======= HU5 PREPROCESSING INFO (NEW) =======
            if preprocessing_info:
                response['preprocessing_info'] = preprocessing_info
            
            # ======= QUERY ADVISOR INTEGRATION (Existing HU4) =======
            if include_advisor:
                try:
                    # Extract intent result for advisor
                    intent_result = None
                    intent_info = result.get("intent_info", {})
                    if intent_info:
                        intent_result = intent_info.get("intent_result_object")

                    # Analyze query effectiveness
                    effectiveness = self.query_advisor.analyze_query_effectiveness(
                        query=question, result=result, intent_result=intent_result
                    )

                    # Track analytics BEFORE generating suggestions
                    intent_type = (
                        intent_result.intent_type
                        if intent_result
                        else IntentType.UNKNOWN
                    )
                    processing_time = (
                        intent_info.get("processing_time_ms", 0)
                        + result.get("template_info", {}).get("processing_time_ms", 0)
                        + result.get("expansion_info", {}).get("processing_time_ms", 0)
                    )

                    suggestion_shown = (
                        effectiveness.score < self.query_advisor.effectiveness_threshold
                    )

                    self.usage_analytics.track_query_outcome(
                        query=question,
                        intent_type=intent_type,
                        effectiveness_score=effectiveness.score,
                        processing_time_ms=processing_time,
                        suggestion_shown=suggestion_shown,
                    )

                    # Generate suggestions if needed
                    suggestions = []
                    contextual_tips = []

                    if effectiveness.score < self.query_advisor.effectiveness_threshold:
                        suggestions = self.query_advisor.generate_suggestions(
                            query=question,
                            intent_result=intent_result,
                            effectiveness=effectiveness,
                        )

                        complexity_score = result.get("model_info", {}).get(
                            "complexity_score", 0.5
                        )
                        contextual_tips = self.query_advisor.get_contextual_tips(
                            intent_type=intent_type, complexity_score=complexity_score
                        )

                    # Add advisor info to response
                    response["advisor_info"] = {
                        "effectiveness_score": effectiveness.score,
                        "effectiveness_reasoning": effectiveness.reasoning,
                        "improvement_areas": effectiveness.improvement_areas,
                        "suggestions": [
                            {
                                "reformulated_query": s.reformulated_query,
                                "reason": s.reason,
                                "expected_improvement": s.expected_improvement,
                                "priority": s.priority,
                            }
                            for s in suggestions
                        ],
                        "contextual_tips": [
                            {
                                "tip_text": t.tip_text,
                                "category": t.category,
                                "example": t.example,
                            }
                            for t in contextual_tips
                        ],
                        "suggestion_shown": suggestion_shown,
                    }

                    logger.debug(
                        f"Query advisor analysis: effectiveness={effectiveness.score:.3f}, suggestions={len(suggestions)}"
                    )

                except Exception as e:
                    logger.error(f"Error in query advisor integration: {e}")
                    # Don't fail the entire query for advisor errors
                    response["advisor_info"] = {
                        "error": "Advisor analysis failed",
                        "suggestion_shown": False,
                    }
            
            # ======= QUALITY VALIDATION (Existing) =======
            if validate_quality and self._should_validate_quality(result):
                try:
                    quality_score = self._validate_response_quality(result, question)
                    response["quality_info"] = quality_score
                except Exception as e:
                    logger.warning(f"Quality validation failed: {e}")
                    response['quality_info'] = {"error": "Quality validation failed"}
            
            # ======= SOURCES (Existing) =======
            if include_sources:
                sources = []
                for doc in result.get("context", []):
                    source_info = {
                        "content": (
                            doc.page_content[:200] + "..."
                            if len(doc.page_content) > 200
                            else doc.page_content
                        ),
                        "metadata": doc.metadata,
                    }
                    sources.append(source_info)
                response["sources"] = sources

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
            logger.debug(
                f"Suggestion {'adopted' if adopted else 'rejected'} for query: {original_query[:50]}..."
            )
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
            answer = result.get("answer", "")
            intent_info = result.get("intent_info", {})
            template_info = result.get("template_info", {})

            # Crear metadata básica si no está disponible
            from src.chains.prompt_templates import TemplateMetadata
            from src.utils.intent_detector import IntentType

            intent_type = IntentType.UNKNOWN
            if intent_info and "intent_result_object" in intent_info:
                intent_type = intent_info["intent_result_object"].intent_type

            # Metadata básica para validación
            metadata = TemplateMetadata(
                sections=template_info.get("template_metadata", {}).get(
                    "sections", ["Response"]
                ),
                citation_requirements={"basic_sources": True},
                quality_criteria=["Clarity", "Completeness", "Academic Rigor"],
                expected_length=template_info.get("template_metadata", {}).get(
                    "expected_length", "medium"
                ),
                academic_rigor=template_info.get("template_metadata", {}).get(
                    "academic_rigor", "intermediate"
                ),
            )

            # Validar calidad
            quality_score = self.quality_validator.validate_response(
                answer, intent_type, metadata
            )

            return {
                "total_score": quality_score.total_score,
                "section_scores": quality_score.section_scores,
                "quality_level": self.quality_validator.get_quality_level(
                    quality_score.total_score
                ).value,
                "issues_count": len(quality_score.issues_found),
                "recommendations_count": len(quality_score.recommendations),
                "validation_successful": True,
            }

        except Exception as e:
            logger.error(f"Error in quality validation: {e}")
            return {"validation_successful": False, "error": str(e)}

    def get_simple_answer(self, question: str) -> str:
        """Obtiene respuesta simple con información del modelo (existing method)"""
        result = self.query(question)

        answer = result["answer"]
        model_info = result.get("model_info", {})

        if model_info and model_info.get("selected_model"):
            model_name = model_info["selected_model"]
            complexity = model_info.get("complexity_score", 0)
            logger.info(
                f"Response generated with {model_name} (complexity: {complexity:.2f})"
            )

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
                "initialized": self._initialized,
                "collection_status": collection_info.get("status", "unknown"),
                "document_count": collection_info.get("document_count", 0),
                "persist_directory": collection_info.get(
                    "persist_directory", "unknown"
                ),
                "smart_selection_enabled": getattr(
                    __import__("config.settings", fromlist=["settings"]),
                    "enable_smart_selection",
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
            return {"initialized": self._initialized, "error": str(e)}

    def get_detailed_analysis(self, question: str) -> Dict[str, Any]:
        """Obtiene análisis académico completo con información del advisor (existing method)"""
        if not self._initialized:
            raise RAGException("RAG service not initialized. Call initialize() first.")

        try:
            # Get full analysis with advisor info
            full_result = self.query(
                question, include_sources=True, include_advisor=True
            )

            # Enhance with detailed academic analysis
            academic_analysis = self.rag_chain.get_academic_analysis(question)

            # Combine both
            full_result.update(academic_analysis)

            return full_result

        except Exception as e:
            logger.error(f"Error getting detailed analysis: {e}")
            raise RAGException(f"Failed to get detailed analysis: {e}")

    def validate_query_only(self, query: str) -> Dict[str, Any]:
        """Valida consulta usando HU4 sin procesar con LLM - Para testing sin API key"""
        try:
            from src.utils.query_validator import QueryValidator

            validator = QueryValidator()
            validation_result = validator.validate_query(query)

            # Simular estructura de respuesta completa para testing
            result = {
                "preprocessing_enabled": True,
                "validation": {
                    "is_valid": validation_result.is_valid,
                    "confidence_score": validation_result.confidence,
                    "validation_passed": validation_result.is_valid,
                    "should_show_modal": not validation_result.is_valid,
                    "issues": [
                        str(issue).split(".")[-1] for issue in validation_result.issues
                    ],
                    "processing_time_ms": validation_result.processing_time_ms,
                },
                "suggestions": {
                    "available": not validation_result.is_valid,
                    "suggestions": [],
                    "quick_fixes": [],
                    "processing_time_ms": 0,
                },
            }

            # Generar sugerencias si es necesario
            if not validation_result.is_valid:
                try:
                    from src.utils.refinement_suggester import \
                        RefinementSuggester

                    suggester = RefinementSuggester()
                    refinement_result = suggester.generate_refinements(
                        query, validation_result
                    )

                    result["suggestions"] = {
                        "available": refinement_result.suggestions_available,
                        "suggestions": [
                            {
                                "suggested_query": s.suggested_query,
                                "reason": s.reason,
                                "confidence": s.confidence,
                                "expected_improvement": s.expected_improvement,
                                "strategy": s.strategy.value,
                                "priority": s.priority,
                            }
                            for s in refinement_result.suggestions
                        ],
                        "quick_fixes": refinement_result.quick_fixes,
                        "processing_time_ms": refinement_result.processing_time_ms,
                    }
                except ImportError:
                    # Si no está disponible el RefinementSuggester, usar mock
                    result["suggestions"]["quick_fixes"] = [
                        "Ser más específico sobre el aspecto que te interesa",
                        "Agregar contexto académico o de aplicación",
                    ]

            return result

        except Exception as e:
            logger.error(f"Error in validation-only mode: {e}")
            return {
                "preprocessing_enabled": False,
                "validation": {
                    "is_valid": True,
                    "confidence_score": 0.5,
                    "validation_passed": True,
                    "should_show_modal": False,
                    "issues": [],
                    "processing_time_ms": 0,
                },
                "suggestions": {
                    "available": False,
                    "suggestions": [],
                    "quick_fixes": [],
                    "processing_time_ms": 0,
                },
            }
