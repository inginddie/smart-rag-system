# -*- coding: utf-8 -*-
"""
Excepciones específicas para el sistema de agentes
Cumple con HU1-CA1.4: Manejo de Errores y Fallbacks
"""

from typing import Optional, Dict, Any

class AgentException(Exception):
    """Excepción base para todos los errores de agentes"""
    
    def __init__(self, message: str, agent_id: str = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.agent_id = agent_id
        self.context = context or {}
        self.timestamp = __import__('time').time()

class AgentInitializationError(AgentException):
    """Error durante la inicialización de un agente"""
    pass

class AgentProcessingError(AgentException):
    """Error durante el procesamiento de una consulta"""
    
    def __init__(self, message: str, agent_id: str = None, query: str = None, context: Dict[str, Any] = None):
        super().__init__(message, agent_id, context)
        self.query = query

class AgentTimeoutError(AgentException):
    """Error por timeout en el procesamiento"""
    
    def __init__(self, message: str, agent_id: str = None, timeout_seconds: float = None, context: Dict[str, Any] = None):
        super().__init__(message, agent_id, context)
        self.timeout_seconds = timeout_seconds

class AgentCapabilityError(AgentException):
    """Error relacionado con capacidades del agente"""
    pass

class AgentMemoryError(AgentException):
    """Error en operaciones de memoria del agente"""
    pass

class AgentToolError(AgentException):
    """Error en el uso de herramientas del agente"""
    
    def __init__(self, message: str, agent_id: str = None, tool_name: str = None, context: Dict[str, Any] = None):
        super().__init__(message, agent_id, context)
        self.tool_name = tool_name

class AgentRegistryError(AgentException):
    """Error en operaciones del registry de agentes"""
    pass

class AgentOrchestrationError(AgentException):
    """Error en la orquestación de múltiples agentes"""
    
    def __init__(self, message: str, agents_involved: list = None, context: Dict[str, Any] = None):
        super().__init__(message, context=context)
        self.agents_involved = agents_involved or []

class AgentCircuitBreakerError(AgentException):
    """Error cuando el circuit breaker está abierto"""
    
    def __init__(self, message: str, agent_id: str = None, failure_count: int = None, context: Dict[str, Any] = None):
        super().__init__(message, agent_id, context)
        self.failure_count = failure_count