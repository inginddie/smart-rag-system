# -*- coding: utf-8 -*-
from typing import Dict, Any, Optional
try:
    from langchain_openai import ChatOpenAI
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:  # pragma: no cover - optional dependency
    ChatOpenAI = None  # type: ignore
    create_retrieval_chain = None  # type: ignore
    create_stuff_documents_chain = None  # type: ignore
    ChatPromptTemplate = None  # type: ignore
from config.settings import settings
from src.storage.vector_store import VectorStoreManager
from src.utils.logger import setup_logger
from src.utils.exceptions import ChainException
from src.utils.tracing import trace_llm

# Importaciones para intent detection y query expansion
from src.utils.intent_detector import intent_detector, IntentType
from src.chains.prompt_templates import prompt_template_selector
from src.utils.query_expander import query_expander

# Manejo de asyncio
import asyncio

logger = setup_logger()

class RAGChain:
    """Cadena RAG con selección inteligente de modelos, detección de intención y expansión de consulta"""
    
    def __init__(self, 
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.1):
        
        self.temperature = temperature
        self.vector_store_manager = VectorStoreManager()
        
        # Model selector lazy loading para evitar dependencias circulares
        self._model_selector = None
        
        # Prompt especializado para investigación de tesis
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        # Cache de modelos y cadenas para evitar reinicialización
        self._model_cache = {}
        self._chain_cache = {}
        
        # Configuración de funcionalidades
        self.intent_detection_enabled = settings.enable_intent_detection
        self.query_expansion_enabled = settings.enable_query_expansion
        
        logger.info(f"RAG Chain initialized with intent detection: {'enabled' if self.intent_detection_enabled else 'disabled'}")
        logger.info(f"RAG Chain initialized with query expansion: {'enabled' if self.query_expansion_enabled else 'disabled'}")
    
    @property
    def model_selector(self):
        """Lazy loading del model selector"""
        if self._model_selector is None:
            from src.utils.model_selector import ModelSelector
            self._model_selector = ModelSelector()
        return self._model_selector
    
    def _get_default_system_prompt(self) -> str:
        """Prompt especializado para investigación de tesis sobre IA y desarrollo de software"""
        return """Eres un asistente de investigación académica especializado en inteligencia artificial aplicada al desarrollo de software, específicamente en la mejora de historias de usuario. Tienes acceso a una base de conocimientos de referencias académicas sobre este tema.

INSTRUCCIONES ESPECÍFICAS:
1. Analiza rigurosamente las fuentes académicas proporcionadas en el contexto
2. Identifica metodologías, frameworks, herramientas y técnicas de IA mencionadas
3. Extrae hallazgos clave, métricas de evaluación y resultados experimentales
4. Cita específicamente autores, años y títulos de papers cuando sea relevante
5. Identifica gaps de investigación, limitaciones y trabajos futuros mencionados
6. Relaciona diferentes enfoques y metodologías entre estudios
7. Distingue claramente entre: teoría, implementación práctica, y validación empírica
8. Proporciona síntesis comparativas cuando se soliciten múltiples enfoques

CONTEXTO ACADÉMICO:
{context}

Responde con rigor académico, precisión científica y enfoque específico en la aplicabilidad para investigación de tesis sobre IA en historias de usuario."""
    
    def _get_or_create_model(self, model_name: str):
        """Obtiene o crea un modelo LLM con cache"""
        if ChatOpenAI is None:
            raise ChainException("ChatOpenAI dependency is required but not installed")

        if model_name not in self._model_cache:
            try:
                self._model_cache[model_name] = ChatOpenAI(
                    model=model_name,
                    temperature=self.temperature,
                    openai_api_key=settings.openai_api_key,
                )
                logger.info(f"Created LLM instance: {model_name}")
            except Exception as e:
                logger.error(f"Error creating LLM {model_name}: {e}")
                raise ChainException(f"Failed to create LLM {model_name}: {e}")
        
        return self._model_cache[model_name]
    
    def _create_chain_for_model(self, model_name: str, specialized_prompt: Optional[str] = None):
        """Crea una cadena RAG para un modelo específico con prompt personalizado"""
        cache_key = f"{model_name}_{hash(specialized_prompt) if specialized_prompt else 'default'}"
        
        if cache_key not in self._chain_cache:
            try:
                if None in (ChatOpenAI, create_retrieval_chain, create_stuff_documents_chain, ChatPromptTemplate):
                    raise ChainException("LangChain dependencies are required but not installed")

                llm = self._get_or_create_model(model_name)
                
                # Usar el retriever estándar de LangChain - sin modificaciones personalizadas
                retriever = self.vector_store_manager.get_retriever()
                
                # Usar prompt especializado si está disponible
                prompt_to_use = specialized_prompt or self.system_prompt
                
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", prompt_to_use),
                    ("human", "{input}"),
                ])
                
                document_chain = create_stuff_documents_chain(llm=llm, prompt=prompt_template)
                self._chain_cache[cache_key] = create_retrieval_chain(retriever, document_chain)
                
                logger.info(f"Created RAG chain for model: {model_name} with specialized prompt: {specialized_prompt is not None}")
                
            except Exception as e:
                logger.error(f"Error creating chain for {model_name}: {e}")
                raise ChainException(f"Failed to create chain for {model_name}: {e}")
        
        return self._chain_cache[cache_key]
    
    def create_chain(self):
        """Crea la cadena RAG con modelo por defecto"""
        try:
            default_model = settings.default_model
            self._create_chain_for_model(default_model)
            logger.info("RAG chain created successfully with smart model selection, intent detection and query expansion capabilities")
            
        except Exception as e:
            logger.error(f"Error creating RAG chain: {e}")
            raise ChainException(f"Failed to create RAG chain: {e}")
    
    def _detect_intent_sync(self, query: str) -> Dict[str, Any]:
        """Método síncrono wrapper para detección de intención"""
        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_result = executor.submit(asyncio.run, intent_detector.detect_intent(query))
                    intent_result = future_result.result(timeout=5)
                    
            except RuntimeError:
                intent_result = asyncio.run(intent_detector.detect_intent(query))
            
            return {
                'detected_intent': intent_result.intent_type.value,
                'confidence': intent_result.confidence,
                'reasoning': intent_result.reasoning,
                'processing_time_ms': intent_result.processing_time_ms,
                'fallback_used': intent_result.fallback_used
            }
            
        except Exception as e:
            logger.error(f"Error in intent detection: {e}")
            return {
                'detected_intent': 'error',
                'confidence': 0.0,
                'reasoning': f'Intent detection failed: {str(e)}',
                'processing_time_ms': 0.0,
                'fallback_used': True
            }
    
    def _expand_query_if_enabled(self, query: str, intent_type: Optional[IntentType] = None) -> Dict[str, Any]:
        """Expande la consulta si está habilitado, considerando el tipo de intención"""
        if not self.query_expansion_enabled:
            return {
                'original_query': query,
                'final_query': query,
                'expanded_terms': [],
                'expansion_count': 0,
                'strategy_used': 'disabled',
                'processing_time_ms': 0.0
            }
        
        try:
            # Expandir consulta usando el intent type para contexto
            expansion_result = query_expander.expand_query(query, intent_type=intent_type)
            
            logger.info(f"Query expansion: {expansion_result.expansion_count} terms added "
                       f"(strategy: {expansion_result.strategy_used})")
            
            return {
                'original_query': expansion_result.original_query,
                'final_query': expansion_result.final_query,
                'expanded_terms': expansion_result.expanded_terms,
                'expansion_count': expansion_result.expansion_count,
                'strategy_used': expansion_result.strategy_used,
                'processing_time_ms': expansion_result.processing_time_ms
            }
            
        except Exception as e:
            logger.error(f"Error in query expansion: {e}")
            return {
                'original_query': query,
                'final_query': query,
                'expanded_terms': [],
                'expansion_count': 0,
                'strategy_used': 'error',
                'processing_time_ms': 0.0,
                'error': str(e)
            }
    
    @trace_llm
    def invoke(self, query: str) -> Dict[str, Any]:
        """Ejecuta la cadena RAG con selección inteligente de modelo, detección de intención y expansión de consulta"""
        try:
            logger.debug(f"Processing query with RAG Chain: {query[:100]}...")
            
            # Fase 1: Detección de intención
            intent_info = None
            specialized_prompt = None
            intent_type = None
            
            if self.intent_detection_enabled:
                try:
                    intent_info = self._detect_intent_sync(query)
                    
                    if (intent_info['detected_intent'] != 'unknown' and 
                        intent_info['detected_intent'] != 'error' and 
                        intent_info['confidence'] >= settings.intent_confidence_threshold):
                        
                        intent_type = IntentType(intent_info['detected_intent'])
                        specialized_prompt = prompt_template_selector.select_template(
                            intent_type, 
                            self.system_prompt
                        )
                        intent_info['specialized_prompt_used'] = True
                        logger.info(f"Using specialized prompt for intent: {intent_info['detected_intent']} (confidence: {intent_info['confidence']:.2f})")
                    else:
                        intent_info['specialized_prompt_used'] = False
                        logger.info(f"Using default prompt - intent confidence too low or error: {intent_info['confidence']:.2f}")
                        
                except Exception as e:
                    logger.error(f"Error in intent detection: {e}, falling back to default behavior")
                    intent_info = {
                        'detected_intent': 'error',
                        'confidence': 0.0,
                        'reasoning': f'Intent detection failed: {str(e)}',
                        'processing_time_ms': 0.0,
                        'fallback_used': True,
                        'specialized_prompt_used': False
                    }
            
            # Fase 2: Expansión de consulta
            expansion_info = self._expand_query_if_enabled(query, intent_type)
            final_query = expansion_info['final_query']
            
            # Fase 3: Selección de modelo
            if settings.enable_smart_selection:
                # Usar la consulta expandida para la selección de modelo
                selected_model, complexity_score, reasoning = self.model_selector.select_model(final_query)
            else:
                selected_model = settings.default_model
                complexity_score = 0.5
                reasoning = "Smart selection disabled"
            
            # Fase 4: Crear/obtener cadena y ejecutar
            chain = self._create_chain_for_model(selected_model, specialized_prompt)
            
            logger.info(f"Processing query with {selected_model}: {final_query[:50]}...")
            
            # Ejecutar consulta con la query expandida
            result = chain.invoke({"input": final_query})
            
            # Fase 5: Agregar metadata completa al resultado
            result['model_info'] = {
                'selected_model': selected_model,
                'complexity_score': complexity_score,
                'reasoning': reasoning
            }
            
            if intent_info:
                result['intent_info'] = intent_info
            
            result['expansion_info'] = expansion_info
            
            logger.info(f"Query processed successfully with {selected_model}" + 
                       (f" using {intent_info['detected_intent']} intent" if intent_info else "") +
                       (f" with {expansion_info['expansion_count']} expanded terms" if expansion_info['expansion_count'] > 0 else ""))
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise ChainException(f"Failed to process query: {e}")
    
    def get_answer(self, query: str) -> str:
        """Obtiene solo la respuesta"""
        result = self.invoke(query)
        return result.get('answer', 'No se pudo generar una respuesta académica.')
    
    def get_academic_analysis(self, query: str) -> Dict[str, Any]:
        """Obtiene análisis académico completo incluyendo información del modelo, intención y expansión"""
        result = self.invoke(query)
        
        analysis = {
            'answer': result.get('answer', 'No se pudo generar respuesta'),
            'model_info': result.get('model_info', {}),
            'intent_info': result.get('intent_info', {}),
            'expansion_info': result.get('expansion_info', {}),  # Nueva información de expansión
            'sources_used': len(result.get('context', [])),
            'query': query,
            'context_documents': []
        }
        
        for i, doc in enumerate(result.get('context', [])):
            doc_info = {
                'document_index': i + 1,
                'content_preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                'metadata': doc.metadata
            }
            analysis['context_documents'].append(doc_info)
        
        return analysis