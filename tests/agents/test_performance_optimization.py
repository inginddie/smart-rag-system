#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para componentes de optimización de performance
"""

import pytest
import asyncio
import time
from unittest.mock import Mock

from src.agents.orchestration.circuit_breaker import (
    CircuitBreaker, CircuitBreakerManager, CircuitState, CircuitBreakerConfig
)
from src.agents.orchestration.load_balancer import (
    LoadBalancer, LoadBalancingStrategy, AgentStats
)
from src.agents.orchestration.performance_monitor import (
    PerformanceMonitor, PerformanceMetric
)


class TestCircuitBreaker:
    """Tests para CircuitBreaker"""
    
    @pytest.fixture
    def breaker(self):
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=10.0,
            slow_call_threshold=5.0
        )
        return CircuitBreaker("TestAgent", config)
    
    def test_initialization(self, breaker):
        """Test: Inicialización correcta"""
        assert breaker.name == "TestAgent"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_closed_state_allows_execution(self, breaker):
        """Test: Estado CLOSED permite ejecución"""
        def dummy_func():
            return "success"
        
        result = breaker.call(dummy_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
    
    def test_transition_to_open_after_failures(self, breaker):
        """Test: Transición a OPEN después de fallos"""
        def failing_func():
            raise Exception("Error")
        
        # Registrar fallos hasta alcanzar threshold
        for i in range(3):
            try:
                breaker.call(failing_func)
            except Exception:
                pass
        
        assert breaker.state == CircuitState.OPEN
    
    def test_transition_to_half_open_after_timeout(self, breaker):
        """Test: Transición a HALF_OPEN después de timeout"""
        def failing_func():
            raise Exception("Error")
        
        # Forzar estado OPEN
        for i in range(3):
            try:
                breaker.call(failing_func)
            except Exception:
                pass
        
        # Simular paso del tiempo
        breaker.last_failure_time = time.time() - 15.0  # Más que timeout
        
        # Próxima llamada debe transicionar a HALF_OPEN
        def success_func():
            return "success"
        
        breaker.call(success_func)
        # Después de una llamada exitosa en HALF_OPEN, aún está en HALF_OPEN
        # (necesita success_threshold éxitos)
        assert breaker.state == CircuitState.HALF_OPEN
    
    def test_transition_to_closed_after_successes(self, breaker):
        """Test: Transición a CLOSED después de éxitos en HALF_OPEN"""
        # Forzar estado HALF_OPEN
        breaker.state = CircuitState.HALF_OPEN
        
        def success_func():
            return "success"
        
        # Registrar éxitos hasta alcanzar threshold
        for i in range(2):
            breaker.call(success_func)
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    def test_metrics_tracking(self, breaker):
        """Test: Tracking de métricas"""
        def success_func():
            return "success"
        
        def failing_func():
            raise Exception("Error")
        
        breaker.call(success_func)
        
        try:
            breaker.call(failing_func)
        except Exception:
            pass
        
        metrics = breaker.get_metrics()
        assert metrics['total_calls'] == 2
        assert metrics['successful_calls'] == 1
        assert metrics['failed_calls'] == 1


class TestCircuitBreakerManager:
    """Tests para CircuitBreakerManager"""
    
    @pytest.fixture
    def manager(self):
        return CircuitBreakerManager()
    
    def test_get_breaker_creates_new(self, manager):
        """Test: get_breaker crea nuevo circuit breaker"""
        breaker = manager.get_breaker("Agent1")
        assert breaker.name == "Agent1"
        assert breaker.state == CircuitState.CLOSED
    
    def test_get_breaker_returns_existing(self, manager):
        """Test: get_breaker retorna existente"""
        breaker1 = manager.get_breaker("Agent1")
        breaker2 = manager.get_breaker("Agent1")
        assert breaker1 is breaker2
    
    def test_get_all_metrics(self, manager):
        """Test: Obtener métricas de todos los breakers"""
        manager.get_breaker("Agent1")
        manager.get_breaker("Agent2")
        
        metrics = manager.get_all_metrics()
        assert "Agent1" in metrics
        assert "Agent2" in metrics
    
    def test_get_healthy_agents(self, manager):
        """Test: Filtrado de agentes saludables"""
        # Crear breakers
        breaker1 = manager.get_breaker("Agent1")
        breaker2 = manager.get_breaker("Agent2")
        breaker3 = manager.get_breaker("Agent3")
        
        # Bloquear Agent2
        def failing_func():
            raise Exception("Error")
        
        for i in range(5):
            try:
                breaker2.call(failing_func)
            except Exception:
                pass
        
        healthy = manager.get_healthy_agents()
        assert "Agent1" in healthy
        assert "Agent2" not in healthy
        assert "Agent3" in healthy


class TestLoadBalancer:
    """Tests para LoadBalancer"""
    
    @pytest.fixture
    def balancer(self):
        return LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
    
    def test_initialization(self, balancer):
        """Test: Inicialización correcta"""
        assert balancer.strategy == LoadBalancingStrategy.ROUND_ROBIN
    
    def test_round_robin_selection(self, balancer):
        """Test: Selección round robin"""
        agents = ["Agent1", "Agent2", "Agent3"]
        
        selections = []
        for i in range(6):
            selected = balancer.select_agent(agents)
            selections.append(selected)
        
        # Debe ciclar: Agent1, Agent2, Agent3, Agent1, Agent2, Agent3
        expected = ["Agent1", "Agent2", "Agent3", "Agent1", "Agent2", "Agent3"]
        assert selections == expected
    
    def test_least_connections_selection(self):
        """Test: Selección por menor conexiones"""
        balancer = LoadBalancer(LoadBalancingStrategy.LEAST_CONNECTIONS)
        agents = ["Agent1", "Agent2"]
        
        # Agent1 tiene 0 conexiones, Agent2 tiene 0 conexiones
        selected1 = balancer.select_agent(agents)
        
        # Simular que Agent1 está ocupado
        balancer._agent_stats["Agent1"].active_connections = 2
        
        # Ahora debe seleccionar Agent2
        selected2 = balancer.select_agent(agents)
        
        assert selected1 == "Agent1"
        assert selected2 == "Agent2"
    
    def test_request_completion_tracking(self, balancer):
        """Test: Tracking de finalización de requests"""
        agent = "Agent1"
        balancer.select_agent([agent])  # Inicia request
        
        # Completar request exitosamente
        balancer.record_request_completion(agent, True, 1.5)
        
        stats = balancer.get_agent_stats(agent)
        assert stats['successful_requests'] == 1
        assert stats['avg_response_time'] == 1.5
        assert stats['success_rate'] == 1.0
    
    def test_get_healthiest_agents(self, balancer):
        """Test: Obtener agentes más saludables"""
        agents = ["Agent1", "Agent2", "Agent3"]
        
        # Hacer que Agent2 sea más lento
        balancer.select_agent(["Agent2"])
        balancer.record_request_completion("Agent2", True, 10.0)  # Lento
        
        # Agent1 y Agent3 son rápidos
        balancer.select_agent(["Agent1"])
        balancer.record_request_completion("Agent1", True, 1.0)
        
        healthiest = balancer.get_healthiest_agents(agents, count=2)
        
        # Agent1 debe estar primero (más saludable)
        assert "Agent1" in healthiest
        assert len(healthiest) <= 2


class TestPerformanceMonitor:
    """Tests para PerformanceMonitor"""
    
    @pytest.fixture
    def monitor(self):
        return PerformanceMonitor(max_metrics=100)
    
    def test_initialization(self, monitor):
        """Test: Inicialización correcta"""
        assert monitor.max_metrics == 100
    
    def test_record_metric(self, monitor):
        """Test: Registro de métricas"""
        monitor.record_metric("Agent1", "process_query", 150.0, True)
        
        metrics = monitor.get_agent_metrics("Agent1")
        assert metrics['total_requests'] == 1
        assert metrics['successful_requests'] == 1
        assert metrics['avg_duration_ms'] == 150.0
        assert metrics['success_rate'] == 1.0
    
    def test_global_metrics(self, monitor):
        """Test: Métricas globales"""
        monitor.record_metric("Agent1", "process_query", 100.0, True)
        monitor.record_metric("Agent2", "process_query", 200.0, False, "Error")
        
        global_metrics = monitor.get_global_metrics()
        assert global_metrics['total_requests'] == 2
        assert global_metrics['successful_requests'] == 1
        assert global_metrics['failed_requests'] == 1
        assert global_metrics['success_rate'] == 0.5
        assert global_metrics['avg_duration_ms'] == 150.0
    
    def test_operation_metrics(self, monitor):
        """Test: Métricas por operación"""
        monitor.record_metric("Agent1", "process_query", 100.0, True)
        monitor.record_metric("Agent2", "process_query", 200.0, True)
        monitor.record_metric("Agent1", "analyze", 50.0, True)
        
        query_metrics = monitor.get_operation_metrics("process_query")
        assert query_metrics['total_requests'] == 2
        assert query_metrics['agents_used'] == 2
        
        analyze_metrics = monitor.get_operation_metrics("analyze")
        assert analyze_metrics['total_requests'] == 1
        assert analyze_metrics['agents_used'] == 1
    
    def test_slow_agents_detection(self, monitor):
        """Test: Detección de agentes lentos"""
        monitor.record_metric("FastAgent", "process_query", 100.0, True)
        monitor.record_metric("SlowAgent", "process_query", 6000.0, True)
        
        slow_agents = monitor.get_slow_agents(threshold_ms=5000.0)
        
        assert len(slow_agents) == 1
        assert slow_agents[0]['agent_name'] == "SlowAgent"
    
    def test_failing_agents_detection(self, monitor):
        """Test: Detección de agentes con fallos"""
        # Agent1: 100% éxito
        monitor.record_metric("Agent1", "process_query", 100.0, True)
        
        # Agent2: 50% fallos
        monitor.record_metric("Agent2", "process_query", 100.0, True)
        monitor.record_metric("Agent2", "process_query", 100.0, False, "Error")
        
        failing_agents = monitor.get_failing_agents(threshold_rate=0.3)
        
        assert len(failing_agents) == 1
        assert failing_agents[0]['agent_name'] == "Agent2"
        assert failing_agents[0]['failure_rate'] == 0.5
    
    def test_performance_report(self, monitor):
        """Test: Generación de reporte completo"""
        monitor.record_metric("Agent1", "process_query", 100.0, True)
        monitor.record_metric("Agent2", "process_query", 200.0, False, "Error")
        
        report = monitor.generate_performance_report()
        
        assert 'global_metrics' in report
        assert 'agent_metrics' in report
        assert 'operation_metrics' in report
        assert 'slow_agents' in report
        assert 'failing_agents' in report
        assert 'report_timestamp' in report


class TestAgentStats:
    """Tests para AgentStats"""
    
    @pytest.fixture
    def stats(self):
        return AgentStats("TestAgent")
    
    def test_initialization(self, stats):
        """Test: Inicialización correcta"""
        assert stats.agent_name == "TestAgent"
        assert stats.active_connections == 0
        assert stats.total_requests == 0
    
    def test_start_request(self, stats):
        """Test: Inicio de request"""
        stats.start_request()
        
        assert stats.active_connections == 1
        assert stats.total_requests == 1
    
    def test_end_request_success(self, stats):
        """Test: Finalización exitosa de request"""
        stats.start_request()
        stats.end_request(success=True, response_time=1.5)
        
        assert stats.active_connections == 0
        assert stats.successful_requests == 1
        assert stats.failed_requests == 0
        assert 1.5 in stats.response_times
    
    def test_end_request_failure(self, stats):
        """Test: Finalización fallida de request"""
        stats.start_request()
        stats.end_request(success=False, response_time=2.0)
        
        assert stats.active_connections == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 1
    
    def test_avg_response_time(self, stats):
        """Test: Cálculo de tiempo promedio"""
        stats.start_request()
        stats.end_request(True, 1.0)
        
        stats.start_request()
        stats.end_request(True, 3.0)
        
        assert stats.get_avg_response_time() == 2.0
    
    def test_success_rate(self, stats):
        """Test: Cálculo de tasa de éxito"""
        stats.start_request()
        stats.end_request(True, 1.0)
        
        stats.start_request()
        stats.end_request(False, 1.0)
        
        assert stats.get_success_rate() == 0.5
    
    def test_load_score(self, stats):
        """Test: Cálculo de score de carga"""
        # Sin carga
        score1 = stats.get_load_score()
        
        # Con conexiones activas
        stats.active_connections = 5
        score2 = stats.get_load_score()
        
        # Score debe aumentar con más carga
        assert score2 > score1
