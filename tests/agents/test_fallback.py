# -*- coding: utf-8 -*-
"""
Tests unitarios para sistema de fallback
Cumple con Tarea 1.4: Tests para manejo de errores y fallbacks
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from src.agents.base.agent import BaseAgent, AgentResponse, AgentCapability
from src.agents.base.exceptions import AgentException, AgentTimeoutError
from src.agents.base.fallback import (
    CircuitBreaker, RetryManager, AgentFallbackManager
)

class MockAgent(BaseAgent):
    """Agente mock para testing"""
    
    def __init__(self, name, should_fail=False, should_timeout=False):
        super().__init__(name, f"Mock {name}")
        self.should_fail = should_fail
        self.should_timeout = should_timeout
        self.call_count = 0
    
    def get_capabilities(self):
        return [AgentCapability.DOCUMENT_SEARCH]
    
    async def process_query(self, query, context=None):
        self.call_count += 1
        
        if self.should_timeout:
            await asyncio.sleep(2)  # Simular timeout
        
        if self.should_fail:
            raise AgentException(f"Mock error from {self.name}", self.agent_id)
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name=self.name,
            content=f"Mock response from {self.name}",
            confidence=0.8,
            reasoning="Mock reasoning",
            sources=[],
            metadata={"query_type": "mock", "processing_strategy": "mock", "source_count": 0},
            processing_time_ms=100.0,
            capabilities_used=[AgentCapability.DOCUMENT_SEARCH]
        )

class TestCircuitBreaker:
    """Tests para CircuitBreaker"""
    
    def test_circuit_breaker_initialization(self):
        """Test inicialización del circuit breaker"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"
        assert cb.last_failure_time is None
    
    def test_circuit_breaker_closed_state(self):
        """Test estado CLOSED del circuit breaker"""
        cb = CircuitBreaker()
        
        assert cb.can_execute() is True
        assert cb.state == "CLOSED"
    
    def test_circuit_breaker_record_success(self):
        """Test registro de éxito"""
        cb = CircuitBreaker()
        cb.failure_count = 2
        cb.state = "HALF_OPEN"
        
        cb.record_success()
        
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"
    
    def test_circuit_breaker_record_failure(self):
        """Test registro de fallo"""
        cb = CircuitBreaker(failure_threshold=2)
        
        # Primer fallo
        cb.record_failure()
        assert cb.failure_count == 1
        assert cb.state == "CLOSED"
        assert cb.last_failure_time is not None
        
        # Segundo fallo - debe abrir el circuit breaker
        cb.record_failure()
        assert cb.failure_count == 2
        assert cb.state == "OPEN"
    
    def test_circuit_breaker_open_state(self):
        """Test estado OPEN del circuit breaker"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1)
        
        cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.can_execute() is False
    
    def test_circuit_breaker_recovery(self):
        """Test recuperación automática del circuit breaker"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.can_execute() is False
        
        # Esperar tiempo de recuperación
        time.sleep(0.2)
        
        # Debe pasar a HALF_OPEN
        assert cb.can_execute() is True
        assert cb.state == "HALF_OPEN"

class TestRetryManager:
    """Tests para RetryManager"""
    
    @pytest.mark.asyncio
    async def test_retry_manager_success_first_try(self):
        """Test éxito en primer intento"""
        retry_manager = RetryManager(max_retries=3)
        
        mock_func = AsyncMock(return_value="success")
        
        result = await retry_manager.execute_with_retry(mock_func, "arg1", kwarg1="value1")
        
        assert result == "success"
        assert mock_func.call_count == 1
        mock_func.assert_called_with("arg1", kwarg1="value1")
    
    @pytest.mark.asyncio
    async def test_retry_manager_success_after_retries(self):
        """Test éxito después de varios reintentos"""
        retry_manager = RetryManager(max_retries=3, base_delay=0.01)
        
        mock_func = AsyncMock()
        mock_func.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            "success"  # Éxito en tercer intento
        ]
        
        result = await retry_manager.execute_with_retry(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_manager_max_retries_exceeded(self):
        """Test cuando se exceden los reintentos máximos"""
        retry_manager = RetryManager(max_retries=2, base_delay=0.01)
        
        mock_func = AsyncMock(side_effect=Exception("Persistent error"))
        
        with pytest.raises(Exception, match="Persistent error"):
            await retry_manager.execute_with_retry(mock_func)
        
        assert mock_func.call_count == 3  # 1 intento inicial + 2 reintentos

class TestAgentFallbackManager:
    """Tests para AgentFallbackManager"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.mock_rag_service = Mock()
        self.fallback_manager = AgentFallbackManager(self.mock_rag_service)
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_success(self):
        """Test ejecución exitosa sin fallback"""
        agent = MockAgent("TestAgent")
        
        response = await self.fallback_manager.execute_with_fallback(
            agent, "test query", timeout_seconds=1.0
        )
        
        assert isinstance(response, AgentResponse)
        assert response.agent_name == "TestAgent"
        assert "Mock response" in response.content
        assert agent.call_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_timeout(self):
        """Test fallback por timeout"""
        agent = MockAgent("TestAgent", should_timeout=True)
        
        # Mock RAG service response
        self.mock_rag_service.query.return_value = {
            "answer": "Fallback response",
            "sources": []
        }
        
        response = await self.fallback_manager.execute_with_fallback(
            agent, "test query", timeout_seconds=0.5
        )
        
        # Debe usar fallback
        assert response.agent_name == "ClassicRAGFallback"
        assert "Fallback response" in response.content
        assert response.metadata["is_fallback"] is True
        assert response.metadata["fallback_reason"] == "timeout"
        
        # Verificar estadísticas
        stats = self.fallback_manager.get_fallback_stats()
        assert stats["total_fallbacks"] == 1
        assert stats["fallbacks_by_error_type"]["timeout"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_agent_error(self):
        """Test fallback por error del agente"""
        agent = MockAgent("TestAgent", should_fail=True)
        
        self.mock_rag_service.query.return_value = {
            "answer": "Fallback response",
            "sources": []
        }
        
        response = await self.fallback_manager.execute_with_fallback(
            agent, "test query"
        )
        
        assert response.agent_name == "ClassicRAGFallback"
        assert response.metadata["fallback_reason"] == "agent_error"
        assert "Mock error" in response.metadata["fallback_error"]
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_circuit_breaker_open(self):
        """Test fallback cuando circuit breaker está abierto"""
        agent = MockAgent("TestAgent")
        
        # Abrir circuit breaker manualmente
        cb = self.fallback_manager.get_circuit_breaker(agent.agent_id)
        cb.state = "OPEN"
        
        self.mock_rag_service.query.return_value = {
            "answer": "Fallback response",
            "sources": []
        }
        
        response = await self.fallback_manager.execute_with_fallback(
            agent, "test query"
        )
        
        # No debe llamar al agente
        assert agent.call_count == 0
        assert response.metadata["fallback_reason"] == "circuit_breaker_open"
        
        stats = self.fallback_manager.get_fallback_stats()
        assert stats["circuit_breaker_activations"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_no_rag_service(self):
        """Test fallback cuando no hay RAG service"""
        fallback_manager = AgentFallbackManager(rag_service=None)
        agent = MockAgent("TestAgent", should_fail=True)
        
        response = await fallback_manager.execute_with_fallback(
            agent, "test query"
        )
        
        assert response.agent_name == "EmergencyFallback"
        assert "error técnico" in response.content
        assert response.metadata["is_emergency_fallback"] is True
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_rag_service_fails(self):
        """Test cuando el RAG service también falla"""
        agent = MockAgent("TestAgent", should_fail=True)
        
        # RAG service también falla
        self.mock_rag_service.query.side_effect = Exception("RAG service error")
        
        response = await self.fallback_manager.execute_with_fallback(
            agent, "test query"
        )
        
        assert response.agent_name == "LastResortFallback"
        assert "dificultades técnicas" in response.content
        assert response.metadata["is_last_resort"] is True
    
    def test_circuit_breaker_management(self):
        """Test gestión de circuit breakers"""
        agent = MockAgent("TestAgent")
        
        # Obtener circuit breaker
        cb1 = self.fallback_manager.get_circuit_breaker(agent.agent_id)
        cb2 = self.fallback_manager.get_circuit_breaker(agent.agent_id)
        
        # Debe ser el mismo objeto
        assert cb1 is cb2
        assert cb1.state == "CLOSED"
    
    def test_reset_circuit_breaker(self):
        """Test reset manual de circuit breaker"""
        agent = MockAgent("TestAgent")
        
        # Abrir circuit breaker
        cb = self.fallback_manager.get_circuit_breaker(agent.agent_id)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "OPEN"
        
        # Reset manual
        result = self.fallback_manager.reset_circuit_breaker(agent.agent_id)
        
        assert result is True
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
    
    def test_reset_nonexistent_circuit_breaker(self):
        """Test reset de circuit breaker inexistente"""
        result = self.fallback_manager.reset_circuit_breaker("nonexistent_id")
        assert result is False
    
    def test_reset_all_circuit_breakers(self):
        """Test reset de todos los circuit breakers"""
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        
        # Crear y abrir circuit breakers
        cb1 = self.fallback_manager.get_circuit_breaker(agent1.agent_id)
        cb2 = self.fallback_manager.get_circuit_breaker(agent2.agent_id)
        
        for _ in range(5):
            cb1.record_failure()
            cb2.record_failure()
        
        assert cb1.state == "OPEN"
        assert cb2.state == "OPEN"
        
        # Reset todos
        self.fallback_manager.reset_all_circuit_breakers()
        
        assert cb1.state == "CLOSED"
        assert cb2.state == "CLOSED"
    
    def test_get_fallback_stats(self):
        """Test obtención de estadísticas de fallback"""
        agent = MockAgent("TestAgent")
        
        # Crear circuit breaker y simular fallo
        cb = self.fallback_manager.get_circuit_breaker(agent.agent_id)
        cb.record_failure()
        
        # Simular estadísticas de fallback
        self.fallback_manager.fallback_stats["total_fallbacks"] = 5
        self.fallback_manager.fallback_stats["fallbacks_by_agent"]["TestAgent"] = 3
        
        stats = self.fallback_manager.get_fallback_stats()
        
        assert stats["total_fallbacks"] == 5
        assert stats["fallbacks_by_agent"]["TestAgent"] == 3
        assert "circuit_breakers" in stats
        assert agent.agent_id in stats["circuit_breakers"]
        assert stats["circuit_breakers"][agent.agent_id]["failure_count"] == 1
        assert stats["active_circuit_breakers"] == 0  # No está abierto

if __name__ == "__main__":
    pytest.main([__file__])