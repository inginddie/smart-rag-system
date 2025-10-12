#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para WorkflowEngine y orquestación multi-agente
"""

import pytest
import asyncio
from unittest.mock import Mock

from src.agents.orchestration.workflow import WorkflowEngine, ExecutionMode
from src.agents.base.agent import BaseAgent, AgentResponse, AgentCapability


class MockAgent(BaseAgent):
    """Agente mock para tests"""
    
    def __init__(self, name: str, response_text: str = None, delay: float = 0.0):
        super().__init__(name, f"Mock agent {name}")
        self.response_text = response_text or f"Response from {name}"
        self.delay = delay
    
    def get_capabilities(self):
        return [AgentCapability.DOCUMENT_SEARCH]
    
    def can_handle_query(self, query: str, context=None):
        return 0.8
    
    async def process_query(self, query: str, context=None):
        # Simular delay
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_name=self.name,
            content=self.response_text,
            confidence=0.8,
            reasoning=f"Mock reasoning from {self.name}",
            sources=[],
            metadata={"query_type": "test", "processing_strategy": "mock", "source_count": 0},
            processing_time_ms=self.delay * 1000,
            capabilities_used=[AgentCapability.DOCUMENT_SEARCH]
        )


class TestWorkflowEngine:
    """Tests para WorkflowEngine"""
    
    @pytest.fixture
    def engine(self):
        return WorkflowEngine(default_timeout=5.0)
    
    @pytest.fixture
    def agents(self):
        return [
            MockAgent("Agent1", "Response 1"),
            MockAgent("Agent2", "Response 2"),
            MockAgent("Agent3", "Response 3")
        ]
    
    def test_initialization(self, engine):
        """Test: Inicialización correcta"""
        assert engine.default_timeout == 5.0
        assert engine._metrics['total_workflows'] == 0
    
    @pytest.mark.asyncio
    async def test_execute_sequential(self, engine, agents):
        """Test: Ejecución secuencial de agentes"""
        responses = await engine.execute_sequential(agents, "test query")
        
        assert len(responses) == 3
        assert all(isinstance(r, AgentResponse) for r in responses)
        assert responses[0].agent_name == "Agent1"
        assert responses[1].agent_name == "Agent2"
        assert responses[2].agent_name == "Agent3"
    
    @pytest.mark.asyncio
    async def test_execute_parallel(self, engine, agents):
        """Test: Ejecución paralela de agentes"""
        responses = await engine.execute_parallel(agents, "test query")
        
        assert len(responses) == 3
        assert all(isinstance(r, AgentResponse) for r in responses)
        # En paralelo, el orden puede variar
        agent_names = {r.agent_name for r in responses}
        assert agent_names == {"Agent1", "Agent2", "Agent3"}
    
    @pytest.mark.asyncio
    async def test_parallel_faster_than_sequential(self, engine):
        """Test: Ejecución paralela es más rápida que secuencial"""
        # Agentes con delay
        slow_agents = [
            MockAgent("Slow1", delay=0.5),
            MockAgent("Slow2", delay=0.5),
            MockAgent("Slow3", delay=0.5)
        ]
        
        # Medir tiempo secuencial
        import time
        start = time.time()
        await engine.execute_sequential(slow_agents, "test")
        sequential_time = time.time() - start
        
        # Medir tiempo paralelo
        start = time.time()
        await engine.execute_parallel(slow_agents, "test")
        parallel_time = time.time() - start
        
        # Paralelo debe ser significativamente más rápido
        assert parallel_time < sequential_time * 0.6  # Al menos 40% más rápido
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, engine):
        """Test: Manejo de timeouts"""
        # Agente que tarda más que el timeout
        slow_agent = MockAgent("SlowAgent", delay=10.0)
        
        # Ejecutar con timeout corto
        engine.default_timeout = 1.0
        responses = await engine.execute_parallel([slow_agent], "test")
        
        # Debe retornar lista vacía (agente falló por timeout)
        assert len(responses) == 0
    
    def test_synthesize_single_response(self, engine):
        """Test: Síntesis de una sola respuesta"""
        response = AgentResponse(
            agent_id="test",
            agent_name="TestAgent",
            content="Test content",
            confidence=0.9,
            reasoning="Test reasoning",
            sources=[],
            metadata={"query_type": "test", "processing_strategy": "test", "source_count": 0},
            processing_time_ms=10.0,
            capabilities_used=[]
        )
        
        result = engine.synthesize_responses([response], "test query")
        
        assert result['answer'] == "Test content"
        assert result['agent_name'] == "TestAgent"
        assert result['confidence'] == 0.9
        assert result['metadata']['agent_count'] == 1
    
    def test_synthesize_multiple_responses(self, engine):
        """Test: Síntesis de múltiples respuestas"""
        responses = [
            AgentResponse(
                agent_id="1",
                agent_name="Agent1",
                content="Content 1",
                confidence=0.8,
                reasoning="Reasoning 1",
                sources=[],
                metadata={"query_type": "test", "processing_strategy": "test", "source_count": 0},
                processing_time_ms=10.0,
                capabilities_used=[]
            ),
            AgentResponse(
                agent_id="2",
                agent_name="Agent2",
                content="Content 2",
                confidence=0.9,
                reasoning="Reasoning 2",
                sources=[],
                metadata={"query_type": "test", "processing_strategy": "test", "source_count": 0},
                processing_time_ms=10.0,
                capabilities_used=[]
            )
        ]
        
        result = engine.synthesize_responses(responses, "test query")
        
        assert result['agent_name'] == 'multi-agent'
        assert result['metadata']['agent_count'] == 2
        assert 'Agent1' in result['answer']
        assert 'Agent2' in result['answer']
        assert abs(result['confidence'] - 0.85) < 0.01  # Promedio de 0.8 y 0.9
    
    def test_detect_multi_agent_query(self, engine):
        """Test: Detección de queries multi-agente"""
        # Query que requiere múltiples agentes
        requires, reasons = engine.detect_multi_agent_query(
            "Compare Python vs Java and analyze their performance"
        )
        assert requires is True
        assert len(reasons) > 0
        
        # Query simple
        requires, reasons = engine.detect_multi_agent_query(
            "What is Python?"
        )
        assert requires is False
    
    def test_metrics_tracking(self, engine, agents):
        """Test: Tracking de métricas"""
        asyncio.run(engine.execute_sequential(agents, "test"))
        asyncio.run(engine.execute_parallel(agents, "test"))
        
        metrics = engine.get_metrics()
        assert metrics['sequential_executions'] == 1
        assert metrics['parallel_executions'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
