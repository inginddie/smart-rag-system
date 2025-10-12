#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PerformanceMonitor - Monitor de performance para orquestación
Implementa CA5.3: Optimización de Performance
"""

from typing import Dict, List, Any, Optional
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Métrica de performance individual"""
    timestamp: float
    agent_name: str
    operation: str
    duration_ms: float
    success: bool
    error: Optional[str] = None


class PerformanceMonitor:
    """
    Monitor de performance para el sistema de orquestación
    
    Rastrea métricas detalladas de latencia, throughput y errores
    """
    
    def __init__(self, max_metrics: int = 1000):
        """
        Inicializa el monitor de performance
        
        Args:
            max_metrics: Máximo número de métricas a mantener en memoria
        """
        self.max_metrics = max_metrics
        self._metrics: deque = deque(maxlen=max_metrics)
        
        # Agregaciones por agente
        self._agent_metrics = defaultdict(lambda: {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_duration_ms': 0.0,
            'min_duration_ms': float('inf'),
            'max_duration_ms': 0.0,
            'recent_durations': deque(maxlen=100)
        })
        
        # Agregaciones por operación
        self._operation_metrics = defaultdict(lambda: {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_duration_ms': 0.0,
            'agents_used': set()
        })
        
        # Métricas globales
        self._global_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_duration_ms': 0.0,
            'start_time': time.time()
        }
        
        logger.info(f"PerformanceMonitor initialized (max_metrics={max_metrics})")
    
    def record_metric(
        self,
        agent_name: str,
        operation: str,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """
        Registra una métrica de performance
        
        Args:
            agent_name: Nombre del agente
            operation: Tipo de operación
            duration_ms: Duración en milisegundos
            success: Si la operación fue exitosa
            error: Descripción del error si falló
        """
        metric = PerformanceMetric(
            timestamp=time.time(),
            agent_name=agent_name,
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error=error
        )
        
        self._metrics.append(metric)
        self._update_aggregations(metric)
        
        logger.debug(
            f"Performance metric: {agent_name}.{operation} "
            f"{duration_ms:.1f}ms {'✓' if success else '✗'}"
        )
    
    def _update_aggregations(self, metric: PerformanceMetric):
        """Actualiza agregaciones con nueva métrica"""
        # Métricas por agente
        agent_stats = self._agent_metrics[metric.agent_name]
        agent_stats['total_requests'] += 1
        agent_stats['total_duration_ms'] += metric.duration_ms
        agent_stats['recent_durations'].append(metric.duration_ms)
        
        if metric.success:
            agent_stats['successful_requests'] += 1
        else:
            agent_stats['failed_requests'] += 1
        
        # Min/Max duration
        if metric.duration_ms < agent_stats['min_duration_ms']:
            agent_stats['min_duration_ms'] = metric.duration_ms
        if metric.duration_ms > agent_stats['max_duration_ms']:
            agent_stats['max_duration_ms'] = metric.duration_ms
        
        # Métricas por operación
        op_stats = self._operation_metrics[metric.operation]
        op_stats['total_requests'] += 1
        op_stats['total_duration_ms'] += metric.duration_ms
        op_stats['agents_used'].add(metric.agent_name)
        
        if metric.success:
            op_stats['successful_requests'] += 1
        else:
            op_stats['failed_requests'] += 1
        
        # Métricas globales
        self._global_metrics['total_requests'] += 1
        self._global_metrics['total_duration_ms'] += metric.duration_ms
        
        if metric.success:
            self._global_metrics['successful_requests'] += 1
        else:
            self._global_metrics['failed_requests'] += 1
    
    def get_agent_metrics(self, agent_name: str) -> Dict[str, Any]:
        """
        Obtiene métricas de un agente específico
        
        Args:
            agent_name: Nombre del agente
        
        Returns:
            Diccionario con métricas del agente
        """
        if agent_name not in self._agent_metrics:
            return {'agent_name': agent_name, 'no_data': True}
        
        stats = self._agent_metrics[agent_name]
        total = stats['total_requests']
        
        # Calcular percentiles de latencia
        durations = list(stats['recent_durations'])
        percentiles = self._calculate_percentiles(durations) if durations else {}
        
        return {
            'agent_name': agent_name,
            'total_requests': total,
            'successful_requests': stats['successful_requests'],
            'failed_requests': stats['failed_requests'],
            'success_rate': stats['successful_requests'] / total if total > 0 else 0.0,
            'failure_rate': stats['failed_requests'] / total if total > 0 else 0.0,
            'avg_duration_ms': stats['total_duration_ms'] / total if total > 0 else 0.0,
            'min_duration_ms': stats['min_duration_ms'] if stats['min_duration_ms'] != float('inf') else 0.0,
            'max_duration_ms': stats['max_duration_ms'],
            'recent_avg_duration_ms': sum(durations) / len(durations) if durations else 0.0,
            **percentiles
        }
    
    def get_operation_metrics(self, operation: str) -> Dict[str, Any]:
        """
        Obtiene métricas de una operación específica
        
        Args:
            operation: Nombre de la operación
        
        Returns:
            Diccionario con métricas de la operación
        """
        if operation not in self._operation_metrics:
            return {'operation': operation, 'no_data': True}
        
        stats = self._operation_metrics[operation]
        total = stats['total_requests']
        
        return {
            'operation': operation,
            'total_requests': total,
            'successful_requests': stats['successful_requests'],
            'failed_requests': stats['failed_requests'],
            'success_rate': stats['successful_requests'] / total if total > 0 else 0.0,
            'avg_duration_ms': stats['total_duration_ms'] / total if total > 0 else 0.0,
            'agents_used': len(stats['agents_used']),
            'agent_names': list(stats['agents_used'])
        }
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """
        Obtiene métricas globales del sistema
        
        Returns:
            Diccionario con métricas globales
        """
        total = self._global_metrics['total_requests']
        uptime = time.time() - self._global_metrics['start_time']
        
        return {
            'total_requests': total,
            'successful_requests': self._global_metrics['successful_requests'],
            'failed_requests': self._global_metrics['failed_requests'],
            'success_rate': self._global_metrics['successful_requests'] / total if total > 0 else 0.0,
            'failure_rate': self._global_metrics['failed_requests'] / total if total > 0 else 0.0,
            'avg_duration_ms': self._global_metrics['total_duration_ms'] / total if total > 0 else 0.0,
            'throughput_per_second': total / uptime if uptime > 0 else 0.0,
            'uptime_seconds': uptime,
            'total_agents': len(self._agent_metrics),
            'total_operations': len(self._operation_metrics)
        }
    
    def get_slow_agents(self, threshold_ms: float = 5000.0) -> List[Dict[str, Any]]:
        """
        Obtiene agentes que están siendo lentos
        
        Args:
            threshold_ms: Umbral de latencia en milisegundos
        
        Returns:
            Lista de agentes lentos con sus métricas
        """
        slow_agents = []
        
        for agent_name in self._agent_metrics:
            metrics = self.get_agent_metrics(agent_name)
            if metrics.get('avg_duration_ms', 0) > threshold_ms:
                slow_agents.append(metrics)
        
        # Ordenar por latencia promedio (peor primero)
        slow_agents.sort(key=lambda x: x.get('avg_duration_ms', 0), reverse=True)
        
        return slow_agents
    
    def get_failing_agents(self, threshold_rate: float = 0.1) -> List[Dict[str, Any]]:
        """
        Obtiene agentes con alta tasa de fallos
        
        Args:
            threshold_rate: Umbral de tasa de fallos (0.1 = 10%)
        
        Returns:
            Lista de agentes con fallos con sus métricas
        """
        failing_agents = []
        
        for agent_name in self._agent_metrics:
            metrics = self.get_agent_metrics(agent_name)
            if metrics.get('failure_rate', 0) > threshold_rate:
                failing_agents.append(metrics)
        
        # Ordenar por tasa de fallos (peor primero)
        failing_agents.sort(key=lambda x: x.get('failure_rate', 0), reverse=True)
        
        return failing_agents
    
    def _calculate_percentiles(self, durations: List[float]) -> Dict[str, float]:
        """
        Calcula percentiles de latencia
        
        Args:
            durations: Lista de duraciones
        
        Returns:
            Diccionario con percentiles
        """
        if not durations:
            return {}
        
        sorted_durations = sorted(durations)
        n = len(sorted_durations)
        
        def percentile(p):
            k = (n - 1) * p / 100
            f = int(k)
            c = k - f
            if f + 1 < n:
                return sorted_durations[f] * (1 - c) + sorted_durations[f + 1] * c
            else:
                return sorted_durations[f]
        
        return {
            'p50_duration_ms': percentile(50),
            'p90_duration_ms': percentile(90),
            'p95_duration_ms': percentile(95),
            'p99_duration_ms': percentile(99)
        }
    
    def get_recent_metrics(self, minutes: int = 5) -> List[PerformanceMetric]:
        """
        Obtiene métricas recientes
        
        Args:
            minutes: Número de minutos hacia atrás
        
        Returns:
            Lista de métricas recientes
        """
        cutoff_time = time.time() - (minutes * 60)
        
        recent = []
        for metric in self._metrics:
            if metric.timestamp >= cutoff_time:
                recent.append(metric)
        
        return recent
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Genera un reporte completo de performance
        
        Returns:
            Diccionario con reporte completo
        """
        return {
            'global_metrics': self.get_global_metrics(),
            'agent_metrics': {
                agent: self.get_agent_metrics(agent)
                for agent in self._agent_metrics.keys()
            },
            'operation_metrics': {
                op: self.get_operation_metrics(op)
                for op in self._operation_metrics.keys()
            },
            'slow_agents': self.get_slow_agents(),
            'failing_agents': self.get_failing_agents(),
            'recent_metrics_count': len(self.get_recent_metrics()),
            'report_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def clear_metrics(self):
        """Limpia todas las métricas"""
        self._metrics.clear()
        self._agent_metrics.clear()
        self._operation_metrics.clear()
        self._global_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_duration_ms': 0.0,
            'start_time': time.time()
        }
        
        logger.info("PerformanceMonitor metrics cleared")
