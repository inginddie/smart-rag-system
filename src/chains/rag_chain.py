# -*- coding: utf-8 -*-
"""
Enhanced RAG Chain with Template Orchestrator Integration
"""
from typing import Any, Dict, Optional

try:
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - optional dependency
    ChatOpenAI = None  # type: ignore
    create_retrieval_chain = None  # type: ignore
    create_stuff_documents_chain = None  # type: ignore
    ChatPromptTemplate = None  # type: ignore

import asyncio

from config.settings import settings
from src.storage.vector_store import VectorStoreManager
from src.utils.exceptions import ChainException
# ======= NUEVAS IMPORTACIONES PARA TEMPLATE ORCHESTRATOR =======
from src.utils.intent_detector import IntentType, intent_detector
from src.utils.logger import setup_logger
from src.utils.template_orchestrator import template_orchestrator
from src.utils.tracing import trace_llm

logger = setup_logger()


class RAGChain:
    """RAG Chain con Template Orchestrator integrado"""

    def __init__(self, system_prompt: Optional[str] = None, temperature: float = 0.1):

        self.temperature = temperature
        self.vector_store_manager = VectorStoreManager()

        # Modelo selector (lazy loading)
        self._model_selector = None

        # Template orchestrator
        self.template_orchestrator = template_orchestrator

        # Prompt por defecto
        self.system_prompt = system_prompt or self._get_default_system_prompt()

        # Cache de modelos y chains
        self._model_cache = {}
        self._chain_cache = {}

        # Template integration habilitado
        self.template_integration_enabled = getattr(
            settings, "enable_intent_detection", True
        )

        logger.info(
            f"RAG Chain initialized with template orchestrator: {'enabled' if self.template_integration_enabled else 'disabled'}"
        )

    @property
    def model_selector(self):
        """Lazy loading del model selector"""
        if self._model_selector is None:
            from src.utils.model_selector import ModelSelector

            self._model_selector = ModelSelector()
        return self._model_selector

    def _get_default_system_prompt(self) -> str:
        """Prompt por defecto para investigación académica"""
        return """Eres un asistente de investigación académica especializado en inteligencia artificial aplicada al desarrollo de software, específicamente en la mejora de historias de usuario.

INSTRUCCIONES:
1. Analiza rigurosamente las fuentes académicas proporcionadas
2. Identifica metodologías, frameworks, herramientas y técnicas de IA
3. Extrae hallazgos clave, métricas de evaluación y resultados experimentales
4. Cita específicamente autores, años y títulos cuando sea relevante
5. Identifica gaps de investigación, limitaciones y trabajos futuros
6. Relaciona diferentes enfoques y metodologías entre estudios
7. Distingue entre teoría, implementación práctica, y validación empírica

FORMATO DE RESPUESTA:
- Respuestas estructuradas y académicamente rigurosas
- Incluye citas específicas: (Autor, Año) o [Título del paper]
- Organiza la información en secciones lógicas
- Destaca controversias o debates en el área
- Sugiere conexiones entre diferentes líneas de investigación

CONTEXTO ACADÉMICO:
{context}

Responde con rigor académico, precisión científica y enfoque específico en investigación sobre IA en historias de usuario."""

    def _get_or_create_model(self, model_name: str):
        """Obtiene o crea modelo con cache"""
        if ChatOpenAI is None:
            raise ChainException("ChatOpenAI dependency is required but not installed")

        # Always force reload settings and check if we need to invalidate cache
        from config.settings import Settings

        current_settings = Settings()

        # Check if we have a cached model with potentially wrong API key
        if model_name in self._model_cache:
            cached_model = self._model_cache[model_name]
            # Check if the cached model has the wrong API key
            if (
                hasattr(cached_model, "openai_api_key")
                and cached_model.openai_api_key != current_settings.openai_api_key
            ):
                logger.info(f"API key changed, invalidating cached model: {model_name}")
                del self._model_cache[model_name]
            elif (
                hasattr(cached_model, "client")
                and hasattr(cached_model.client, "api_key")
                and cached_model.client.api_key != current_settings.openai_api_key
            ):
                logger.info(
                    f"API key changed in client, invalidating cached model: {model_name}"
                )
                del self._model_cache[model_name]

        if model_name not in self._model_cache:
            try:
                self._model_cache[model_name] = ChatOpenAI(
                    model=model_name,
                    temperature=self.temperature,
                    openai_api_key=current_settings.openai_api_key,
                )
                logger.info(
                    f"Created LLM instance: {model_name} with API key: ...{current_settings.openai_api_key[-10:]}"
                )
            except Exception as e:
                logger.error(f"Error creating LLM {model_name}: {e}")
                raise ChainException(f"Failed to create LLM {model_name}: {e}")

        return self._model_cache[model_name]

    def clear_model_cache(self):
        """Limpiar cache de modelos - útil cuando cambia API key"""
        logger.info("Clearing model cache")
        self._model_cache.clear()

    def create_chain(self):
        """Crea la cadena RAG con modelo por defecto"""
        try:
            default_model = settings.default_model
            self._create_chain_for_model(default_model)
            logger.info(
                "RAG chain created successfully with template orchestrator support"
            )

        except Exception as e:
            logger.error(f"Error creating RAG chain: {e}")
            raise ChainException(f"Failed to create RAG chain: {e}")

    def _create_chain_for_model(
        self, model_name: str, specialized_prompt: Optional[str] = None
    ):
        """Crea cadena para modelo específico con prompt personalizado"""
        cache_key = f"{model_name}_{hash(specialized_prompt) if specialized_prompt else 'default'}"

        if cache_key not in self._chain_cache:
            try:
                if None in (
                    ChatOpenAI,
                    create_retrieval_chain,
                    create_stuff_documents_chain,
                    ChatPromptTemplate,
                ):
                    raise ChainException(
                        "LangChain dependencies are required but not installed"
                    )

                llm = self._get_or_create_model(model_name)
                retriever = self.vector_store_manager.get_retriever()

                prompt_to_use = specialized_prompt or self.system_prompt

                prompt_template = ChatPromptTemplate.from_messages(
                    [
                        ("system", prompt_to_use),
                        ("human", "{input}"),
                    ]
                )

                document_chain = create_stuff_documents_chain(
                    llm=llm, prompt=prompt_template
                )
                self._chain_cache[cache_key] = create_retrieval_chain(
                    retriever, document_chain
                )

                logger.info(f"Created RAG chain for model: {model_name}")

            except Exception as e:
                logger.error(f"Error creating chain for {model_name}: {e}")
                raise ChainException(f"Failed to create chain for {model_name}: {e}")

        return self._chain_cache[cache_key]

    def _detect_intent_sync(self, query: str) -> Dict[str, Any]:
        """Detección de intención síncrona"""
        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future_result = executor.submit(
                        asyncio.run, intent_detector.detect_intent(query)
                    )
                    intent_result = future_result.result(timeout=5)

            except RuntimeError:
                intent_result = asyncio.run(intent_detector.detect_intent(query))

            return {
                "detected_intent": intent_result.intent_type.value,
                "confidence": intent_result.confidence,
                "reasoning": intent_result.reasoning,
                "processing_time_ms": intent_result.processing_time_ms,
                "fallback_used": intent_result.fallback_used,
                "matched_patterns": intent_result.matched_patterns,
                "intent_result_object": intent_result,  # Para template orchestrator
            }

        except Exception as e:
            logger.error(f"Error in intent detection: {e}")
            return {
                "detected_intent": "error",
                "confidence": 0.0,
                "reasoning": f"Intent detection failed: {str(e)}",
                "processing_time_ms": 0.0,
                "fallback_used": True,
                "matched_patterns": [],
                "intent_result_object": None,
            }

    @trace_llm
    def invoke(self, query: str) -> Dict[str, Any]:
        """Pipeline RAG completo con template orchestrator"""
        try:
            logger.debug(f"Processing query with enhanced RAG Chain: {query[:100]}...")

            # ======= TEMPLATE ORCHESTRATOR INTEGRATION =======
            template_info = None
            specialized_prompt = None
            intent_info = None

            if self.template_integration_enabled:
                try:
                    # 1. Intent Detection
                    intent_info = self._detect_intent_sync(query)

                    if intent_info.get("intent_result_object"):
                        # 2. Model Selection (para user expertise y complexity)
                        if settings.enable_smart_selection:
                            selected_model, complexity_score, reasoning = (
                                self.model_selector.select_model(query)
                            )
                        else:
                            selected_model = settings.default_model
                            complexity_score = 0.5
                            reasoning = "Smart selection disabled"

                        # 3. Template Selection via Orchestrator
                        template_selection = self.template_orchestrator.select_template(
                            intent_result=intent_info["intent_result_object"],
                            user_expertise="intermediate",  # TODO: obtener de user profile
                            query_complexity=complexity_score,
                            base_prompt=self.system_prompt,
                        )

                        # 4. Usar template especializado si selection fue exitosa
                        if not template_selection.fallback_used:
                            specialized_prompt = template_selection.template_prompt
                            template_info = {
                                "template_used": True,
                                "selection_reason": template_selection.selection_reason,
                                "confidence_score": template_selection.confidence_score,
                                "processing_time_ms": template_selection.processing_time_ms,
                                "template_metadata": {
                                    "sections": template_selection.template_metadata.sections,
                                    "expected_length": template_selection.template_metadata.expected_length,
                                    "academic_rigor": template_selection.template_metadata.academic_rigor,
                                },
                            }
                            logger.info(
                                f"Using specialized template for {intent_info['detected_intent']}"
                            )
                        else:
                            template_info = {
                                "template_used": False,
                                "selection_reason": template_selection.selection_reason,
                                "fallback_used": True,
                            }
                            logger.info(
                                "Using default prompt - template selection fell back"
                            )

                except Exception as e:
                    logger.error(f"Error in template orchestration: {e}")
                    template_info = {
                        "template_used": False,
                        "error": str(e),
                        "fallback_used": True,
                    }

            # ======= MODEL SELECTION =======
            if settings.enable_smart_selection:
                selected_model, complexity_score, reasoning = (
                    self.model_selector.select_model(query)
                )
            else:
                selected_model = settings.default_model
                complexity_score = 0.5
                reasoning = "Smart selection disabled"

            # ======= DOCUMENT RETRIEVAL =======
            # Usar intent_type para enhanced retrieval si está disponible
            intent_type = None
            if intent_info and intent_info.get("intent_result_object"):
                intent_type = intent_info["intent_result_object"].intent_type

            # Crear retriever que soporte intent-aware search
            retriever = self.vector_store_manager.get_retriever()

            # ======= CHAIN CREATION Y EXECUTION =======
            # Crear cadena con template especializado o default
            if None in (
                ChatOpenAI,
                create_retrieval_chain,
                create_stuff_documents_chain,
                ChatPromptTemplate,
            ):
                raise ChainException(
                    "LangChain dependencies are required but not installed"
                )

            llm = self._get_or_create_model(selected_model)
            prompt_to_use = specialized_prompt or self.system_prompt

            prompt_template = ChatPromptTemplate.from_messages(
                [
                    ("system", prompt_to_use),
                    ("human", "{input}"),
                ]
            )

            document_chain = create_stuff_documents_chain(
                llm=llm, prompt=prompt_template
            )
            chain = create_retrieval_chain(retriever, document_chain)

            logger.info(f"Processing query with {selected_model}: {query[:50]}...")

            # Ejecutar consulta
            result = chain.invoke({"input": query})

            # ======= RESULT ENHANCEMENT =======
            result["model_info"] = {
                "selected_model": selected_model,
                "complexity_score": complexity_score,
                "reasoning": reasoning,
            }

            if intent_info:
                result["intent_info"] = intent_info

            if template_info:
                result["template_info"] = template_info

            # Información de expansión si existe
            expansion_info = None
            if result.get("context") and len(result["context"]) > 0:
                first_doc = result["context"][0]
                if (
                    hasattr(first_doc, "metadata")
                    and "query_expansion" in first_doc.metadata
                ):
                    expansion_info = first_doc.metadata["query_expansion"]
                    result["expansion_info"] = expansion_info

            # Log resultado
            template_used = template_info and template_info.get("template_used", False)
            intent_detected = intent_info and intent_info.get(
                "detected_intent", "unknown"
            )

            logger.info(
                f"Query processed successfully: model={selected_model}, "
                f"intent={intent_detected}, template_used={template_used}"
            )

            return result

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise ChainException(f"Failed to process query: {e}")

    def get_answer(self, query: str) -> str:
        """Obtiene solo la respuesta"""
        result = self.invoke(query)
        return result.get("answer", "No se pudo generar una respuesta académica.")

    def get_academic_analysis(self, query: str) -> Dict[str, Any]:
        """Análisis académico completo con template info"""
        result = self.invoke(query)

        analysis = {
            "answer": result.get("answer", "No se pudo generar respuesta"),
            "model_info": result.get("model_info", {}),
            "intent_info": result.get("intent_info", {}),
            "template_info": result.get("template_info", {}),
            "expansion_info": result.get("expansion_info", {}),
            "sources_used": len(result.get("context", [])),
            "query": query,
            "context_documents": [],
        }

        # Agregar información de contexto
        for i, doc in enumerate(result.get("context", [])):
            doc_info = {
                "document_index": i + 1,
                "content_preview": (
                    doc.page_content[:200] + "..."
                    if len(doc.page_content) > 200
                    else doc.page_content
                ),
                "metadata": doc.metadata,
            }
            analysis["context_documents"].append(doc_info)

        return analysis
