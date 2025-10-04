# -*- coding: utf-8 -*-
"""
Base Agent Module - Arquitectura fundamental de agentes
"""

# Importaciones lazy para evitar problemas circulares
__all__ = [
    # Core classes
    "BaseAgent",
    "AgentResponse", 
    "AgentStats",
    "AgentCapability",
    "AgentStatus",
    "AgentMessage",
    
    # Registry
    "AgentRegistry",
    "agent_registry",
    
    # Exceptions
    "AgentException",
    "AgentInitializationError",
    "AgentProcessingError",
    "AgentTimeoutError",
    "AgentCapabilityError",
    "AgentMemoryError",
    "AgentToolError",
    "AgentRegistryError",
    "AgentOrchestrationError",
    "AgentCircuitBreakerError",
    
    # Fallback system
    "CircuitBreaker",
    "RetryManager",
    "AgentFallbackManager",
    "fallback_manager"
]