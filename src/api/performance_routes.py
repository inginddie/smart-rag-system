#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Routes para métricas de performance
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/performance", tags=["performance"])

# Instancia global del workflow engine (se inicializa en main.py)
_workflow_engine = None


def set_workflow_engine(engine):
    """Configura la instancia del workflow engine"""
    global _workflow_engine
    _workflow_engine = engine


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Obtiene métricas generales del sistema
    
    Returns:
        Diccionario con métricas del workflow engine
    """
    if not _workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not initialized")
    
    try:
        metrics = _workflow_engine.get_metrics()
        return {
            "status": "success",
            "data": metrics
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def get_performance_report() -> Dict[str, Any]:
    """
    Genera reporte completo de performance
    
    Returns:
        Reporte detallado con todas las métricas
    """
    if not _workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not initialized")
    
    try:
        report = _workflow_engine.get_performance_report()
        return {
            "status": "success",
            "data": report
        }
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_agent_metrics() -> Dict[str, Any]:
    """
    Obtiene métricas de todos los agentes
    
    Returns:
        Métricas por agente
    """
    if not _workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not initialized")
    
    try:
        # Métricas del performance monitor
        agent_metrics = _workflow_engine.performance_monitor.get_global_metrics()
        
        # Métricas del load balancer
        load_balancer_stats = _workflow_engine.load_balancer.get_all_stats()
        
        # Métricas del circuit breaker
        circuit_breaker_metrics = _workflow_engine.circuit_breaker_manager.get_all_metrics()
        
        return {
            "status": "success",
            "data": {
                "performance": agent_metrics,
                "load_balancer": load_balancer_stats,
                "circuit_breaker": circuit_breaker_metrics
            }
        }
    except Exception as e:
        logger.error(f"Error getting agent metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_name}")
async def get_agent_detail(agent_name: str) -> Dict[str, Any]:
    """
    Obtiene métricas detalladas de un agente específico
    
    Args:
        agent_name: Nombre del agente
    
    Returns:
        Métricas detalladas del agente
    """
    if not _workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not initialized")
    
    try:
        # Métricas de performance
        perf_metrics = _workflow_engine.performance_monitor.get_agent_metrics(agent_name)
        
        # Estadísticas del load balancer
        lb_stats = _workflow_engine.load_balancer.get_agent_stats(agent_name)
        
        # Estado del circuit breaker
        cb_breaker = _workflow_engine.circuit_breaker_manager.get_breaker(agent_name)
        cb_metrics = cb_breaker.get_metrics()
        
        return {
            "status": "success",
            "data": {
                "agent_name": agent_name,
                "performance": perf_metrics,
                "load_balancer": lb_stats,
                "circuit_breaker": cb_metrics
            }
        }
    except Exception as e:
        logger.error(f"Error getting agent detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slow-agents")
async def get_slow_agents(threshold_ms: float = 5000.0) -> Dict[str, Any]:
    """
    Obtiene agentes que están siendo lentos
    
    Args:
        threshold_ms: Umbral de latencia en milisegundos
    
    Returns:
        Lista de agentes lentos
    """
    if not _workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not initialized")
    
    try:
        slow_agents = _workflow_engine.performance_monitor.get_slow_agents(threshold_ms)
        return {
            "status": "success",
            "data": {
                "threshold_ms": threshold_ms,
                "slow_agents": slow_agents,
                "count": len(slow_agents)
            }
        }
    except Exception as e:
        logger.error(f"Error getting slow agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/failing-agents")
async def get_failing_agents(threshold_rate: float = 0.1) -> Dict[str, Any]:
    """
    Obtiene agentes con alta tasa de fallos
    
    Args:
        threshold_rate: Umbral de tasa de fallos (0.1 = 10%)
    
    Returns:
        Lista de agentes con fallos
    """
    if not _workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not initialized")
    
    try:
        failing_agents = _workflow_engine.performance_monitor.get_failing_agents(threshold_rate)
        return {
            "status": "success",
            "data": {
                "threshold_rate": threshold_rate,
                "failing_agents": failing_agents,
                "count": len(failing_agents)
            }
        }
    except Exception as e:
        logger.error(f"Error getting failing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/circuit-breakers")
async def get_circuit_breaker_status() -> Dict[str, Any]:
    """
    Obtiene estado de todos los circuit breakers
    
    Returns:
        Estado de circuit breakers por agente
    """
    if not _workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not initialized")
    
    try:
        metrics = _workflow_engine.circuit_breaker_manager.get_all_metrics()
        healthy = _workflow_engine.circuit_breaker_manager.get_healthy_agents()
        
        return {
            "status": "success",
            "data": {
                "metrics": metrics,
                "healthy_agents": healthy,
                "total_agents": len(metrics),
                "healthy_count": len(healthy)
            }
        }
    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/circuit-breakers/{agent_name}/reset")
async def reset_circuit_breaker(agent_name: str) -> Dict[str, Any]:
    """
    Reset manual de un circuit breaker
    
    Args:
        agent_name: Nombre del agente
    
    Returns:
        Confirmación del reset
    """
    if not _workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not initialized")
    
    try:
        breaker = _workflow_engine.circuit_breaker_manager.get_breaker(agent_name)
        breaker.reset()
        
        return {
            "status": "success",
            "message": f"Circuit breaker for {agent_name} has been reset",
            "data": breaker.get_metrics()
        }
    except Exception as e:
        logger.error(f"Error resetting circuit breaker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/load-balancer/stats")
async def get_load_balancer_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas del load balancer
    
    Returns:
        Estadísticas del load balancer
    """
    if not _workflow_engine:
        raise HTTPException(status_code=503, detail="Workflow engine not initialized")
    
    try:
        metrics = _workflow_engine.load_balancer.get_metrics()
        all_stats = _workflow_engine.load_balancer.get_all_stats()
        
        return {
            "status": "success",
            "data": {
                "metrics": metrics,
                "agent_stats": all_stats
            }
        }
    except Exception as e:
        logger.error(f"Error getting load balancer stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check del sistema de performance
    
    Returns:
        Estado de salud del sistema
    """
    if not _workflow_engine:
        return {
            "status": "unhealthy",
            "message": "Workflow engine not initialized"
        }
    
    try:
        # Obtener métricas básicas
        global_metrics = _workflow_engine.performance_monitor.get_global_metrics()
        slow_agents = _workflow_engine.performance_monitor.get_slow_agents()
        failing_agents = _workflow_engine.performance_monitor.get_failing_agents()
        
        # Determinar estado de salud
        is_healthy = (
            len(slow_agents) == 0 and
            len(failing_agents) == 0 and
            global_metrics.get('success_rate', 0) > 0.9
        )
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "data": {
                "success_rate": global_metrics.get('success_rate', 0),
                "slow_agents_count": len(slow_agents),
                "failing_agents_count": len(failing_agents),
                "total_requests": global_metrics.get('total_requests', 0),
                "uptime_seconds": global_metrics.get('uptime_seconds', 0)
            }
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "unhealthy",
            "message": str(e)
        }
