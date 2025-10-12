#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para AgentOrchestrator y AgentSelector
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.agents.orchestration.selector import AgentSelector, SelectionDecision
from src.agents.orchestration.orchestrator import AgentOrchestrator
from src.agents.base.agent import BaseAgent, AgentResponse, AgentCapability
from src.agents.base.registry import AgentRegistry


class MockAgent(BaseAgent):
    """Agente mock para tests"""
    
    def __init__(self, name: str, score: float = 0.8):
        super().__init__(name, f"Mock agent {name}")
        self.mock_score = score
    
    def get_capabilities(self):
        return [AgentCapability.DOCUMENT_SEARCH]
    
    def can_handle_query(self, query: str, context=None):
        return self.mock_score
    
    async def process_query(self, query: str, context=None):
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name=self.name,
            content=f"Response from {self.name}",
            confidence=self.mock_score,
            reasoning="Mock reasoning",
            sources=[],
            metadata={"query_type": "test", "processing_strategy": "mock", "source_count": 0},
            processing_time_ms=10.0,
            capabilities_used=[AgentCapability.DOCUMENT_SEARCH]
        )


class TestAgentSelector:
    """Tests para AgentSelector"""
    
    @pytest.fixture
    def selector(self):
        return AgentSelector(confidence_threshold=0.7)
    
    @pytest.fixture
    def agents(self):
        return [
            MockAgent("Agent1", score=0.9),
            MockAgent("Agent2", score=0.5),
            MockAgent("Agent3", score=0.3)
        ]
    
    def test_initialization(self, selector):
        """Test: Inicialización correcta"""
        assert selector.confidence_threshold == 0.7
        assert selector._metrics['total_selections'] == 0
    
    def test_select_best_agent(self, selector, agents):
        """Test: Selecciona el agente con mayor score"""
        decision = selector.select_agent("test query", agents)
        
        assert decision.selected_agent is not None
        assert decision.selected_agent.name == "Agent1"
        assert decision.confidence == 0.9
        assert not decision.should_use_fallback
    
    def test_fallback_when_below_threshold(self, selector, agents):
        """Test: Fallback cuando todos los scores están bajo el threshold"""
        low_score_agents = [MockAgent("LowAgent", score=0.3)]
        decision = selector.select_agent("test query", low_score_agents)
        
        assert decision.selected_agent is None
        assert decision.should_use_fallback
        assert "below threshold" in decision.reasoning
    
    def test_fallback_when_no_agents(self, selector):
        """Test: Fallback cuando no hay agentes disponibles"""
        decision = selector.select_agent("test query", [])
        
        assert decision.selected_agent is None
        assert decision.should_use_fallback
        assert "No agents available" in decision.reasoning
    
    def test_metrics_tracking(self, selector, agents):
        """Test: Tracking de métricas"""
        # Primera selección - agente
        selector.select_agent("test query 1", agents)
        
        # Segunda selección - fallback
        low_agents = [MockAgent("LowAgent", score=0.3)]
        selector.select_agent("test query 2", low_agents)
        
        metrics = selector.get_metrics()
        assert metrics['total_selections'] == 2
        assert metrics['agent_selections'] == 1
        assert metrics['fallback_selections'] == 1
        assert metrics['agent_selection_rate'] == 0.5
    
    def test_decision_history(self, selector, agents):
        """Test: Historial de decisiones"""
        selector.select_agent("query 1", agents)
        selector.select_agent("query 2", agents)
        
        history = selector.get_recent_decisions(limit=2)
        assert len(history) == 2
        assert all('selected_agent' in d for d in history)
    
    def test_threshold_adjustment(self, selector):
        """Test: Ajuste de threshold"""
        selector.adjust_threshold(0.8)
        assert selector.confidence_threshold == 0.8
        
        with pytest.raises(ValueError):
            selector.adjust_threshold(1.5)


class TestAgentOrchestrator:
    """Tests para AgentOrchestrator"""
    
    @pytest.fixture
    def registry(self):
        registry = AgentRegistry()
        registry.register_agent(MockAgent("Agent1", score=0.9))
        registry.register_agent(MockAgent("Agent2", score=0.5))
        return registry
    
    @pytest.fixture
    def orchestrator(self, registry):
        return AgentOrchestrator(
            agent_registry=registry,
            confidence_threshold=0.7,
            enable_multi_agent=False
        )
    
    @pytest.mark.asyncio
    async def test_orchestrate_with_agent(self, orchestrator):
        """Test: Orquestación con agente seleccionado"""
        result = await orchestrator.orchestrate("test query")
        
        assert 'answer' in result
        assert 'agent_name' in result
        assert result['agent_name'] == 'Agent1'
        assert 'orchestration' in result
    
    @pytest.mark.asyncio
    async def test_orchestrate_with_fallback(self, orchestrator):
        """Test: Orquestación con fallback"""
        def fallback_handler(query):
            return {"answer": "Fallback response"}
        
        # Usar threshold alto para forzar fallback
        orchestrator.selector.adjust_threshold(0.95)
        
        result = await orchestrator.orchestrate(
            "test query",
            fallback_handler=fallback_handler
        )
        
        assert 'answer' in result
        assert result.get('metadata', {}).get('fallback') == True
    
    @pytest.mark.asyncio
    async def test_orchestrate_no_agents(self):
        """Test: Orquestación sin agentes disponibles"""
        empty_registry = AgentRegistry()
        orchestrator = AgentOrchestrator(empty_registry)
        
        result = await orchestrator.orchestrate("test query")
        
        assert 'answer' in result
        assert 'No agent available' in result['answer']
    
    def test_metrics_tracking(self, orchestrator):
        """Test: Tracking de métricas"""
        asyncio.run(orchestrator.orchestrate("query 1"))
        asyncio.run(orchestrator.orchestrate("query 2"))
        
        metrics = orchestrator.get_metrics()
        assert metrics['total_orchestrations'] == 2
        assert metrics['successful_orchestrations'] >= 0
    
    def test_get_recent_decisions(self, orchestrator):
        """Test: Obtener decisiones recientes"""
        asyncio.run(orchestrator.orchestrate("query 1"))
        asyncio.run(orchestrator.orchestrate("query 2"))
        
        decisions = orchestrator.get_recent_decisions(limit=2)
        assert len(decisions) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
