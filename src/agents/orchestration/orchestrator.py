#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentOrchestrator - Orquestación inteligente de agentes
Implementa CA5.1 y CA5.2: Selección y Orquestación Multi-Agente
"""

from typing import Dict, List, Any, Optional
import logging
import asyncio
from datetime import datetime

from src.agents.base.agent import BaseAgent, AgentResponse
from src.agents.base.registry import AgentRegistry
from src.agents.orchestration.selector import AgentSelector, SelectionDecision
from src.agents.orchestration.workflow import WorkflowEngine

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orquestador inteligente de agentes
    
    Responsabilidades:
    - Coordinar selección de agentes
    - Ejecutar agentes individuales o múltiples
    - Sintetizar resultados de múltiples agentes
    - Gestionar fallbacks y errores
    """
    
    def __init__(
        self,
        agent_registry: AgentRegistry,
        confidence_threshold: float = 0.7,
        enable_multi_agent: bool = False
    ):
        """
        Inicializa el orquestador
        
        Args:
            agent_registry: Registro de agentes disponibles
            confidence_threshold: Umbral para selección de agentes
            enable_multi_agent: Habilitar orquestación multi-agente
        """
        self.agent_registry = agent_registry
        self.selector = AgentSelector(confidence_threshold=confidence_threshold)
        self.workflow_engine = WorkflowEngine(default_timeout=30.0)
        self.enable_multi_agent = enable_multi_agent
        
        self._metrics = {
            'total_orchestrations': 0,
            'single_agent_executions': 0,
            'multi_agent_executions': 0,
            'fallback_executions': 0,
            'successful_orchestrations': 0,
            'failed_orchestrations': 0
        }
        
        logger.info(
            f"AgentOrchestrator initialized "
            f"(threshold={confidence_threshold}, multi_agent={enable_multi_agent})"
        )
    
    async def orchestrate(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        fallback_handler: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Orquesta la ejecución de agentes para una consulta
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
            fallback_handler: Función de fallback si no hay agente apropiado
        
        Returns:
            Diccionario con resultado de la orquestación
        """
        logger.info(f"Orchestrating query: {query[:50]}...")
        start_time = datetime.utcnow()
        
        self._metrics['total_orchestrations'] += 1
        
        try:
            # Obtener agentes disponibles
            available_agents = self.agent_registry.get_all_agents()
            
            if not available_agents:
                logger.warning("No agents available, using fallback")
                return await self._execute_fallback(
                    query, context, fallback_handler, "No agents available"
                )
            
            # Seleccionar agente(s)
            decision = self.selector.select_agent(query, available_agents, context)
            
            # Ejecutar según decisión
            if decision.should_use_fallback:
                result = await self._execute_fallback(
                    query, context, fallback_handler, decision.reasoning
                )
            elif self.enable_multi_agent and self._should_use_multiple_agents(decision):
                result = await self._execute_multi_agent(query, decision, context)
            else:
                result = await self._execute_single_agent(query, decision, context)
            
            # Agregar metadata de orquestación
            result['orchestration'] = {
                'decision': decision.to_dict(),
                'execution_time_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                'multi_agent_used': self.enable_multi_agent and not decision.should_use_fallback
            }
            
            self._metrics['successful_orchestrations'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error in orchestration: {e}")
            self._metrics['failed_orchestrations'] += 1
            
            # Intentar fallback en caso de error
            if fallback_handler:
                return await self._execute_fallback(
                    query, context, fallback_handler, f"Error: {str(e)}"
                )
            
            raise
    
    async def _execute_single_agent(
        self,
        query: str,
        decision: SelectionDecision,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Ejecuta un solo agente
        
        Args:
            query: Consulta del usuario
            decision: Decisión de selección
            context: Contexto adicional
        
        Returns:
            Resultado de la ejecución
        """
        logger.info(f"Executing single agent: {decision.selected_agent.name}")
        self._metrics['single_agent_executions'] += 1
        
        try:
            # Ejecutar agente
            response = await decision.selected_agent.process_query(query, context)
            
            return {
                'answer': response.content,
                'agent_name': response.agent_name,
                'confidence': response.confidence,
                'reasoning': response.reasoning,
                'sources': response.sources,
                'metadata': response.metadata,
                'processing_time_ms': response.processing_time_ms,
                'capabilities_used': [cap.value for cap in response.capabilities_used]
            }
            
        except Exception as e:
            logger.error(f"Error executing agent {decision.selected_agent.name}: {e}")
            raise
    
    async def _execute_multi_agent(
        self,
        query: str,
        decision: SelectionDecision,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Ejecuta múltiples agentes
        
        Args:
            query: Consulta del usuario
            decision: Decisión de selección
            context: Contexto adicional
        
        Returns:
            Resultado sintetizado
        """
        logger.info("Multi-agent execution requested")
        self._metrics['multi_agent_executions'] += 1
        
        # Obtener agentes relevantes (top 2-3 con score > 0.5)
        relevant_agents = self._get_relevant_agents(decision)
        
        if len(relevant_agents) <= 1:
            # Si solo hay un agente relevante, ejecutar single-agent
            logger.info("Only one relevant agent, using single-agent execution")
            return await self._execute_single_agent(query, decision, context)
        
        logger.info(f"Executing {len(relevant_agents)} agents in parallel")
        
        # Ejecutar agentes en paralelo
        responses = await self.workflow_engine.execute_parallel(
            relevant_agents,
            query,
            context
        )
        
        # Sintetizar resultados
        synthesized = self.workflow_engine.synthesize_responses(responses, query)
        
        return synthesized
    
    def _get_relevant_agents(
        self,
        decision: SelectionDecision,
        min_score: float = 0.5,
        max_agents: int = 3
    ) -> List[BaseAgent]:
        """
        Obtiene agentes relevantes para ejecución multi-agente
        
        Args:
            decision: Decisión de selección
            min_score: Score mínimo para considerar un agente
            max_agents: Máximo número de agentes
        
        Returns:
            Lista de agentes relevantes
        """
        # Filtrar agentes por score
        relevant = []
        all_agents = self.agent_registry.get_all_agents()
        
        for agent in all_agents:
            score = decision.all_scores.get(agent.name, 0.0)
            if score >= min_score:
                relevant.append((agent, score))
        
        # Ordenar por score descendente
        relevant.sort(key=lambda x: x[1], reverse=True)
        
        # Tomar top N
        top_agents = [agent for agent, score in relevant[:max_agents]]
        
        logger.debug(f"Selected {len(top_agents)} relevant agents from {len(all_agents)} available")
        
        return top_agents
    
    async def _execute_fallback(
        self,
        query: str,
        context: Optional[Dict[str, Any]],
        fallback_handler: Optional[callable],
        reason: str
    ) -> Dict[str, Any]:
        """
        Ejecuta el fallback a RAG clásico
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
            fallback_handler: Función de fallback
            reason: Razón del fallback
        
        Returns:
            Resultado del fallback
        """
        logger.info(f"Executing fallback: {reason}")
        self._metrics['fallback_executions'] += 1
        
        if fallback_handler is None:
            return {
                'answer': f"No agent available to handle this query. Reason: {reason}",
                'agent_name': 'fallback',
                'confidence': 0.0,
                'reasoning': reason,
                'sources': [],
                'metadata': {'fallback': True, 'reason': reason}
            }
        
        try:
            # Ejecutar fallback handler
            result = fallback_handler(query)
            
            # Asegurar formato consistente
            if isinstance(result, dict):
                result['metadata'] = result.get('metadata', {})
                result['metadata']['fallback'] = True
                result['metadata']['reason'] = reason
                return result
            else:
                return {
                    'answer': str(result),
                    'agent_name': 'fallback',
                    'confidence': 0.0,
                    'reasoning': reason,
                    'sources': [],
                    'metadata': {'fallback': True, 'reason': reason}
                }
                
        except Exception as e:
            logger.error(f"Error in fallback handler: {e}")
            return {
                'answer': f"Error in fallback: {str(e)}",
                'agent_name': 'fallback',
                'confidence': 0.0,
                'reasoning': f"Fallback error: {str(e)}",
                'sources': [],
                'metadata': {'fallback': True, 'error': str(e)}
            }
    
    def _should_use_multiple_agents(self, decision: SelectionDecision) -> bool:
        """
        Determina si se deben usar múltiples agentes
        
        Args:
            decision: Decisión de selección
        
        Returns:
            True si se deben usar múltiples agentes
        """
        # Contar agentes con score > 0.5
        high_score_agents = sum(
            1 for score in decision.all_scores.values() if score >= 0.5
        )
        
        # Usar multi-agente si hay 2+ agentes con score alto
        should_use = high_score_agents >= 2
        
        if should_use:
            logger.info(f"Multi-agent recommended: {high_score_agents} agents with score >= 0.5")
        
        return should_use
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene métricas del orquestador
        
        Returns:
            Diccionario con métricas
        """
        total = self._metrics['total_orchestrations']
        
        metrics = {
            **self._metrics,
            'success_rate': (
                self._metrics['successful_orchestrations'] / total if total > 0 else 0.0
            ),
            'failure_rate': (
                self._metrics['failed_orchestrations'] / total if total > 0 else 0.0
            ),
            'selector_metrics': self.selector.get_metrics(),
            'workflow_metrics': self.workflow_engine.get_metrics()
        }
        
        return metrics
    
    def get_recent_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las decisiones recientes del selector
        
        Args:
            limit: Número de decisiones a retornar
        
        Returns:
            Lista de decisiones
        """
        return self.selector.get_recent_decisions(limit)
