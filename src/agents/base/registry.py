# -*- coding: utf-8 -*-
"""
Agent Registry - Sistema de Registro y Descubrimiento de Agentes
Cumple con HU1-CA1.2: Registro y Descubrimiento de Agentes
"""

from typing import Dict, List, Optional, Type, Any
import time
from collections import defaultdict
from src.agents.base.agent import BaseAgent, AgentCapability, AgentStats
try:
    from src.utils.logger import setup_logger
    logger = setup_logger()
except (ImportError, TypeError):
    import logging
    logger = logging.getLogger("agent.registry")

class AgentRegistry:
    """
    Registro centralizado para gestión de agentes del sistema.
    
    Funcionalidades:
    - Registro automático de agentes
    - Descubrimiento por capabilities
    - Health checks periódicos
    - Métricas agregadas de uso
    - API para consultar estado
    """
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._agents_by_name: Dict[str, BaseAgent] = {}
        self._agents_by_capability: Dict[AgentCapability, List[BaseAgent]] = defaultdict(list)
        self._agent_types: Dict[str, Type[BaseAgent]] = {}
        self._registry_stats = {
            "total_agents": 0,
            "healthy_agents": 0,
            "total_queries_processed": 0,
            "avg_success_rate": 0.0,
            "last_health_check": None
        }
        
        logger.info("AgentRegistry initialized")
    
    def register_agent(self, agent: BaseAgent) -> bool:
        """
        Registra un agente en el sistema
        
        Cumple con HU1-CA1.2: Registre automáticamente todos los agentes disponibles
        
        Args:
            agent: Instancia del agente a registrar
            
        Returns:
            bool: True si el registro fue exitoso
        """
        try:
            # Validar que el agente no esté ya registrado
            if agent.agent_id in self._agents:
                logger.warning(f"Agent {agent.name} already registered with ID {agent.agent_id}")
                return False
            
            # Registrar por ID y nombre
            self._agents[agent.agent_id] = agent
            self._agents_by_name[agent.name] = agent
            
            # Registrar por capabilities
            for capability in agent.get_capabilities():
                self._agents_by_capability[capability].append(agent)
            
            # Registrar tipo de agente
            self._agent_types[agent.name] = type(agent)
            
            # Actualizar estadísticas
            self._registry_stats["total_agents"] += 1
            
            logger.info(f"Registered agent: {agent.name} (ID: {agent.agent_id})", extra={
                "agent_id": agent.agent_id,
                "agent_name": agent.name,
                "capabilities": [cap.value for cap in agent.get_capabilities()],
                "total_agents": self._registry_stats["total_agents"]
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent.name}: {e}", extra={
                "agent_name": agent.name,
                "error": str(e)
            })
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Desregistra un agente del sistema"""
        try:
            if agent_id not in self._agents:
                logger.warning(f"Agent {agent_id} not found for unregistration")
                return False
            
            agent = self._agents[agent_id]
            
            # Remover de todos los índices
            del self._agents[agent_id]
            del self._agents_by_name[agent.name]
            del self._agent_types[agent.name]
            
            # Remover de capabilities
            for capability in agent.get_capabilities():
                if agent in self._agents_by_capability[capability]:
                    self._agents_by_capability[capability].remove(agent)
            
            # Actualizar estadísticas
            self._registry_stats["total_agents"] -= 1
            
            logger.info(f"Unregistered agent: {agent.name} (ID: {agent_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Obtiene agente por ID"""
        return self._agents.get(agent_id)
    
    def get_agent_by_name(self, name: str) -> Optional[BaseAgent]:
        """Obtiene agente por nombre"""
        return self._agents_by_name.get(name)
    
    def get_agents_by_capability(self, capability: AgentCapability) -> List[BaseAgent]:
        """
        Obtiene agentes que tienen una capacidad específica
        
        Cumple con HU1-CA1.2: Permita descubrir agentes por capabilities
        
        Args:
            capability: Capacidad específica a buscar
            
        Returns:
            List[BaseAgent]: Lista de agentes con esa capacidad
        """
        agents = self._agents_by_capability.get(capability, [])
        
        logger.debug(f"Found {len(agents)} agents with capability {capability.value}", extra={
            "capability": capability.value,
            "agent_count": len(agents),
            "agent_names": [agent.name for agent in agents]
        })
        
        return agents
    
    def get_all_agents(self) -> List[BaseAgent]:
        """Retorna todos los agentes registrados"""
        return list(self._agents.values())
    
    def find_best_agent_for_query(self, query: str, context: Dict[str, Any] = None) -> Optional[BaseAgent]:
        """
        Encuentra el mejor agente para manejar una consulta específica
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
            
        Returns:
            Optional[BaseAgent]: Mejor agente o None si ninguno es adecuado
        """
        best_agent = None
        best_score = 0.0
        
        for agent in self._agents.values():
            try:
                score = agent.can_handle_query(query, context)
                if score > best_score:
                    best_score = score
                    best_agent = agent
            except Exception as e:
                logger.error(f"Error evaluating agent {agent.name} for query: {e}")
                continue
        
        if best_agent and best_score >= 0.3:  # Umbral mínimo de confianza
            logger.debug(f"Best agent for query: {best_agent.name} (score: {best_score:.3f})", extra={
                "query_preview": query[:100],
                "best_agent": best_agent.name,
                "best_score": best_score
            })
            return best_agent
        
        logger.debug(f"No suitable agent found for query (best score: {best_score:.3f})", extra={
            "query_preview": query[:100],
            "best_score": best_score,
            "agents_evaluated": len(self._agents)
        })
        
        return None
    
    def get_agents_ranked_for_query(self, query: str, context: Dict[str, Any] = None, min_score: float = 0.1) -> List[tuple]:
        """
        Obtiene agentes rankeados por su capacidad de manejar una consulta
        
        Returns:
            List[tuple]: Lista de (agente, score) ordenada por score descendente
        """
        ranked_agents = []
        
        for agent in self._agents.values():
            try:
                score = agent.can_handle_query(query, context)
                if score >= min_score:
                    ranked_agents.append((agent, score))
            except Exception as e:
                logger.error(f"Error evaluating agent {agent.name}: {e}")
                continue
        
        # Ordenar por score descendente
        ranked_agents.sort(key=lambda x: x[1], reverse=True)
        
        return ranked_agents
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica salud de todos los agentes
        
        Cumple con HU1-CA1.2: Mantenga estado de salud de cada agente
        
        Returns:
            Dict: Estado de salud de todos los agentes
        """
        health_status = {}
        healthy_count = 0
        
        for agent in self._agents.values():
            try:
                agent_health = agent.health_check()
                health_status[agent.name] = agent_health
                
                if agent_health.get("healthy", False):
                    healthy_count += 1
                    
            except Exception as e:
                health_status[agent.name] = {
                    "healthy": False,
                    "error": str(e),
                    "agent_id": agent.agent_id
                }
                logger.error(f"Health check failed for {agent.name}: {e}")
        
        # Actualizar estadísticas del registry
        self._registry_stats["healthy_agents"] = healthy_count
        self._registry_stats["last_health_check"] = time.time()
        
        overall_health = {
            "registry_healthy": healthy_count > 0,
            "total_agents": len(self._agents),
            "healthy_agents": healthy_count,
            "unhealthy_agents": len(self._agents) - healthy_count,
            "health_percentage": (healthy_count / len(self._agents) * 100) if self._agents else 0,
            "agents": health_status,
            "timestamp": time.time()
        }
        
        logger.info(f"Health check completed: {healthy_count}/{len(self._agents)} agents healthy", extra={
            "total_agents": len(self._agents),
            "healthy_agents": healthy_count,
            "health_percentage": overall_health["health_percentage"]
        })
        
        return overall_health
    
    def get_agent_stats(self) -> Dict[str, AgentStats]:
        """
        Retorna estadísticas de todos los agentes
        
        Cumple con HU1-CA1.2: Proporcione métricas de uso por agente
        
        Returns:
            Dict: Estadísticas por agente
        """
        stats = {}
        total_queries = 0
        total_success_rate = 0.0
        
        for agent in self._agents.values():
            agent_stats = agent.get_stats()
            stats[agent.name] = agent_stats
            
            total_queries += agent_stats.total_queries
            if agent_stats.total_queries > 0:
                total_success_rate += agent_stats.success_rate
        
        # Actualizar estadísticas agregadas
        self._registry_stats["total_queries_processed"] = total_queries
        self._registry_stats["avg_success_rate"] = (
            total_success_rate / len(self._agents) if self._agents else 0.0
        )
        
        return stats
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas agregadas del registry"""
        # Actualizar estadísticas antes de retornar
        self.get_agent_stats()
        
        return {
            **self._registry_stats,
            "capabilities_available": list(self._agents_by_capability.keys()),
            "agent_types": list(self._agent_types.keys()),
            "agents_by_capability": {
                cap.value: len(agents) 
                for cap, agents in self._agents_by_capability.items()
            }
        }
    
    def get_capability_coverage(self) -> Dict[str, int]:
        """Obtiene cobertura de capacidades disponibles"""
        return {
            capability.value: len(agents)
            for capability, agents in self._agents_by_capability.items()
        }
    
    def clear_registry(self):
        """Limpia completamente el registry (útil para testing)"""
        self._agents.clear()
        self._agents_by_name.clear()
        self._agents_by_capability.clear()
        self._agent_types.clear()
        self._registry_stats = {
            "total_agents": 0,
            "healthy_agents": 0,
            "total_queries_processed": 0,
            "avg_success_rate": 0.0,
            "last_health_check": None
        }
        
        logger.info("Agent registry cleared")
    
    def __len__(self) -> int:
        """Retorna número de agentes registrados"""
        return len(self._agents)
    
    def __contains__(self, agent_id: str) -> bool:
        """Verifica si un agente está registrado"""
        return agent_id in self._agents
    
    def __str__(self) -> str:
        return f"AgentRegistry(agents={len(self._agents)}, capabilities={len(self._agents_by_capability)})"

# Instancia global del registry
agent_registry = AgentRegistry()