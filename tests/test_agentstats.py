#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List, Optional
import time
from enum import Enum

class AgentCapability(Enum):
    """Capacidades específicas que puede tener un agente"""
    DOCUMENT_SEARCH = "document_search"
    COMPARISON_ANALYSIS = "comparison_analysis"
    STATE_OF_ART = "state_of_art_synthesis"
    SYNTHESIS = "information_synthesis"
    REASONING = "multi_step_reasoning"
    ACADEMIC_ANALYSIS = "academic_analysis"
    LITERATURE_REVIEW = "literature_review"
    METHODOLOGY_EXTRACTION = "methodology_extraction"

@dataclass
class AgentStats:
    """
    Estadísticas de performance por agente
    Cumple con HU1-CA1.1: Métricas de performance por agente
    """
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    avg_response_time_ms: float = 0.0
    avg_confidence: float = 0.0
    last_error: Optional[str] = None
    last_error_timestamp: Optional[float] = None
    capabilities: List[AgentCapability] = field(default_factory=list)
    uptime_start: float = field(default_factory=time.time)
    
    @property
    def success_rate(self) -> float:
        """Calcula tasa de éxito"""
        if self.total_queries == 0:
            return 0.0
        return self.successful_queries / self.total_queries
    
    @property
    def error_rate(self) -> float:
        """Calcula tasa de error"""
        if self.total_queries == 0:
            return 0.0
        return self.failed_queries / self.total_queries
    
    @property
    def uptime_hours(self) -> float:
        """Calcula horas de uptime"""
        return (time.time() - self.uptime_start) / 3600
    
    def update_success(self, response_time_ms: float, confidence: float):
        """Actualiza estadísticas para consulta exitosa"""
        self.total_queries += 1
        self.successful_queries += 1
        
        # Actualizar promedio de tiempo de respuesta
        if self.total_queries == 1:
            self.avg_response_time_ms = response_time_ms
        else:
            total_time = self.avg_response_time_ms * (self.total_queries - 1)
            self.avg_response_time_ms = (total_time + response_time_ms) / self.total_queries
        
        # Actualizar promedio de confidence
        if self.total_queries == 1:
            self.avg_confidence = confidence
        else:
            total_conf = self.avg_confidence * (self.total_queries - 1)
            self.avg_confidence = (total_conf + confidence) / self.total_queries
    
    def update_failure(self, error_message: str):
        """Actualiza estadísticas para consulta fallida"""
        self.total_queries += 1
        self.failed_queries += 1
        self.last_error = error_message
        self.last_error_timestamp = time.time()

if __name__ == "__main__":
    # Test básico
    stats = AgentStats()
    print(f"AgentStats created: {stats}")
    
    stats.update_success(100.0, 0.8)
    print(f"After success: queries={stats.total_queries}, success_rate={stats.success_rate}")
    
    stats.update_failure("Test error")
    print(f"After failure: queries={stats.total_queries}, error_rate={stats.error_rate}")
    
    print("AgentStats test completed successfully!")