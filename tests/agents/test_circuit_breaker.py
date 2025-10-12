#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para CircuitBreaker
"""

import pytest
import time

from src.agents.orchestration.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError
)


class TestCircuitBreaker:
    """Tests para CircuitBreaker"""
    
    @pytest.fixture
    def config(self):
        return CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=1.0,
            slow_call_threshold=0.5
        )
    
    @pytest.fixture
    def breaker(self, config):
        return CircuitBreaker("TestAgent", config)
    
    def test_initialization(self, breaker):
        """Test: Inicialización correcta"""
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0
    
    def test_successful_call(self, breaker):
        """Test: Llamada exitosa"""
        def success_func():
            return "success"
        
        result = breaker.call(success_func)
        
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker._metrics['successful_calls'] == 1
    
    def test_failed_call(self, breaker):
        """Test: Llamada fallida"""
        def fail_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            breaker.call(fail_func)
        
        assert breaker.failure_count == 1
        assert breaker._metrics['failed_calls'] == 1
    
    def test_opens_after_threshold(self, breaker):
        """Test: Se abre después del threshold de fallos"""
        def fail_func():
            raise ValueError("Test error")
        
        # Fallar 3 veces (threshold)
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(fail_func)
        
        # Debe estar abierto
        assert breaker.state == CircuitState.OPEN
    
    def test_rejects_when_open(self, breaker):
        """Test: Rechaza llamadas cuando está abierto"""
        # Abrir el circuit
        def fail_func():
            raise ValueError("Test error")
        
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(fail_func)
        
        # Intentar llamada - debe rechazar
        def success_func():
            return "success"
        
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(success_func)
        
        assert breaker._metrics['rejected_calls'] == 1
    
    def test_half_open_after_timeout(self, breaker):
        """Test: Transición a HALF_OPEN después del timeout"""
        # Abrir el circuit
        def fail_func():
            raise ValueError("Test error")
        
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Esperar timeout
        time.sleep(1.1)
        
        # Intentar llamada - debe pasar a HALF_OPEN
        def success_func():
            return "success"
        
        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.HALF_OPEN
    
    def test_closes_from_half_open(self, breaker):
        """Test: Cierra desde HALF_OPEN después de éxitos"""
        # Abrir y pasar a HALF_OPEN
        breaker.state = CircuitState.HALF_OPEN
        
        def success_func():
            return "success"
        
        # 2 éxitos (threshold)
        breaker.call(success_func)
        breaker.call(success_func)
        
        # Debe estar cerrado
        assert breaker.state == CircuitState.CLOSED
    
    def test_slow_call_detection(self, breaker):
        """Test: Detección de llamadas lentas"""
        def slow_func():
            time.sleep(0.6)  # Más que slow_call_threshold (0.5)
            return "slow"
        
        result = breaker.call(slow_func)
        
        assert result == "slow"
        assert breaker._metrics['slow_calls'] == 1
    
    def test_manual_reset(self, breaker):
        """Test: Reset manual"""
        # Abrir el circuit
        def fail_func():
            raise ValueError("Test error")
        
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(fail_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Reset manual
        breaker.reset()
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_get_metrics(self, breaker):
        """Test: Obtener métricas"""
        def success_func():
            return "success"
        
        breaker.call(success_func)
        
        metrics = breaker.get_metrics()
        
        assert 'total_calls' in metrics
        assert 'successful_calls' in metrics
        assert 'state' in metrics
        assert metrics['state'] == 'closed'


class TestCircuitBreakerManager:
    """Tests para CircuitBreakerManager"""
    
    @pytest.fixture
    def manager(self):
        return CircuitBreakerManager()
    
    def test_initialization(self, manager):
        """Test: Inicialización correcta"""
        assert manager.default_config is not None
        assert len(manager._breakers) == 0
    
    def test_get_breaker(self, manager):
        """Test: Obtener o crear breaker"""
        breaker1 = manager.get_breaker("Agent1")
        breaker2 = manager.get_breaker("Agent1")
        
        # Debe retornar el mismo breaker
        assert breaker1 is breaker2
        assert breaker1.name == "Agent1"
    
    def test_multiple_breakers(self, manager):
        """Test: Múltiples breakers"""
        breaker1 = manager.get_breaker("Agent1")
        breaker2 = manager.get_breaker("Agent2")
        
        assert breaker1 is not breaker2
        assert len(manager._breakers) == 2
    
    def test_get_all_metrics(self, manager):
        """Test: Obtener métricas de todos"""
        manager.get_breaker("Agent1")
        manager.get_breaker("Agent2")
        
        metrics = manager.get_all_metrics()
        
        assert "Agent1" in metrics
        assert "Agent2" in metrics
    
    def test_reset_all(self, manager):
        """Test: Reset de todos los breakers"""
        breaker1 = manager.get_breaker("Agent1")
        breaker2 = manager.get_breaker("Agent2")
        
        # Abrir ambos
        breaker1.state = CircuitState.OPEN
        breaker2.state = CircuitState.OPEN
        
        # Reset all
        manager.reset_all()
        
        assert breaker1.state == CircuitState.CLOSED
        assert breaker2.state == CircuitState.CLOSED
    
    def test_get_healthy_agents(self, manager):
        """Test: Obtener agentes saludables"""
        breaker1 = manager.get_breaker("Agent1")
        breaker2 = manager.get_breaker("Agent2")
        breaker3 = manager.get_breaker("Agent3")
        
        # Abrir uno
        breaker2.state = CircuitState.OPEN
        
        healthy = manager.get_healthy_agents()
        
        assert "Agent1" in healthy
        assert "Agent2" not in healthy
        assert "Agent3" in healthy


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
