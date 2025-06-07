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

logger = setup_logger()

class RAGChain:
    """Cadena RAG con selección inteligente de modelos para investigación académica"""
    
    def __init__(self, 
                 system_prompt: Optional[str] = None,
                 temperature: float = 0.1):
        
        self.temperature = temperature
        self.vector_store_manager = VectorStoreManager()
        
        # Importar ModelSelector solo cuando se necesite para evitar dependencias circulares
        self._model_selector = None
        
        # Prompt especializado para investigación de tesis
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        # Cache de modelos para evitar reinicialización
        self._model_cache = {}
        self._chain_cache = {}
    
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

TIPOS DE CONSULTAS QUE PUEDES RESOLVER:
- Estado del arte en IA para historias de usuario
- Metodologías y frameworks propuestos
- Herramientas y técnicas específicas (NLP, ML, etc.)
- Métricas de evaluación utilizadas
- Casos de estudio y validaciones empíricas
- Gaps de investigación identificados
- Comparación entre diferentes enfoques
- Fundamentos teóricos y conceptuales

FORMATO DE RESPUESTA:
- Proporciona respuestas estructuradas y académicamente rigurosas
- Incluye citas específicas: (Autor, Año) o [Título del paper]
- Organiza la información en secciones lógicas cuando sea apropiado
- Destaca controversias o debates en el área
- Sugiere conexiones entre diferentes líneas de investigación
- Si hay limitaciones en el contexto, menciona qué información adicional sería útil

DIRECTRICES ACADÉMICAS:
- Mantén rigor científico en todas las respuestas
- Diferencia entre hechos establecidos, hipótesis y especulaciones
- Identifica cuando hay consenso o divergencia en la literatura
- Proporciona contexto histórico cuando sea relevante
- Señala implicaciones prácticas para el desarrollo de software

CONTEXTO ACADÉMICO:
{context}

Responde con rigor académico, precisión científica y enfoque específico en la aplicabilidad para investigación de tesis sobre IA en historias de usuario."""
    
    def _get_or_create_model(self, model_name: str):
        """Obtiene o crea un modelo LLM con cache"""
        if ChatOpenAI is None:
            raise ChainException(
                "ChatOpenAI dependency is required but not installed"
            )

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
    
    def _create_chain_for_model(self, model_name: str):
        """Crea una cadena RAG para un modelo específico"""
        if model_name not in self._chain_cache:
            try:
                if None in (ChatOpenAI, create_retrieval_chain, create_stuff_documents_chain, ChatPromptTemplate):
                    raise ChainException("LangChain dependencies are required but not installed")

                llm = self._get_or_create_model(model_name)
                retriever = self.vector_store_manager.get_retriever()
                
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", self.system_prompt),
                    ("human", "{input}"),
                ])
                
                document_chain = create_stuff_documents_chain(llm=llm, prompt=prompt_template)
                self._chain_cache[model_name] = create_retrieval_chain(retriever, document_chain)
                
                logger.info(f"Created RAG chain for model: {model_name}")
                
            except Exception as e:
                logger.error(f"Error creating chain for {model_name}: {e}")
                raise ChainException(f"Failed to create chain for {model_name}: {e}")
        
        return self._chain_cache[model_name]
    
    def create_chain(self):
        """Crea la cadena RAG con modelo por defecto"""
        try:
            # Crear cadena con modelo por defecto para compatibilidad
            default_model = settings.default_model
            self._create_chain_for_model(default_model)
            logger.info("RAG chain created successfully with smart model selection")
            
        except Exception as e:
            logger.error(f"Error creating RAG chain: {e}")
            raise ChainException(f"Failed to create RAG chain: {e}")
    
    def invoke(self, query: str) -> Dict[str, Any]:
        """Ejecuta la cadena RAG con selección inteligente de modelo"""
        try:
            # Seleccionar modelo basado en complejidad de la consulta
            if settings.enable_smart_selection:
                selected_model, complexity_score, reasoning = self.model_selector.select_model(query)
            else:
                selected_model = settings.default_model
                complexity_score = 0.5
                reasoning = "Smart selection disabled"
            
            # Crear/obtener cadena para el modelo seleccionado
            chain = self._create_chain_for_model(selected_model)
            
            logger.info(f"Processing query with {selected_model}: {query[:50]}...")
            
            # Ejecutar consulta
            result = chain.invoke({"input": query})
            
            # Agregar información de selección de modelo al resultado
            result['model_info'] = {
                'selected_model': selected_model,
                'complexity_score': complexity_score,
                'reasoning': reasoning
            }
            
            logger.info(f"Query processed successfully with {selected_model}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise ChainException(f"Failed to process query: {e}")
    
    def get_answer(self, query: str) -> str:
        """Obtiene solo la respuesta"""
        result = self.invoke(query)
        return result.get('answer', 'No se pudo generar una respuesta académica.')
    
    def get_academic_analysis(self, query: str) -> Dict[str, Any]:
        """Obtiene análisis académico completo incluyendo información del modelo"""
        result = self.invoke(query)
        
        # Extraer información adicional para análisis académico
        analysis = {
            'answer': result.get('answer', 'No se pudo generar respuesta'),
            'model_info': result.get('model_info', {}),
            'sources_used': len(result.get('context', [])),
            'query': query,
            'context_documents': []
        }
        
        # Agregar información de contexto para referencias
        for i, doc in enumerate(result.get('context', [])):
            doc_info = {
                'document_index': i + 1,
                'content_preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                'metadata': doc.metadata
            }
            analysis['context_documents'].append(doc_info)
        
        return analysis