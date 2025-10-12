#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorkflowEngine - Motor de ejecución de workflows multi-agente
Implementa CA5.2: Orquestación Multi-Agente
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import asyncio
import time
from datetime import datetime
from enum import Enum

from src.agents.base.agent import BaseAgent, AgentResponse
from src.agents.orchestration.circuit_breaker import (
    CircuitBreakerManager,
    CircuitBreakerOpenError,
    CircuitState
)
from src.agents.orchestration.load_balancer import LoadBalancer, LoadBalancingStrategy
from src.agents.orchestration.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Modos de ejecución de agentes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class WorkflowStep:
    """Paso individual en un workflow"""
    
    def __init__(
        self,
        agent: BaseAgent,
        query: str,
        depends_on: Optional[List[str]] = None,
        timeout: float = 30.0
    ):
        self.agent = agent
        self.query = query
        self.depends_on = depends_on or []
        self.timeout = timeout
        self.result: Optional[AgentResponse] = None
        self.error: Optional[str] = None
        self.completed = False


class WorkflowEngine:
    """
    Motor de ejecución de workflows multi-agente
    
    Responsabilidades:
    - Ejecutar agentes en secuencia o paralelo
    - Gestionar dependencias entre agentes
    - Sintetizar resultados de múltiples agentes
    - Manejar timeouts y errores
    """
    
    def __init__(self, default_timeout: float = 30.0, enable_circuit_breaker: bool = True):
        """
        Inicializa el workflow engine
        
        Args:
            default_timeout: Timeout por defecto para cada agente (segundos)
            enable_circuit_breaker: Habilitar circuit breakers
        """
        self.default_timeout = default_timeout
        self.enable_circuit_breaker = enable_circuit_breaker
        self.circuit_breaker_manager = CircuitBreakerManager() if enable_circuit_breaker else None
        
        # Componentes de optimización de performance
        self.load_balancer = LoadBalancer(LoadBalancingStrategy.WEIGHTED_RESPONSE_TIME)
        self.performance_monitor = PerformanceMonitor(max_metrics=1000)
        
        self._metrics = {
            'total_workflows': 0,
            'sequential_executions': 0,
            'parallel_executions': 0,
            'successful_workflows': 0,
            'failed_workflows': 0,
            'avg_execution_time_ms': 0.0,
            'circuit_breaker_rejections': 0
        }
        
        self._latency_metrics = {
            'min_latency_ms': float('inf'),
            'max_latency_ms': 0.0,
            'p50_latency_ms': 0.0,
            'p95_latency_ms': 0.0,
            'p99_latency_ms': 0.0
        }
        
        self._latency_samples = []
        
        logger.info(f"WorkflowEngine initialized with performance optimization (timeout={default_timeout}s, circuit_breaker={enable_circuit_breaker})")
    
    async def execute_sequential(
        self,
        agents: List[BaseAgent],
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[AgentResponse]:
        """
        Ejecuta agentes secuencialmente
        
        Args:
            agents: Lista de agentes a ejecutar
            query: Query original
            context: Contexto adicional
        
        Returns:
            Lista de respuestas de agentes
        """
        logger.info(f"Executing {len(agents)} agents sequentially")
        self._metrics['sequential_executions'] += 1
        
        responses = []
        accumulated_context = context or {}
        
        for i, agent in enumerate(agents, 1):
            try:
                logger.debug(f"Executing agent {i}/{len(agents)}: {agent.name}")
                
                # Ejecutar con timeout
                response = await asyncio.wait_for(
                    agent.process_query(query, accumulated_context),
                    timeout=self.default_timeout
                )
                
                responses.append(response)
                
                # Actualizar contexto para siguiente agente
                accumulated_context['previous_responses'] = responses
                
                logger.debug(f"Agent {agent.name} completed successfully")
                
            except asyncio.TimeoutError:
                logger.warning(f"Agent {agent.name} timed out after {self.default_timeout}s")
                # Continuar con siguiente agente
                
            except Exception as e:
                logger.error(f"Error executing agent {agent.name}: {e}")
                # Continuar con siguiente agente
        
        return responses
    
    async def execute_parallel(
        self,
        agents: List[BaseAgent],
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[AgentResponse]:
        """
        Ejecuta agentes en paralelo
        
        Args:
            agents: Lista de agentes a ejecutar
            query: Query original
            context: Contexto adicional
        
        Returns:
            Lista de respuestas de agentes
        """
        logger.info(f"Executing {len(agents)} agents in parallel")
        self._metrics['parallel_executions'] += 1
        
        # Crear tareas para todos los agentes
        tasks = []
        for agent in agents:
            task = asyncio.create_task(
                self._execute_agent_with_timeout(agent, query, context)
            )
            tasks.append(task)
        
        # Esperar a que todas completen
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar resultados exitosos
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, AgentResponse):
                responses.append(result)
                logger.debug(f"Agent {agents[i].name} completed successfully")
            elif isinstance(result, Exception):
                logger.error(f"Agent {agents[i].name} failed: {result}")
            else:
                logger.warning(f"Agent {agents[i].name} returned unexpected result")
        
        return responses
    
    async def _execute_agent_with_timeout(
        self,
        agent: BaseAgent,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[AgentResponse]:
        """
        Ejecuta un agente con timeout y circuit breaker
        
        Args:
            agent: Agente a ejecutar
            query: Query
            context: Contexto
        
        Returns:
            Respuesta del agente o None si falla
        """
        start_time = time.time()
        
        try:
            # Verificar circuit breaker
            if self.enable_circuit_breaker:
                breaker = self.circuit_breaker_manager.get_breaker(agent.name)
                
                # Verificar si el circuit está abierto
                if breaker.get_state() == CircuitState.OPEN:
                    if not breaker._should_attempt_reset():
                        logger.warning(f"Agent {agent.name} rejected by circuit breaker")
                        self._metrics['circuit_breaker_rejections'] += 1
                        return None
            
            # Ejecutar agente
            response = await asyncio.wait_for(
                agent.process_query(query, context),
                timeout=self.default_timeout
            )
            
            # Registrar éxito en circuit breaker
            if self.enable_circuit_breaker:
                breaker._on_success()
            
            # Registrar latencia
            latency_ms = (time.time() - start_time) * 1000
            self._record_latency(latency_ms)
            
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Agent {agent.name} timed out")
            if self.enable_circuit_breaker:
                breaker._on_failure()
            return None
        except Exception as e:
            logger.error(f"Agent {agent.name} error: {e}")
            if self.enable_circuit_breaker:
                breaker._on_failure()
            return None
    
    def _record_latency(self, latency_ms: float):
        """
        Registra una muestra de latencia
        
        Args:
            latency_ms: Latencia en milisegundos
        """
        self._latency_samples.append(latency_ms)
        
        # Mantener solo las últimas 1000 muestras
        if len(self._latency_samples) > 1000:
            self._latency_samples = self._latency_samples[-1000:]
        
        # Actualizar métricas
        self._latency_metrics['min_latency_ms'] = min(self._latency_samples)
        self._latency_metrics['max_latency_ms'] = max(self._latency_samples)
        
        # Calcular percentiles
        if len(self._latency_samples) >= 10:
            sorted_samples = sorted(self._latency_samples)
            n = len(sorted_samples)
            self._latency_metrics['p50_latency_ms'] = sorted_samples[int(n * 0.50)]
            self._latency_metrics['p95_latency_ms'] = sorted_samples[int(n * 0.95)]
            self._latency_metrics['p99_latency_ms'] = sorted_samples[int(n * 0.99)]
    
    def synthesize_responses(
        self,
        responses: List[AgentResponse],
        query: str
    ) -> Dict[str, Any]:
        """
        Sintetiza respuestas de múltiples agentes
        
        Args:
            responses: Lista de respuestas de agentes
            query: Query original
        
        Returns:
            Respuesta sintetizada
        """
        if not responses:
            return {
                'answer': "No responses from agents",
                'agent_name': 'multi-agent',
                'confidence': 0.0,
                'reasoning': "No agents provided responses",
                'sources': [],
                'metadata': {'agent_count': 0}
            }
        
        # Si solo hay una respuesta, retornarla directamente
        if len(responses) == 1:
            response = responses[0]
            return {
                'answer': response.content,
                'agent_name': response.agent_name,
                'confidence': response.confidence,
                'reasoning': response.reasoning,
                'sources': response.sources,
                'metadata': {
                    **response.metadata,
                    'agent_count': 1
                }
            }
        
        # Múltiples respuestas - sintetizar
        logger.info(f"Synthesizing {len(responses)} agent responses")
        
        # Combinar contenidos
        combined_content = self._combine_contents(responses)
        
        # Combinar fuentes
        all_sources = []
        for response in responses:
            all_sources.extend(response.sources)
        
        # Calcular confidence promedio ponderado
        total_confidence = sum(r.confidence for r in responses)
        avg_confidence = total_confidence / len(responses)
        
        # Crear reasoning combinado
        agent_names = [r.agent_name for r in responses]
        reasoning = f"Synthesized from {len(responses)} agents: {', '.join(agent_names)}"
        
        return {
            'answer': combined_content,
            'agent_name': 'multi-agent',
            'confidence': avg_confidence,
            'reasoning': reasoning,
            'sources': all_sources,
            'metadata': {
                'agent_count': len(responses),
                'agents_used': agent_names,
                'individual_confidences': [r.confidence for r in responses]
            }
        }
    
    def _combine_contents(self, responses: List[AgentResponse]) -> str:
        """
        Combina contenidos de múltiples respuestas
        
        Args:
            responses: Lista de respuestas
        
        Returns:
            Contenido combinado
        """
        # Estrategia simple: concatenar con separadores
        sections = []
        
        for i, response in enumerate(responses, 1):
            section = f"### Análisis {i} ({response.agent_name})\n\n{response.content}"
            sections.append(section)
        
        combined = "\n\n---\n\n".join(sections)
        
        # Agregar resumen si hay múltiples respuestas
        if len(responses) > 1:
            summary = (
                f"\n\n### Resumen\n\n"
                f"Esta respuesta combina análisis de {len(responses)} agentes especializados "
                f"para proporcionar una perspectiva comprehensiva."
            )
            combined = combined + summary
        
        return combined
    
    def detect_multi_agent_query(self, query: str) -> Tuple[bool, List[str]]:
        """
        Detecta si una query requiere múltiples agentes
        
        Args:
            query: Query del usuario
        
        Returns:
            Tupla (requiere_multi_agente, razones)
        """
        reasons = []
        
        # Patrones que sugieren múltiples agentes
        multi_agent_patterns = [
            ("compare", "Comparison requires multiple perspectives"),
            ("analyze and synthesize", "Analysis and synthesis are separate tasks"),
            ("both", "Multiple aspects mentioned"),
            ("as well as", "Multiple requirements"),
            ("in addition", "Additional requirements"),
        ]
        
        query_lower = query.lower()
        
        for pattern, reason in multi_agent_patterns:
            if pattern in query_lower:
                reasons.append(reason)
        
        # Detectar múltiples preguntas
        if "?" in query and query.count("?") > 1:
            reasons.append("Multiple questions detected")
        
        # Detectar listas
        if any(marker in query_lower for marker in ["1.", "2.", "first", "second", "also"]):
            reasons.append("Multiple items or steps mentioned")
        
        requires_multi = len(reasons) > 0
        
        return requires_multi, reasons
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene métricas completas del workflow engine
        
        Returns:
            Diccionario con métricas
        """
        metrics = {
            **self._metrics,
            'latency': self._latency_metrics,
            'default_timeout': self.default_timeout,
            'circuit_breaker_enabled': self.enable_circuit_breaker
        }
        
        # Agregar métricas de circuit breakers
        if self.enable_circuit_breaker and self.circuit_breaker_manager:
            metrics['circuit_breakers'] = self.circuit_breaker_manager.get_all_metrics()
        
        # Agregar métricas de performance
        metrics['performance_metrics'] = self.performance_monitor.get_global_metrics()
        metrics['load_balancer_metrics'] = self.load_balancer.get_metrics()
        
        return metrics
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Genera reporte completo de performance
        
        Returns:
            Reporte detallado de performance
        """
        return {
            'workflow_metrics': self._metrics,
            'performance_report': self.performance_monitor.generate_performance_report(),
            'circuit_breaker_status': self.circuit_breaker_manager.get_all_metrics() if self.circuit_breaker_manager else {},
            'load_balancer_stats': self.load_balancer.get_all_stats(),
            'slow_agents': self.performance_monitor.get_slow_agents(),
            'failing_agents': self.performance_monitor.get_failing_agents()
        }
