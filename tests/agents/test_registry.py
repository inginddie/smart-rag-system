# -*- coding: utf-8 -*-
"""
Tests unitarios para AgentRegistry
Cumple con Tarea 1.4: Tests para AgentRegistry registration y discovery
"""

import pytest
from unittest.mock import Mock
from src.agents.base.agent import BaseAgent, AgentCapability, AgentResponse
from src.agents.base.registry import AgentRegistry

class MockAgent(BaseAgent):
    """Agente mock para testing"""
    
    def __init__(self, name, capabilities=None):
        self._capabilities = capabilities or [AgentCapability.DOCUMENT_SEARCH]
        super().__init__(name, f"Mock {name}")
    
    def get_capabilities(self):
        return self._capabilities
    
    async def process_query(self, query, context=None):
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name=self.name,
            content=f"Mock response from {self.name}",
            confidence=0.8,
            reasoning="Mock reasoning",
            sources=[],
            metadata={"query_type": "mock", "processing_strategy": "mock", "source_count": 0},
            processing_time_ms=100.0,
            capabilities_used=self._capabilities
        )

class TestAgentRegistry:
    """Tests para AgentRegistry"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.registry = AgentRegistry()
    
    def test_registry_initialization(self):
        """Test inicialización del registry"""
        assert len(self.registry) == 0
        assert self.registry.get_all_agents() == []
        
        stats = self.registry.get_registry_stats()
        assert stats["total_agents"] == 0
        assert stats["healthy_agents"] == 0
    
    def test_register_agent_success(self):
        """Test registro exitoso de agente"""
        agent = MockAgent("TestAgent")
        
        result = self.registry.register_agent(agent)
        
        assert result is True
        assert len(self.registry) == 1
        assert agent.agent_id in self.registry
        assert self.registry.get_agent(agent.agent_id) == agent
        assert self.registry.get_agent_by_name("TestAgent") == agent
    
    def test_register_duplicate_agent(self):
        """Test registro de agente duplicado"""
        agent = MockAgent("TestAgent")
        
        # Primer registro
        result1 = self.registry.register_agent(agent)
        assert result1 is True
        
        # Segundo registro del mismo agente
        result2 = self.registry.register_agent(agent)
        assert result2 is False
        assert len(self.registry) == 1
    
    def test_unregister_agent(self):
        """Test desregistro de agente"""
        agent = MockAgent("TestAgent")
        self.registry.register_agent(agent)
        
        assert len(self.registry) == 1
        
        result = self.registry.unregister_agent(agent.agent_id)
        
        assert result is True
        assert len(self.registry) == 0
        assert self.registry.get_agent(agent.agent_id) is None
        assert self.registry.get_agent_by_name("TestAgent") is None
    
    def test_unregister_nonexistent_agent(self):
        """Test desregistro de agente inexistente"""
        result = self.registry.unregister_agent("nonexistent_id")
        assert result is False
    
    def test_get_agents_by_capability(self):
        """Test obtención de agentes por capacidad"""
        agent1 = MockAgent("Agent1", [AgentCapability.DOCUMENT_SEARCH])
        agent2 = MockAgent("Agent2", [AgentCapability.COMPARISON_ANALYSIS])
        agent3 = MockAgent("Agent3", [AgentCapability.DOCUMENT_SEARCH, AgentCapability.SYNTHESIS])
        
        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)
        self.registry.register_agent(agent3)
        
        # Buscar por DOCUMENT_SEARCH
        search_agents = self.registry.get_agents_by_capability(AgentCapability.DOCUMENT_SEARCH)
        assert len(search_agents) == 2
        assert agent1 in search_agents
        assert agent3 in search_agents
        
        # Buscar por COMPARISON_ANALYSIS
        comparison_agents = self.registry.get_agents_by_capability(AgentCapability.COMPARISON_ANALYSIS)
        assert len(comparison_agents) == 1
        assert agent2 in comparison_agents
        
        # Buscar por capacidad no existente
        synthesis_agents = self.registry.get_agents_by_capability(AgentCapability.SYNTHESIS)
        assert len(synthesis_agents) == 1
        assert agent3 in synthesis_agents
    
    def test_find_best_agent_for_query(self):
        """Test búsqueda del mejor agente para una consulta"""
        # Crear agentes con diferentes capacidades de manejo
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        
        # Mock can_handle_query para diferentes scores
        agent1.can_handle_query = Mock(return_value=0.8)
        agent2.can_handle_query = Mock(return_value=0.6)
        
        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)
        
        best_agent = self.registry.find_best_agent_for_query("test query")
        
        assert best_agent == agent1
        agent1.can_handle_query.assert_called_once_with("test query", None)
        agent2.can_handle_query.assert_called_once_with("test query", None)
    
    def test_find_best_agent_no_suitable(self):
        """Test cuando ningún agente es adecuado"""
        agent = MockAgent("Agent1")
        agent.can_handle_query = Mock(return_value=0.2)  # Score muy bajo
        
        self.registry.register_agent(agent)
        
        best_agent = self.registry.find_best_agent_for_query("test query")
        
        assert best_agent is None
    
    def test_find_best_agent_with_error(self):
        """Test manejo de errores en evaluación de agentes"""
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        
        # Agent1 lanza excepción
        agent1.can_handle_query = Mock(side_effect=Exception("Test error"))
        agent2.can_handle_query = Mock(return_value=0.8)
        
        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)
        
        best_agent = self.registry.find_best_agent_for_query("test query")
        
        # Debe retornar agent2 a pesar del error en agent1
        assert best_agent == agent2
    
    def test_get_agents_ranked_for_query(self):
        """Test obtención de agentes rankeados"""
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        agent3 = MockAgent("Agent3")
        
        agent1.can_handle_query = Mock(return_value=0.9)
        agent2.can_handle_query = Mock(return_value=0.7)
        agent3.can_handle_query = Mock(return_value=0.05)  # Muy bajo, no incluido
        
        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)
        self.registry.register_agent(agent3)
        
        ranked = self.registry.get_agents_ranked_for_query("test query", min_score=0.1)
        
        assert len(ranked) == 2
        assert ranked[0] == (agent1, 0.9)  # Mejor score primero
        assert ranked[1] == (agent2, 0.7)
    
    def test_health_check(self):
        """Test health check del registry"""
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        
        # Mock health check responses
        agent1.health_check = Mock(return_value={"healthy": True, "agent_id": agent1.agent_id})
        agent2.health_check = Mock(return_value={"healthy": False, "agent_id": agent2.agent_id})
        
        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)
        
        health = self.registry.health_check()
        
        assert health["registry_healthy"] is True
        assert health["total_agents"] == 2
        assert health["healthy_agents"] == 1
        assert health["unhealthy_agents"] == 1
        assert health["health_percentage"] == 50.0
        assert "Agent1" in health["agents"]
        assert "Agent2" in health["agents"]
    
    def test_health_check_with_exception(self):
        """Test health check con excepción en agente"""
        agent = MockAgent("Agent1")
        agent.health_check = Mock(side_effect=Exception("Health check error"))
        
        self.registry.register_agent(agent)
        
        health = self.registry.health_check()
        
        assert health["healthy_agents"] == 0
        assert health["unhealthy_agents"] == 1
        assert health["agents"]["Agent1"]["healthy"] is False
        assert "error" in health["agents"]["Agent1"]
    
    def test_get_agent_stats(self):
        """Test obtención de estadísticas de agentes"""
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        
        # Mock stats
        mock_stats1 = Mock()
        mock_stats1.total_queries = 10
        mock_stats1.success_rate = 0.9
        
        mock_stats2 = Mock()
        mock_stats2.total_queries = 5
        mock_stats2.success_rate = 0.8
        
        agent1.get_stats = Mock(return_value=mock_stats1)
        agent2.get_stats = Mock(return_value=mock_stats2)
        
        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)
        
        stats = self.registry.get_agent_stats()
        
        assert "Agent1" in stats
        assert "Agent2" in stats
        assert stats["Agent1"] == mock_stats1
        assert stats["Agent2"] == mock_stats2
    
    def test_get_registry_stats(self):
        """Test obtención de estadísticas del registry"""
        agent1 = MockAgent("Agent1", [AgentCapability.DOCUMENT_SEARCH])
        agent2 = MockAgent("Agent2", [AgentCapability.COMPARISON_ANALYSIS])
        
        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)
        
        stats = self.registry.get_registry_stats()
        
        assert stats["total_agents"] == 2
        assert "capabilities_available" in stats
        assert "agent_types" in stats
        assert "agents_by_capability" in stats
        assert AgentCapability.DOCUMENT_SEARCH in stats["capabilities_available"]
        assert AgentCapability.COMPARISON_ANALYSIS in stats["capabilities_available"]
    
    def test_get_capability_coverage(self):
        """Test obtención de cobertura de capacidades"""
        agent1 = MockAgent("Agent1", [AgentCapability.DOCUMENT_SEARCH])
        agent2 = MockAgent("Agent2", [AgentCapability.DOCUMENT_SEARCH, AgentCapability.SYNTHESIS])
        
        self.registry.register_agent(agent1)
        self.registry.register_agent(agent2)
        
        coverage = self.registry.get_capability_coverage()
        
        assert coverage[AgentCapability.DOCUMENT_SEARCH.value] == 2
        assert coverage[AgentCapability.SYNTHESIS.value] == 1
    
    def test_clear_registry(self):
        """Test limpieza del registry"""
        agent = MockAgent("Agent1")
        self.registry.register_agent(agent)
        
        assert len(self.registry) == 1
        
        self.registry.clear_registry()
        
        assert len(self.registry) == 0
        assert self.registry.get_all_agents() == []
        
        stats = self.registry.get_registry_stats()
        assert stats["total_agents"] == 0
    
    def test_registry_contains(self):
        """Test operador 'in' del registry"""
        agent = MockAgent("Agent1")
        
        assert agent.agent_id not in self.registry
        
        self.registry.register_agent(agent)
        
        assert agent.agent_id in self.registry
    
    def test_registry_string_representation(self):
        """Test representación en string del registry"""
        agent = MockAgent("Agent1", [AgentCapability.DOCUMENT_SEARCH])
        self.registry.register_agent(agent)
        
        str_repr = str(self.registry)
        
        assert "AgentRegistry" in str_repr
        assert "agents=1" in str_repr
        assert "capabilities=1" in str_repr

if __name__ == "__main__":
    pytest.main([__file__])