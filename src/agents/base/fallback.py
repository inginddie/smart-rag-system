# -*- coding: utf-8 -*-
"""
Sistema de Fallback para Agentes
Cumple con HU1-CA1.4: Fallback automático a RAG clásico
"""

import time
import asyncio
from typing import Dict, Any, Optional, Callable
from collections import defaultdict
from src.agents.base.agent import BaseAgent, AgentResponse, AgentCapability
from src.agents.base.exceptions import (
    AgentException, AgentTimeoutError, AgentCircuitBreakerError
)
try:
    from src.utils.logger import setup_logger
    logger = setup_logger()
except (ImportError, TypeError):
    import logging
    logger = logging.getLogger("agent.fallback")

class CircuitBreaker:
    """
    Circuit Breaker para agentes problemáticos
    Previene cascadas de fallos y permite recuperación automática
    """
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = AgentException):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Verifica si se puede ejecutar la operación"""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            if self.last_failure_time is not None and time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker moving to HALF_OPEN state")
                return True
            return False
        
        # HALF_OPEN state
        return True
    
    def record_success(self):
        """Registra una ejecución exitosa"""
        self.failure_count = 0
        self.state = "CLOSED"
        logger.debug("Circuit breaker reset to CLOSED state")
    
    def record_failure(self):
        """Registra una falla"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")

class RetryManager:
    """
    Gestor de reintentos con backoff exponencial
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs):
        """Ejecuta función con reintentos y backoff exponencial"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    break
                
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
        
        raise last_exception

class AgentFallbackManager:
    """
    Gestor de fallbacks para agentes
    Maneja errores, circuit breakers y fallback a RAG clásico
    """
    
    def __init__(self, rag_service=None):
        self.rag_service = rag_service
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_manager = RetryManager()
        
        # Estadísticas de fallback
        self.fallback_stats = {
            "total_fallbacks": 0,
            "fallbacks_by_agent": defaultdict(int),
            "fallbacks_by_error_type": defaultdict(int),
            "circuit_breaker_activations": 0
        }
        
        logger.info("AgentFallbackManager initialized")
    
    def get_circuit_breaker(self, agent_id: str) -> CircuitBreaker:
        """Obtiene o crea circuit breaker para un agente"""
        if agent_id not in self.circuit_breakers:
            self.circuit_breakers[agent_id] = CircuitBreaker()
        return self.circuit_breakers[agent_id]
    
    async def execute_with_fallback(self, 
                                   agent: BaseAgent, 
                                   query: str, 
                                   context: Dict[str, Any] = None,
                                   timeout_seconds: float = 30.0) -> AgentResponse:
        """
        Ejecuta consulta en agente con manejo completo de errores y fallback
        
        Cumple con HU1-CA1.4: Fallback automático a RAG clásico
        """
        circuit_breaker = self.get_circuit_breaker(agent.agent_id)
        
        # Verificar circuit breaker
        if not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker OPEN for agent {agent.name}, using fallback")
            self.fallback_stats["circuit_breaker_activations"] += 1
            return await self._fallback_to_classic_rag(query, context, 
                                                     reason="circuit_breaker_open",
                                                     agent_name=agent.name)
        
        try:
            # Ejecutar con timeout
            response = await asyncio.wait_for(
                self._execute_agent_with_retry(agent, query, context),
                timeout=timeout_seconds
            )
            
            # Registrar éxito en circuit breaker
            circuit_breaker.record_success()
            
            return response
            
        except asyncio.TimeoutError:
            error_msg = f"Agent {agent.name} timed out after {timeout_seconds}s"
            logger.error(error_msg, extra={
                "agent_id": agent.agent_id,
                "timeout_seconds": timeout_seconds,
                "query_preview": query[:100]
            })
            
            circuit_breaker.record_failure()
            agent._record_failure(error_msg)
            
            self.fallback_stats["fallbacks_by_error_type"]["timeout"] += 1
            
            return await self._fallback_to_classic_rag(query, context,
                                                     reason="timeout",
                                                     agent_name=agent.name,
                                                     error=error_msg)
        
        except AgentException as e:
            logger.error(f"Agent error in {agent.name}: {e}", extra={
                "agent_id": agent.agent_id,
                "error_type": type(e).__name__,
                "query_preview": query[:100]
            })
            
            circuit_breaker.record_failure()
            agent._record_failure(str(e))
            
            self.fallback_stats["fallbacks_by_error_type"][type(e).__name__] += 1
            
            return await self._fallback_to_classic_rag(query, context,
                                                     reason="agent_error",
                                                     agent_name=agent.name,
                                                     error=str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error in {agent.name}: {e}", extra={
                "agent_id": agent.agent_id,
                "error_type": type(e).__name__,
                "query_preview": query[:100]
            })
            
            circuit_breaker.record_failure()
            agent._record_failure(str(e))
            
            self.fallback_stats["fallbacks_by_error_type"]["unexpected"] += 1
            
            return await self._fallback_to_classic_rag(query, context,
                                                     reason="unexpected_error",
                                                     agent_name=agent.name,
                                                     error=str(e))
    
    async def _execute_agent_with_retry(self, 
                                       agent: BaseAgent, 
                                       query: str, 
                                       context: Dict[str, Any] = None) -> AgentResponse:
        """Ejecuta agente con sistema de reintentos"""
        return await self.retry_manager.execute_with_retry(
            agent.process_query, query, context
        )
    
    async def _fallback_to_classic_rag(self, 
                                      query: str, 
                                      context: Dict[str, Any] = None,
                                      reason: str = "unknown",
                                      agent_name: str = "unknown",
                                      error: str = None) -> AgentResponse:
        """
        Fallback a RAG clásico cuando los agentes fallan
        
        Cumple con HU1-CA1.4: Hacer fallback al RAG clásico automáticamente
        """
        self.fallback_stats["total_fallbacks"] += 1
        self.fallback_stats["fallbacks_by_agent"][agent_name] += 1
        
        logger.info(f"Falling back to classic RAG", extra={
            "reason": reason,
            "failed_agent": agent_name,
            "error": error,
            "query_preview": query[:100]
        })
        
        try:
            if self.rag_service:
                # Usar RAG service existente
                result = self.rag_service.query(query, include_sources=True)
                
                # Convertir a formato AgentResponse
                return AgentResponse(
                    agent_id="classic_rag_fallback",
                    agent_name="ClassicRAGFallback",
                    content=result.get("answer", "No se pudo generar respuesta."),
                    confidence=0.7,  # Confidence moderada para fallback
                    reasoning=f"Fallback to classic RAG due to: {reason}",
                    sources=result.get("sources", []),
                    metadata={
                        "fallback_reason": reason,
                        "failed_agent": agent_name,
                        "fallback_error": error,
                        "is_fallback": True,
                        "query_type": "fallback",
                        "processing_strategy": "classic_rag",
                        "source_count": len(result.get("sources", []))
                    },
                    processing_time_ms=0.0,  # No medimos tiempo de fallback
                    capabilities_used=[AgentCapability.DOCUMENT_SEARCH]
                )
            else:
                # Respuesta de emergencia si no hay RAG service
                return AgentResponse(
                    agent_id="emergency_fallback",
                    agent_name="EmergencyFallback",
                    content=f"Lo siento, no pude procesar tu consulta debido a un error técnico. Razón: {reason}",
                    confidence=0.1,
                    reasoning=f"Emergency fallback - no RAG service available",
                    sources=[],
                    metadata={
                        "fallback_reason": reason,
                        "failed_agent": agent_name,
                        "is_emergency_fallback": True,
                        "query_type": "emergency",
                        "processing_strategy": "emergency",
                        "source_count": 0
                    },
                    processing_time_ms=0.0,
                    capabilities_used=[]
                )
                
        except Exception as fallback_error:
            logger.error(f"Fallback to classic RAG also failed: {fallback_error}")
            
            # Respuesta de último recurso
            return AgentResponse(
                agent_id="last_resort_fallback",
                agent_name="LastResortFallback",
                content="Lo siento, el sistema está experimentando dificultades técnicas. Por favor, inténtalo de nuevo más tarde.",
                confidence=0.0,
                reasoning=f"Last resort fallback - all systems failed",
                sources=[],
                metadata={
                    "fallback_reason": reason,
                    "failed_agent": agent_name,
                    "fallback_error": str(fallback_error),
                    "is_last_resort": True,
                    "query_type": "last_resort",
                    "processing_strategy": "last_resort",
                    "source_count": 0
                },
                processing_time_ms=0.0,
                capabilities_used=[]
            )
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de fallbacks"""
        circuit_breaker_stats = {}
        for agent_id, cb in self.circuit_breakers.items():
            circuit_breaker_stats[agent_id] = {
                "state": cb.state,
                "failure_count": cb.failure_count,
                "last_failure_time": cb.last_failure_time
            }
        
        return {
            **self.fallback_stats,
            "circuit_breakers": circuit_breaker_stats,
            "active_circuit_breakers": sum(1 for cb in self.circuit_breakers.values() if cb.state != "CLOSED")
        }
    
    def reset_circuit_breaker(self, agent_id: str) -> bool:
        """Resetea manualmente un circuit breaker"""
        if agent_id in self.circuit_breakers:
            self.circuit_breakers[agent_id].record_success()
            logger.info(f"Circuit breaker reset for agent {agent_id}")
            return True
        return False
    
    def reset_all_circuit_breakers(self):
        """Resetea todos los circuit breakers"""
        for agent_id in self.circuit_breakers:
            self.circuit_breakers[agent_id].record_success()
        logger.info("All circuit breakers reset")

# Instancia global del fallback manager
fallback_manager = AgentFallbackManager()