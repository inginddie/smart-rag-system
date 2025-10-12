#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CircuitBreaker - Protección contra agentes lentos o fallidos
Implementa CA5.3: Optimización de Performance
"""

from typing import Dict, Optional
import logging
import time
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuración del circuit breaker"""
    failure_threshold: int = 5  # Fallos antes de abrir
    success_threshold: int = 2  # Éxitos para cerrar desde half-open
    timeout: float = 60.0  # Segundos antes de intentar half-open
    slow_call_threshold: float = 10.0  # Segundos para considerar "lento"


class CircuitBreaker:
    """
    Circuit Breaker para proteger contra agentes lentos o fallidos
    
    Patrón:
    - CLOSED: Operación normal, cuenta fallos
    - OPEN: Rechaza requests, espera timeout
    - HALF_OPEN: Permite requests de prueba
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Inicializa el circuit breaker
        
        Args:
            name: Nombre del circuit breaker (típicamente nombre del agente)
            config: Configuración del circuit breaker
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change: float = time.time()
        
        self._metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'rejected_calls': 0,
            'slow_calls': 0,
            'state_changes': 0
        }
        
        logger.info(f"CircuitBreaker '{name}' initialized in CLOSED state")
    
    def call(self, func, *args, **kwargs):
        """
        Ejecuta una función protegida por el circuit breaker
        
        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
        
        Returns:
            Resultado de la función
        
        Raises:
            CircuitBreakerOpenError: Si el circuit está abierto
        """
        self._metrics['total_calls'] += 1
        
        # Verificar estado
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                self._metrics['rejected_calls'] += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN"
                )
        
        # Ejecutar función
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Verificar si fue lento
            if execution_time > self.config.slow_call_threshold:
                self._metrics['slow_calls'] += 1
                logger.warning(
                    f"Slow call detected for '{self.name}': {execution_time:.2f}s"
                )
            
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Maneja una llamada exitosa"""
        self._metrics['successful_calls'] += 1
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
    
    def _on_failure(self):
        """Maneja una llamada fallida"""
        self._metrics['failed_calls'] += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()
        elif self.failure_count >= self.config.failure_threshold:
            self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Verifica si debe intentar reset desde OPEN"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.timeout
    
    def _transition_to_open(self):
        """Transición a estado OPEN"""
        if self.state != CircuitState.OPEN:
            logger.warning(f"Circuit breaker '{self.name}' transitioning to OPEN")
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
            self._metrics['state_changes'] += 1
    
    def _transition_to_half_open(self):
        """Transición a estado HALF_OPEN"""
        logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = time.time()
        self._metrics['state_changes'] += 1
    
    def _transition_to_closed(self):
        """Transición a estado CLOSED"""
        logger.info(f"Circuit breaker '{self.name}' transitioning to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()
        self._metrics['state_changes'] += 1
    
    def reset(self):
        """Reset manual del circuit breaker"""
        logger.info(f"Circuit breaker '{self.name}' manually reset")
        self._transition_to_closed()
    
    def get_state(self) -> CircuitState:
        """Obtiene el estado actual"""
        return self.state
    
    def get_metrics(self) -> Dict:
        """Obtiene métricas del circuit breaker"""
        return {
            **self._metrics,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'time_in_current_state': time.time() - self.last_state_change
        }


class CircuitBreakerOpenError(Exception):
    """Excepción cuando el circuit breaker está abierto"""
    pass


class CircuitBreakerManager:
    """
    Gestor de circuit breakers para múltiples agentes
    """
    
    def __init__(self, default_config: Optional[CircuitBreakerConfig] = None):
        """
        Inicializa el gestor
        
        Args:
            default_config: Configuración por defecto para nuevos breakers
        """
        self.default_config = default_config or CircuitBreakerConfig()
        self._breakers: Dict[str, CircuitBreaker] = {}
        
        logger.info("CircuitBreakerManager initialized")
    
    def get_breaker(self, agent_name: str) -> CircuitBreaker:
        """
        Obtiene o crea un circuit breaker para un agente
        
        Args:
            agent_name: Nombre del agente
        
        Returns:
            CircuitBreaker para el agente
        """
        if agent_name not in self._breakers:
            self._breakers[agent_name] = CircuitBreaker(
                agent_name,
                self.default_config
            )
        
        return self._breakers[agent_name]
    
    def get_all_metrics(self) -> Dict[str, Dict]:
        """
        Obtiene métricas de todos los circuit breakers
        
        Returns:
            Diccionario con métricas por agente
        """
        return {
            name: breaker.get_metrics()
            for name, breaker in self._breakers.items()
        }
    
    def reset_all(self):
        """Reset de todos los circuit breakers"""
        for breaker in self._breakers.values():
            breaker.reset()
        logger.info("All circuit breakers reset")
    
    def get_healthy_agents(self) -> list:
        """
        Obtiene lista de agentes con circuit breaker cerrado
        
        Returns:
            Lista de nombres de agentes saludables
        """
        return [
            name for name, breaker in self._breakers.items()
            if breaker.get_state() == CircuitState.CLOSED
        ]
