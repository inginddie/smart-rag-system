#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgentSelector - Selección inteligente de agentes
Implementa CA5.1: Selección Inteligente de Agentes
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime

from src.agents.base.agent import BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class SelectionDecision:
    """Decisión de selección de agente"""
    selected_agent: Optional[BaseAgent]
    confidence: float
    reasoning: str
    all_scores: Dict[str, float]
    timestamp: str
    should_use_fallback: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la decisión a diccionario"""
        return {
            'selected_agent': self.selected_agent.name if self.selected_agent else None,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'all_scores': self.all_scores,
            'timestamp': self.timestamp,
            'should_use_fallback': self.should_use_fallback
        }


class AgentSelector:
    """
    Selector inteligente de agentes
    
    Responsabilidades:
    - Evaluar confidence score de todos los agentes
    - Seleccionar el agente más apropiado
    - Decidir cuándo usar fallback a RAG clásico
    - Registrar decisiones para observabilidad
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        """
        Inicializa el selector de agentes
        
        Args:
            confidence_threshold: Umbral mínimo de confianza para usar un agente
        """
        self.confidence_threshold = confidence_threshold
        self._decision_history: List[SelectionDecision] = []
        self._metrics = {
            'total_selections': 0,
            'agent_selections': 0,
            'fallback_selections': 0,
            'avg_confidence': 0.0
        }
        
        logger.info(f"AgentSelector initialized with threshold={confidence_threshold}")
    
    def select_agent(
        self,
        query: str,
        available_agents: List[BaseAgent],
        context: Optional[Dict[str, Any]] = None
    ) -> SelectionDecision:
        """
        Selecciona el mejor agente para una consulta
        
        Args:
            query: Consulta del usuario
            available_agents: Lista de agentes disponibles
            context: Contexto adicional
        
        Returns:
            SelectionDecision con el agente seleccionado y metadata
        """
        logger.info(f"Selecting agent for query: {query[:50]}...")
        
        # Evaluar todos los agentes
        scores = self._evaluate_all_agents(query, available_agents, context)
        
        # Seleccionar el mejor
        decision = self._make_selection_decision(query, scores, available_agents)
        
        # Registrar decisión
        self._record_decision(decision)
        
        # Actualizar métricas
        self._update_metrics(decision)
        
        logger.info(
            f"Selected: {decision.selected_agent.name if decision.selected_agent else 'FALLBACK'} "
            f"(confidence={decision.confidence:.2f})"
        )
        
        return decision
    
    def _evaluate_all_agents(
        self,
        query: str,
        agents: List[BaseAgent],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Evalúa el confidence score de todos los agentes
        
        Args:
            query: Consulta del usuario
            agents: Lista de agentes a evaluar
            context: Contexto adicional
        
        Returns:
            Diccionario con scores por agente
        """
        scores = {}
        
        for agent in agents:
            try:
                score = agent.can_handle_query(query, context)
                scores[agent.name] = score
                logger.debug(f"Agent {agent.name}: score={score:.2f}")
            except Exception as e:
                logger.error(f"Error evaluating agent {agent.name}: {e}")
                scores[agent.name] = 0.0
        
        return scores
    
    def _make_selection_decision(
        self,
        query: str,
        scores: Dict[str, float],
        agents: List[BaseAgent]
    ) -> SelectionDecision:
        """
        Toma la decisión de selección basada en los scores
        
        Args:
            query: Consulta del usuario
            scores: Scores de cada agente
            agents: Lista de agentes disponibles
        
        Returns:
            SelectionDecision con el resultado
        """
        # Encontrar el agente con mayor score
        if not scores:
            return self._create_fallback_decision(
                query, scores, "No agents available"
            )
        
        best_agent_name = max(scores, key=scores.get)
        best_score = scores[best_agent_name]
        
        # Verificar si supera el threshold
        if best_score < self.confidence_threshold:
            reasoning = (
                f"Best agent '{best_agent_name}' score ({best_score:.2f}) "
                f"below threshold ({self.confidence_threshold})"
            )
            return self._create_fallback_decision(query, scores, reasoning)
        
        # Seleccionar el agente
        selected_agent = next(
            (agent for agent in agents if agent.name == best_agent_name),
            None
        )
        
        if selected_agent is None:
            return self._create_fallback_decision(
                query, scores, f"Agent '{best_agent_name}' not found"
            )
        
        reasoning = (
            f"Selected '{best_agent_name}' with highest confidence "
            f"({best_score:.2f}) above threshold ({self.confidence_threshold})"
        )
        
        return SelectionDecision(
            selected_agent=selected_agent,
            confidence=best_score,
            reasoning=reasoning,
            all_scores=scores,
            timestamp=datetime.utcnow().isoformat(),
            should_use_fallback=False
        )
    
    def _create_fallback_decision(
        self,
        query: str,
        scores: Dict[str, float],
        reasoning: str
    ) -> SelectionDecision:
        """
        Crea una decisión de fallback
        
        Args:
            query: Consulta del usuario
            scores: Scores de agentes
            reasoning: Razón del fallback
        
        Returns:
            SelectionDecision indicando fallback
        """
        return SelectionDecision(
            selected_agent=None,
            confidence=0.0,
            reasoning=f"Fallback to classic RAG: {reasoning}",
            all_scores=scores,
            timestamp=datetime.utcnow().isoformat(),
            should_use_fallback=True
        )
    
    def _record_decision(self, decision: SelectionDecision) -> None:
        """Registra la decisión en el historial"""
        self._decision_history.append(decision)
        
        # Mantener solo las últimas 100 decisiones
        if len(self._decision_history) > 100:
            self._decision_history = self._decision_history[-100:]
    
    def _update_metrics(self, decision: SelectionDecision) -> None:
        """Actualiza las métricas del selector"""
        self._metrics['total_selections'] += 1
        
        if decision.should_use_fallback:
            self._metrics['fallback_selections'] += 1
        else:
            self._metrics['agent_selections'] += 1
        
        # Actualizar promedio de confianza
        total = self._metrics['total_selections']
        current_avg = self._metrics['avg_confidence']
        self._metrics['avg_confidence'] = (
            (current_avg * (total - 1) + decision.confidence) / total
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene métricas del selector
        
        Returns:
            Diccionario con métricas
        """
        total = self._metrics['total_selections']
        
        return {
            'total_selections': total,
            'agent_selections': self._metrics['agent_selections'],
            'fallback_selections': self._metrics['fallback_selections'],
            'agent_selection_rate': (
                self._metrics['agent_selections'] / total if total > 0 else 0.0
            ),
            'fallback_rate': (
                self._metrics['fallback_selections'] / total if total > 0 else 0.0
            ),
            'avg_confidence': self._metrics['avg_confidence'],
            'confidence_threshold': self.confidence_threshold
        }
    
    def get_recent_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las decisiones más recientes
        
        Args:
            limit: Número de decisiones a retornar
        
        Returns:
            Lista de decisiones en formato diccionario
        """
        recent = self._decision_history[-limit:]
        return [decision.to_dict() for decision in recent]
    
    def adjust_threshold(self, new_threshold: float) -> None:
        """
        Ajusta el umbral de confianza
        
        Args:
            new_threshold: Nuevo umbral (0.0 - 1.0)
        """
        if not 0.0 <= new_threshold <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {new_threshold}")
        
        old_threshold = self.confidence_threshold
        self.confidence_threshold = new_threshold
        
        logger.info(f"Threshold adjusted: {old_threshold} -> {new_threshold}")
