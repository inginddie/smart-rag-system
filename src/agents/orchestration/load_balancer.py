#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LoadBalancer - Balanceador de carga para agentes
Implementa CA5.3: Optimización de Performance
"""

from typing import Dict, List, Any, Optional
import logging
import time
from enum import Enum
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Estrategias de balanceo de carga"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RESPONSE_TIME = "weighted_response_time"
    RANDOM = "random"


class AgentStats:
    """Estadísticas de un agente"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.active_connections = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        self.last_request_time = 0.0
        self.response_times = deque(maxlen=100)  # Últimos 100 tiempos
    
    def start_request(self):
        """Inicia una request"""
        self.active_connections += 1
        self.total_requests += 1
        self.last_request_time = time.time()
    
    def end_request(self, success: bool, response_time: float):
        """Termina una request"""
        self.active_connections = max(0, self.active_connections - 1)
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        self.total_response_time += response_time
        self.response_times.append(response_time)
    
    def get_avg_response_time(self) -> float:
        """Obtiene tiempo de respuesta promedio"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def get_success_rate(self) -> float:
        """Obtiene tasa de éxito"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    def get_load_score(self) -> float:
        """
        Calcula score de carga (menor es mejor)
        Combina conexiones activas, tiempo de respuesta y tasa de éxito
        """
        # Penalizar conexiones activas
        connection_penalty = self.active_connections * 0.3
        
        # Penalizar tiempo de respuesta alto
        avg_time = self.get_avg_response_time()
        time_penalty = min(avg_time / 10.0, 2.0)  # Max penalty of 2.0
        
        # Penalizar baja tasa de éxito
        success_rate = self.get_success_rate()
        success_penalty = (1.0 - success_rate) * 2.0
        
        return connection_penalty + time_penalty + success_penalty


class LoadBalancer:
    """
    Balanceador de carga para agentes
    
    Distribuye requests entre agentes disponibles usando diferentes estrategias
    """
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.WEIGHTED_RESPONSE_TIME):
        """
        Inicializa el load balancer
        
        Args:
            strategy: Estrategia de balanceo
        """
        self.strategy = strategy
        self._agent_stats: Dict[str, AgentStats] = {}
        self._round_robin_index = 0
        
        self._metrics = {
            'total_requests': 0,
            'balanced_requests': 0,
            'strategy_changes': 0
        }
        
        logger.info(f"LoadBalancer initialized with strategy: {strategy.value}")
    
    def select_agent(self, available_agents: List[str]) -> Optional[str]:
        """
        Selecciona un agente usando la estrategia configurada
        
        Args:
            available_agents: Lista de agentes disponibles
        
        Returns:
            Nombre del agente seleccionado o None
        """
        if not available_agents:
            return None
        
        self._metrics['total_requests'] += 1
        
        # Asegurar que todos los agentes tienen stats
        for agent in available_agents:
            if agent not in self._agent_stats:
                self._agent_stats[agent] = AgentStats(agent)
        
        # Seleccionar según estrategia
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            selected = self._select_round_robin(available_agents)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            selected = self._select_least_connections(available_agents)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_RESPONSE_TIME:
            selected = self._select_weighted_response_time(available_agents)
        else:  # RANDOM
            import random
            selected = random.choice(available_agents)
        
        if selected:
            self._metrics['balanced_requests'] += 1
            self._agent_stats[selected].start_request()
        
        logger.debug(f"LoadBalancer selected: {selected} from {len(available_agents)} agents")
        return selected
    
    def _select_round_robin(self, agents: List[str]) -> str:
        """Selección round robin"""
        selected = agents[self._round_robin_index % len(agents)]
        self._round_robin_index += 1
        return selected
    
    def _select_least_connections(self, agents: List[str]) -> str:
        """Selección por menor número de conexiones activas"""
        min_connections = float('inf')
        selected = agents[0]
        
        for agent in agents:
            stats = self._agent_stats[agent]
            if stats.active_connections < min_connections:
                min_connections = stats.active_connections
                selected = agent
        
        return selected
    
    def _select_weighted_response_time(self, agents: List[str]) -> str:
        """Selección por tiempo de respuesta ponderado"""
        min_score = float('inf')
        selected = agents[0]
        
        for agent in agents:
            stats = self._agent_stats[agent]
            score = stats.get_load_score()
            
            if score < min_score:
                min_score = score
                selected = agent
        
        return selected
    
    def record_request_completion(
        self,
        agent_name: str,
        success: bool,
        response_time: float
    ):
        """
        Registra la finalización de una request
        
        Args:
            agent_name: Nombre del agente
            success: Si la request fue exitosa
            response_time: Tiempo de respuesta en segundos
        """
        if agent_name in self._agent_stats:
            self._agent_stats[agent_name].end_request(success, response_time)
    
    def get_agent_stats(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene estadísticas de un agente
        
        Args:
            agent_name: Nombre del agente
        
        Returns:
            Diccionario con estadísticas
        """
        if agent_name not in self._agent_stats:
            return None
        
        stats = self._agent_stats[agent_name]
        return {
            'agent_name': agent_name,
            'active_connections': stats.active_connections,
            'total_requests': stats.total_requests,
            'successful_requests': stats.successful_requests,
            'failed_requests': stats.failed_requests,
            'success_rate': stats.get_success_rate(),
            'avg_response_time': stats.get_avg_response_time(),
            'load_score': stats.get_load_score(),
            'last_request_time': stats.last_request_time
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene estadísticas de todos los agentes"""
        return {
            agent_name: self.get_agent_stats(agent_name)
            for agent_name in self._agent_stats.keys()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del load balancer"""
        total_active = sum(
            stats.active_connections for stats in self._agent_stats.values()
        )
        
        return {
            **self._metrics,
            'strategy': self.strategy.value,
            'total_agents': len(self._agent_stats),
            'total_active_connections': total_active,
            'avg_connections_per_agent': (
                total_active / len(self._agent_stats) if self._agent_stats else 0.0
            )
        }
    
    def change_strategy(self, new_strategy: LoadBalancingStrategy):
        """
        Cambia la estrategia de balanceo
        
        Args:
            new_strategy: Nueva estrategia
        """
        old_strategy = self.strategy
        self.strategy = new_strategy
        self._metrics['strategy_changes'] += 1
        
        logger.info(f"LoadBalancer strategy changed: {old_strategy.value} -> {new_strategy.value}")
    
    def reset_stats(self):
        """Reset de todas las estadísticas"""
        self._agent_stats.clear()
        self._round_robin_index = 0
        
        logger.info("LoadBalancer stats reset")
    
    def get_healthiest_agents(self, agents: List[str], count: int = 3) -> List[str]:
        """
        Obtiene los agentes más saludables
        
        Args:
            agents: Lista de agentes disponibles
            count: Número de agentes a retornar
        
        Returns:
            Lista de agentes ordenados por salud (mejor primero)
        """
        # Asegurar stats para todos los agentes
        for agent in agents:
            if agent not in self._agent_stats:
                self._agent_stats[agent] = AgentStats(agent)
        
        # Ordenar por load score (menor es mejor)
        sorted_agents = sorted(
            agents,
            key=lambda a: self._agent_stats[a].get_load_score()
        )
        
        return sorted_agents[:count]
