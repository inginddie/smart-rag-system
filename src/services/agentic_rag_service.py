# -*- coding: utf-8 -*-
"""
Servicio Agentic RAG que extiende el RAGService existente.
Mantiene compatibilidad completa con la API actual.
"""

from typing import Dict, List, Any, Optional
from src.services.rag_service import RAGService
from src.agents.base.agent import BaseAgent, AgentResponse
from src.agents.memory.manager import MemoryManager
from src.agents.specialized.document_search import DocumentSearchAgent
from src.utils.logger import setup_logger
from src.utils.exceptions import RAGException
import asyncio
import uuid

logger = setup_logger()

class AgenticRAGService(RAGService):
    """
    Servicio RAG Agentic que extiende funcionalidad existente.
    
    Características:
    - Compatibilidad 100% con RAGService actual
    - Agentes especializados para tareas específicas
    - Sistema de memoria distribuida
    - Selección automática de agentes
    - Razonamiento iterativo (preparado para ReAct)
    """
    
    def __init__(self):
        # Inicializar servicio base
        super().__init__()
        
        # Componentes agentic
        self.memory_manager = None
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_selector = None
        self.agentic_mode = False  # Modo gradual
        
        # Métricas agentic
        self.agentic_metrics = {
            "agent_queries": 0,
            "fallback_to_classic": 0,
            "multi_agent_queries": 0
        }
        
        logger.info("AgenticRAGService initialized (classic mode)")
    
    def initialize_agentic_mode(self, 
                               redis_url: str = "redis://localhost:6379/0",
                               enable_agents: bool = True) -> bool:
        """
        Inicializa modo agentic de forma gradual.
        Mantiene funcionalidad clásica como fallback.
        """
        try:
            logger.info("Initializing agentic mode...")
            
            # Inicializar memoria distribuida
            self.memory_manager = MemoryManager(
                redis_url=redis_url,
                vector_store_manager=self.vector_store_manager
            )
            
            if enable_agents:
                # Crear agente especializado en documentos
                self.agents["document_search"] = DocumentSearchAgent(
                    vector_store_manager=self.vector_store_manager,
                    rag_chain=self.rag_chain,
                    memory_manager=self.memory_manager
                )
                
                logger.info(f"Initialized {len(self.agents)} specialized agents")
            
            # Activar modo agentic
            self.agentic_mode = True
            logger.info("✅ Agentic mode activated")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing agentic mode: {e}")
            logger.warning("Continuing in classic RAG mode")
            return False
    
    def initialize(self, force_reindex: bool = False) -> bool:
        """
        Inicializa servicio con soporte agentic opcional.
        Mantiene compatibilidad con método original.
        """
        # Inicializar base RAG primero
        base_success = super().initialize(force_reindex)
        
        if base_success:
            # Intentar inicializar modo agentic
            try:
                self.initialize_agentic_mode()
            except Exception as e:
                logger.warning(f"Agentic initialization failed: {e}")
                # Continuar en modo clásico
                pass
        
        return base_success
    
    async def query_agentic(self, 
                           question: str, 
                           include_sources: bool = False,
                           session_id: str = None) -> Dict[str, Any]:
        """
        Procesa consulta usando agentes especializados.
        Nueva funcionalidad agentic sin romper API existente.
        """
        if not self.agentic_mode:
            # Fallback a modo clásico
            logger.debug("Agentic mode not available, using classic RAG")
            self.agentic_metrics["fallback_to_classic"] += 1
            return self.query(question, include_sources)
        
        try:
            session_id = session_id or str(uuid.uuid4())
            
            # Agregar consulta al historial de conversación
            if self.memory_manager:
                self.memory_manager.add_to_conversation(
                    session_id, 
                    "user", 
                    question
                )
            
            # Seleccionar agente más apropiado
            selected_agent = await self._select_best_agent(question)
            
            if selected_agent:
                logger.info(f"Selected agent: {selected_agent.name}")
                
                # Obtener contexto de memoria si está disponible
                context = await self._get_conversation_context(session_id)
                
                # Procesar con agente
                agent_response = await selected_agent.process_query(question, context)
                
                # Convertir a formato compatible
                response = self._convert_agent_response(agent_response, include_sources)
                response["question"] = question
                
                # Guardar respuesta en conversación
                if self.memory_manager:
                    self.memory_manager.add_to_conversation(
                        session_id,
                        "assistant", 
                        response["answer"],
                        metadata={"agent": selected_agent.name}
                    )
                
                self.agentic_metrics["agent_queries"] += 1
                return response
                
            else:
                # No hay agente apropiado, usar RAG clásico
                logger.debug("No suitable agent found, falling back to classic RAG")
                self.agentic_metrics["fallback_to_classic"] += 1
                return self.query(question, include_sources)
                
        except Exception as e:
            logger.error(f"Error in agentic query: {e}")
            # Fallback seguro a RAG clásico
            self.agentic_metrics["fallback_to_classic"] += 1
            return self.query(question, include_sources)
    
    def query(self, question: str, include_sources: bool = False) -> Dict[str, Any]:
        """
        Método clásico preservado para compatibilidad.
        Con mejoras opcionales si modo agentic está disponible.
        """
        # Si modo agentic está disponible, intentar usarlo de forma async
        if self.agentic_mode and self.agents:
            try:
                # Ejecutar consulta agentic de forma sincrónica
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Si ya hay un loop corriendo, crear task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self.query_agentic(question, include_sources)
                        )
                        return future.result(timeout=30)
                else:
                    # Ejecutar en nuevo loop
                    return asyncio.run(
                        self.query_agentic(question, include_sources)
                    )
            except Exception as e:
                logger.warning(f"Agentic query failed, using classic: {e}")
        
        # Ejecutar método clásico original
        return super().query(question, include_sources)
    
    async def _select_best_agent(self, question: str) -> Optional[BaseAgent]:
        """
        Selecciona el mejor agente para manejar la consulta.
        """
        if not self.agents:
            return None
        
        best_agent = None
        best_score = 0.0
        
        for agent_name, agent in self.agents.items():
            try:
                score = agent.can_handle_query(question)
                logger.debug(f"Agent {agent_name} score: {score}")
                
                if score > best_score:
                    best_score = score
                    best_agent = agent
                    
            except Exception as e:
                logger.error(f"Error evaluating agent {agent_name}: {e}")
                continue
        
        # Solo usar agente si score es suficientemente alto
        if best_score >= 0.3:
            return best_agent
        
        return None
    
    async def _get_conversation_context(self, session_id: str) -> Dict[str, Any]:
        """
        Obtiene contexto de conversación para el agente.
        """
        context = {"session_id": session_id}
        
        if self.memory_manager:
            try:
                # Obtener historial reciente
                history = self.memory_manager.get_conversation_history(session_id, limit=5)
                context["conversation_history"] = history
                
                # Obtener memoria semántica relevante si hay historial
                if history:
                    last_messages = [msg["content"] for msg in history[-3:]]
                    semantic_context = self.memory_manager.search_semantic_memory(
                        " ".join(last_messages), 
                        k=3
                    )
                    context["semantic_memory"] = semantic_context
                    
            except Exception as e:
                logger.warning(f"Error getting conversation context: {e}")
        
        return context
    
    def _convert_agent_response(self, 
                               agent_response: AgentResponse, 
                               include_sources: bool = False) -> Dict[str, Any]:
        """
        Convierte respuesta de agente al formato clásico para compatibilidad.
        """
        response = {
            "answer": agent_response.content,
            "question": "",  # Se establece externamente
            "model_info": agent_response.metadata.get("model_info", {}),
            "agent_info": {
                "agent_name": agent_response.agent_name,
                "agent_id": agent_response.agent_id,
                "confidence": agent_response.confidence,
                "reasoning": agent_response.reasoning
            }
        }
        
        if include_sources and agent_response.sources:
            response["sources"] = agent_response.sources
        
        return response
    
    def get_simple_answer(self, question: str) -> str:
        """
        Preserva método simple para compatibilidad.
        """
        result = self.query(question)
        return result["answer"]
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de agentes (nueva funcionalidad).
        """
        stats = {
            "agentic_mode": self.agentic_mode,
            "agents_count": len(self.agents),
            "metrics": self.agentic_metrics.copy()
        }
        
        if self.agents:
            agent_stats = {}
            for name, agent in self.agents.items():
                agent_stats[name] = agent.get_stats()
            stats["agent_details"] = agent_stats
        
        if self.memory_manager:
            stats["memory_stats"] = self.memory_manager.get_memory_stats()
        
        return stats
    
    def get_status(self) -> Dict[str, Any]:
        """
        Extiende status con información agentic.
        """
        base_status = super().get_status()
        
        # Agregar información agentic
        base_status.update({
            "agentic_mode": self.agentic_mode,
            "agents_available": list(self.agents.keys()),
            "memory_manager": self.memory_manager is not None,
            "agentic_metrics": self.agentic_metrics
        })
        
        return base_status
    
    def disable_agentic_mode(self):
        """
        Desactiva modo agentic temporalmente.
        """
        self.agentic_mode = False
        logger.info("Agentic mode disabled, using classic RAG")
    
    def enable_agentic_mode(self):
        """
        Reactiva modo agentic si está inicializado.
        """
        if self.agents and self.memory_manager:
            self.agentic_mode = True
            logger.info("Agentic mode enabled")
        else:
            logger.warning("Cannot enable agentic mode - not properly initialized")

# ================================
# FACTORY PARA MIGRACIÓN GRADUAL
# ================================

def create_rag_service(agentic: bool = True) -> RAGService:
    """
    Factory function para crear servicio RAG.
    Permite migración gradual controlada.
    """
    if agentic:
        try:
            service = AgenticRAGService()
            logger.info("Created AgenticRAGService")
            return service
        except Exception as e:
            logger.error(f"Failed to create AgenticRAGService: {e}")
            logger.info("Falling back to classic RAGService")
            return RAGService()
    else:
        logger.info("Created classic RAGService")
        return RAGService()
