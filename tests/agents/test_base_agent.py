# -*- coding: utf-8 -*-
"""
Tests unitarios para BaseAgent y estructuras fundamentales
Cumple con Tarea 1.4: Tests unitarios para arquitectura base
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock
from src.agents.base.agent import (
    BaseAgent, AgentResponse, AgentStats, AgentCapability, 
    AgentStatus, AgentMessage
)
from src.agents.base.exceptions import AgentException

class TestAgent(BaseAgent):
    """Agente de prueba para testing"""
    
    def __init__(self, name: str, description: str):
        self._capabilities = [AgentCapability.DOCUMENT_SEARCH, AgentCapability.SYNTHESIS]
        super().__init__(name, description)
    
    def get_capabilities(self):
        return self._capabilities
    
    async def process_query(self, query: str, context=None):
        if query == "error":
            raise AgentException("Test error", self.agent_id)
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name=self.name,
            content=f"Test response for: {query}",
            confidence=0.8,
            reasoning="Test reasoning",
            sources=[{"test": "source"}],
            metadata={"query_type": "test", "processing_strategy": "test", "source_count": 1},
            processing_time_ms=100.0,
            capabilities_used=[AgentCapability.DOCUMENT_SEARCH]
        )

class TestAgentResponse:
    """Tests para AgentResponse dataclass"""
    
    def test_agent_response_creation(self):
        """Test creación básica de AgentResponse"""
        response = AgentResponse(
            agent_id="test_id",
            agent_name="TestAgent",
            content="Test content",
            confidence=0.8,
            reasoning="Test reasoning",
            sources=[],
            metadata={"query_type": "test", "processing_strategy": "test", "source_count": 0},
            processing_time_ms=100.0,
            capabilities_used=[AgentCapability.DOCUMENT_SEARCH]
        )
        
        assert response.agent_id == "test_id"
        assert response.agent_name == "TestAgent"
        assert response.content == "Test content"
        assert response.confidence == 0.8
        assert isinstance(response.timestamp, float)
        assert response.timestamp > 0
    
    def test_agent_response_validation(self):
        """Test validación de datos en AgentResponse"""
        # Confidence fuera de rango
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            AgentResponse(
                agent_id="test",
                agent_name="Test",
                content="Test",
                confidence=1.5,  # Inválido
                reasoning="Test",
                sources=[],
                metadata={},
                processing_time_ms=100.0,
                capabilities_used=[]
            )
        
        # Sources no es lista
        with pytest.raises(ValueError, match="Sources must be a list"):
            AgentResponse(
                agent_id="test",
                agent_name="Test",
                content="Test",
                confidence=0.8,
                reasoning="Test",
                sources="not a list",  # Inválido
                metadata={},
                processing_time_ms=100.0,
                capabilities_used=[]
            )
    
    def test_agent_response_metadata_completion(self):
        """Test que metadata se completa con campos requeridos"""
        response = AgentResponse(
            agent_id="test",
            agent_name="Test",
            content="Test",
            confidence=0.8,
            reasoning="Test",
            sources=[],
            metadata={},  # Vacío
            processing_time_ms=100.0,
            capabilities_used=[]
        )
        
        # Verificar que se añadieron campos requeridos
        assert "query_type" in response.metadata
        assert "processing_strategy" in response.metadata
        assert "source_count" in response.metadata

class TestAgentStats:
    """Tests para AgentStats"""
    
    def test_agent_stats_creation(self):
        """Test creación de AgentStats"""
        stats = AgentStats()
        
        assert stats.total_queries == 0
        assert stats.successful_queries == 0
        assert stats.failed_queries == 0
        assert stats.success_rate == 0.0
        assert stats.error_rate == 0.0
        assert stats.uptime_hours >= 0
    
    def test_agent_stats_update_success(self):
        """Test actualización de estadísticas exitosas"""
        stats = AgentStats()
        
        stats.update_success(100.0, 0.8)
        
        assert stats.total_queries == 1
        assert stats.successful_queries == 1
        assert stats.failed_queries == 0
        assert stats.success_rate == 1.0
        assert stats.error_rate == 0.0
        assert stats.avg_response_time_ms == 100.0
        assert stats.avg_confidence == 0.8
    
    def test_agent_stats_update_failure(self):
        """Test actualización de estadísticas de fallo"""
        stats = AgentStats()
        
        stats.update_failure("Test error")
        
        assert stats.total_queries == 1
        assert stats.successful_queries == 0
        assert stats.failed_queries == 1
        assert stats.success_rate == 0.0
        assert stats.error_rate == 1.0
        assert stats.last_error == "Test error"
        assert stats.last_error_timestamp is not None
    
    def test_agent_stats_mixed_updates(self):
        """Test estadísticas con éxitos y fallos mezclados"""
        stats = AgentStats()
        
        stats.update_success(100.0, 0.8)
        stats.update_success(200.0, 0.9)
        stats.update_failure("Error")
        
        assert stats.total_queries == 3
        assert stats.successful_queries == 2
        assert stats.failed_queries == 1
        assert stats.success_rate == 2/3
        assert stats.error_rate == 1/3
        assert stats.avg_response_time_ms == 150.0  # (100 + 200) / 2
        assert abs(stats.avg_confidence - 0.85) < 0.0001  # (0.8 + 0.9) / 2

class TestBaseAgent:
    """Tests para BaseAgent"""
    
    def test_agent_initialization(self):
        """Test inicialización básica del agente"""
        agent = TestAgent("TestAgent", "Test description")
        
        assert agent.name == "TestAgent"
        assert agent.description == "Test description"
        assert agent.status == AgentStatus.IDLE
        assert agent.agent_id.startswith("TestAgent_")
        assert len(agent.agent_id.split("_")[1]) == 8  # UUID hex de 8 caracteres
        assert isinstance(agent.stats, AgentStats)
        assert agent.stats.capabilities == agent.get_capabilities()
    
    def test_agent_capabilities(self):
        """Test obtención de capacidades"""
        agent = TestAgent("TestAgent", "Test description")
        capabilities = agent.get_capabilities()
        
        assert AgentCapability.DOCUMENT_SEARCH in capabilities
        assert AgentCapability.SYNTHESIS in capabilities
        assert len(capabilities) == 2
    
    def test_can_handle_query_basic(self):
        """Test evaluación básica de capacidad de manejo de consulta"""
        agent = TestAgent("TestAgent", "Test description")
        
        # Consulta que coincide con capacidades
        score1 = agent.can_handle_query("search for documents")
        assert score1 > 0.0
        
        # Consulta que no coincide
        score2 = agent.can_handle_query("weather forecast")
        assert score2 >= 0.0  # Puede ser 0 o muy bajo
        
        # Consulta vacía
        score3 = agent.can_handle_query("")
        assert score3 >= 0.0
    
    def test_can_handle_query_with_keywords(self):
        """Test evaluación con palabras clave específicas"""
        agent = TestAgent("TestAgent", "Test description")
        
        # Palabras clave de DOCUMENT_SEARCH
        score = agent.can_handle_query("find research papers")
        assert score > 0.0
        
        # Palabras clave de SYNTHESIS
        score = agent.can_handle_query("synthesize information")
        assert score > 0.0
    
    @pytest.mark.asyncio
    async def test_process_query_success(self):
        """Test procesamiento exitoso de consulta"""
        agent = TestAgent("TestAgent", "Test description")
        
        response = await agent.process_query("test query")
        
        assert isinstance(response, AgentResponse)
        assert response.agent_id == agent.agent_id
        assert response.agent_name == agent.name
        assert "test query" in response.content
        assert response.confidence == 0.8
        assert len(response.sources) == 1
    
    @pytest.mark.asyncio
    async def test_process_query_error(self):
        """Test manejo de errores en procesamiento"""
        agent = TestAgent("TestAgent", "Test description")
        
        with pytest.raises(AgentException):
            await agent.process_query("error")
    
    def test_status_update(self):
        """Test actualización de estado"""
        agent = TestAgent("TestAgent", "Test description")
        
        assert agent.status == AgentStatus.IDLE
        
        agent.update_status(AgentStatus.THINKING)
        assert agent.status == AgentStatus.THINKING
        
        agent.update_status(AgentStatus.COMPLETED)
        assert agent.status == AgentStatus.COMPLETED
    
    def test_tool_management(self):
        """Test gestión de herramientas"""
        agent = TestAgent("TestAgent", "Test description")
        
        # Mock tool
        mock_tool = Mock()
        mock_tool.__class__.__name__ = "MockTool"
        
        # Añadir herramienta
        agent.add_tool(mock_tool)
        assert len(agent.tools) == 1
        
        # Obtener herramienta
        retrieved_tool = agent.get_tool("MockTool")
        assert retrieved_tool == mock_tool
        
        # Herramienta no encontrada
        not_found = agent.get_tool("NonExistentTool")
        assert not_found is None
    
    @pytest.mark.asyncio
    async def test_use_tool_sync(self):
        """Test uso de herramienta síncrona"""
        agent = TestAgent("TestAgent", "Test description")
        
        # Mock tool síncrona
        mock_tool = Mock()
        mock_tool.__class__.__name__ = "MockTool"
        mock_tool.return_value = "tool result"
        
        agent.add_tool(mock_tool)
        
        result = await agent.use_tool("MockTool", param="value")
        assert result == "tool result"
        mock_tool.assert_called_once_with(param="value")
    
    @pytest.mark.asyncio
    async def test_use_tool_async(self):
        """Test uso de herramienta asíncrona"""
        agent = TestAgent("TestAgent", "Test description")
        
        # Mock tool asíncrona
        mock_tool = AsyncMock()
        mock_tool.__class__.__name__ = "AsyncMockTool"
        mock_tool.return_value = "async tool result"
        
        agent.add_tool(mock_tool)
        
        result = await agent.use_tool("AsyncMockTool", param="value")
        assert result == "async tool result"
        mock_tool.assert_called_once_with(param="value")
    
    @pytest.mark.asyncio
    async def test_use_tool_not_found(self):
        """Test uso de herramienta no encontrada"""
        agent = TestAgent("TestAgent", "Test description")
        
        with pytest.raises(ValueError, match="Tool NonExistent not found"):
            await agent.use_tool("NonExistent")
    
    def test_memory_operations(self):
        """Test operaciones de memoria"""
        agent = TestAgent("TestAgent", "Test description")
        
        # Mock memory manager
        mock_memory = Mock()
        agent.memory_manager = mock_memory
        
        # Recordar
        agent.remember("key", "value", "context")
        mock_memory.store_memory.assert_called_once_with(
            agent_id=agent.agent_id,
            key="key",
            value="value",
            context="context"
        )
        
        # Recordar
        mock_memory.get_memory.return_value = "retrieved_value"
        result = agent.recall("key", "context")
        
        mock_memory.get_memory.assert_called_once_with(
            agent_id=agent.agent_id,
            key="key",
            context="context"
        )
        assert result == "retrieved_value"
    
    def test_message_operations(self):
        """Test operaciones de mensajería"""
        agent = TestAgent("TestAgent", "Test description")
        
        # Enviar mensaje
        message = agent.send_message("recipient", "content", "info", {"meta": "data"})
        
        assert isinstance(message, AgentMessage)
        assert message.sender == agent.agent_id
        assert message.recipient == "recipient"
        assert message.content == "content"
        assert message.message_type == "info"
        assert message.metadata == {"meta": "data"}
        assert len(agent.interaction_history) == 1
        
        # Recibir mensaje
        incoming_message = AgentMessage(
            id="msg_id",
            sender="other_agent",
            recipient=agent.agent_id,
            content="incoming",
            message_type="response",
            metadata={}
        )
        
        agent.receive_message(incoming_message)
        assert len(agent.interaction_history) == 2
    
    def test_stats_recording(self):
        """Test registro de estadísticas"""
        agent = TestAgent("TestAgent", "Test description")
        
        # Registrar éxito
        agent._record_success(150.0, 0.9)
        
        stats = agent.get_stats()
        assert stats.total_queries == 1
        assert stats.successful_queries == 1
        assert stats.avg_response_time_ms == 150.0
        assert stats.avg_confidence == 0.9
        
        # Registrar fallo
        agent._record_failure("Test error")
        
        stats = agent.get_stats()
        assert stats.total_queries == 2
        assert stats.failed_queries == 1
        assert stats.last_error == "Test error"
    
    def test_health_check(self):
        """Test health check del agente"""
        agent = TestAgent("TestAgent", "Test description")
        
        health = agent.health_check()
        
        assert isinstance(health, dict)
        assert health["agent_id"] == agent.agent_id
        assert health["name"] == agent.name
        assert health["healthy"] is True
        assert "uptime_hours" in health
        assert "capabilities" in health
    
    def test_reset(self):
        """Test reset del agente"""
        agent = TestAgent("TestAgent", "Test description")
        
        # Añadir algo de estado
        agent.update_status(AgentStatus.THINKING)
        agent.send_message("test", "test", "test")
        
        assert agent.status != AgentStatus.IDLE
        assert len(agent.interaction_history) > 0
        
        # Reset
        agent.reset()
        
        assert agent.status == AgentStatus.IDLE
        assert len(agent.interaction_history) == 0
    
    def test_string_representation(self):
        """Test representación en string"""
        agent = TestAgent("TestAgent", "Test description")
        
        str_repr = str(agent)
        assert "TestAgent" in str_repr
        assert "idle" in str_repr
        assert "queries=0" in str_repr
        
        repr_str = repr(agent)
        assert repr_str == str_repr

class TestAgentMessage:
    """Tests para AgentMessage"""
    
    def test_message_creation(self):
        """Test creación de mensaje"""
        message = AgentMessage(
            id="test_id",
            sender="sender_id",
            recipient="recipient_id",
            content="test content",
            message_type="info",
            metadata={"key": "value"}
        )
        
        assert message.id == "test_id"
        assert message.sender == "sender_id"
        assert message.recipient == "recipient_id"
        assert message.content == "test content"
        assert message.message_type == "info"
        assert message.metadata == {"key": "value"}
        assert isinstance(message.timestamp, float)
    
    def test_message_auto_id(self):
        """Test generación automática de ID"""
        message = AgentMessage(
            id="",  # ID vacío
            sender="sender",
            recipient="recipient",
            content="content",
            message_type="info",
            metadata={}
        )
        
        # Debe generar ID automáticamente
        assert message.id != ""
        assert len(message.id) > 0

if __name__ == "__main__":
    pytest.main([__file__])