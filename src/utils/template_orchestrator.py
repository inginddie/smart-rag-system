# -*- coding: utf-8 -*-
"""
Template Orchestrator - Coordinación inteligente de templates académicos
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from config.settings import settings
from src.chains.prompt_templates import (EnhancedPromptTemplateSelector,
                                         TemplateMetadata)
from src.utils.intent_detector import IntentResult, IntentType
from src.utils.logger import setup_logger

logger = setup_logger()


@dataclass
class TemplateSelectionResult:
    """Resultado de selección de template"""

    template_prompt: str
    template_metadata: TemplateMetadata
    selection_reason: str
    confidence_score: float
    fallback_used: bool
    processing_time_ms: float


class TemplateSelectionStrategy(Enum):
    """Estrategias de selección de template"""

    INTENT_BASED = "intent_based"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    HYBRID = "hybrid"
    FALLBACK = "fallback"


class TemplateOrchestrator:
    """Orchestrador central para template selection y aplicación"""

    def __init__(self):
        self.template_selector = EnhancedPromptTemplateSelector()
        self.selection_strategy = TemplateSelectionStrategy.HYBRID
        self.confidence_threshold = getattr(
            settings, "template_confidence_threshold", 0.7
        )

        self.selection_metrics = {
            "total_selections": 0,
            "successful_selections": 0,
            "fallback_uses": 0,
            "average_processing_time": 0.0,
        }

    def select_template(
        self,
        intent_result: IntentResult,
        user_expertise: str = "intermediate",
        query_complexity: float = 0.5,
        base_prompt: str = "",
    ) -> TemplateSelectionResult:
        """Selecciona template óptimo basado en múltiples factores"""
        start_time = time.perf_counter()

        try:
            strategy = self._determine_selection_strategy(
                intent_result, query_complexity
            )

            if strategy == TemplateSelectionStrategy.INTENT_BASED:
                result = self._select_by_intent(
                    intent_result, user_expertise, base_prompt
                )
            elif strategy == TemplateSelectionStrategy.CONFIDENCE_WEIGHTED:
                result = self._select_by_confidence(
                    intent_result, user_expertise, base_prompt
                )
            elif strategy == TemplateSelectionStrategy.HYBRID:
                result = self._select_hybrid(
                    intent_result, user_expertise, query_complexity, base_prompt
                )
            else:
                result = self._select_fallback(
                    intent_result, user_expertise, base_prompt
                )

            processing_time = (time.perf_counter() - start_time) * 1000
            result.processing_time_ms = processing_time

            self._update_metrics(result, processing_time)

            logger.debug(f"Template selected: {intent_result.intent_type.value}")
            return result

        except Exception as e:
            logger.error(f"Error in template selection: {e}")
            processing_time = (time.perf_counter() - start_time) * 1000
            return self._create_fallback_result(base_prompt, str(e), processing_time)

    def _determine_selection_strategy(
        self, intent_result: IntentResult, query_complexity: float
    ) -> TemplateSelectionStrategy:
        """Determina la estrategia óptima de selección"""
        if (
            intent_result.fallback_used
            or intent_result.intent_type == IntentType.UNKNOWN
        ):
            return TemplateSelectionStrategy.FALLBACK

        if intent_result.confidence >= 0.9:
            return TemplateSelectionStrategy.INTENT_BASED

        if (
            intent_result.confidence >= self.confidence_threshold
            and query_complexity > 0.6
        ):
            return TemplateSelectionStrategy.CONFIDENCE_WEIGHTED

        return TemplateSelectionStrategy.HYBRID

    def _select_by_intent(
        self, intent_result: IntentResult, user_expertise: str, base_prompt: str
    ) -> TemplateSelectionResult:
        """Selección directa basada en intent"""
        template_prompt = self.template_selector.select_template(
            intent_result.intent_type, base_prompt, user_expertise
        )

        template_metadata = self.template_selector.get_template_metadata(
            intent_result.intent_type
        )

        return TemplateSelectionResult(
            template_prompt=template_prompt,
            template_metadata=template_metadata,
            selection_reason=f"Direct intent selection: {intent_result.intent_type.value}",
            confidence_score=intent_result.confidence,
            fallback_used=False,
            processing_time_ms=0.0,
        )

    def _select_by_confidence(
        self, intent_result: IntentResult, user_expertise: str, base_prompt: str
    ) -> TemplateSelectionResult:
        """Selección ponderada por confidence"""
        if intent_result.confidence >= self.confidence_threshold:
            return self._select_by_intent(intent_result, user_expertise, base_prompt)

        adapted_prompt = self.template_selector._get_default_academic_template()
        if user_expertise != "intermediate":
            adapted_prompt = self.template_selector._adapt_template_for_expertise(
                adapted_prompt, user_expertise
            )

        return TemplateSelectionResult(
            template_prompt=adapted_prompt,
            template_metadata=self.template_selector.get_template_metadata(
                IntentType.UNKNOWN
            ),
            selection_reason=f"Low confidence ({intent_result.confidence:.2f}), using generic template",
            confidence_score=intent_result.confidence,
            fallback_used=True,
            processing_time_ms=0.0,
        )

    def _select_hybrid(
        self,
        intent_result: IntentResult,
        user_expertise: str,
        query_complexity: float,
        base_prompt: str,
    ) -> TemplateSelectionResult:
        """Selección híbrida considerando múltiples factores"""
        selection_score = self._calculate_hybrid_score(intent_result, query_complexity)
        adaptive_threshold = self.confidence_threshold * (1.0 - query_complexity * 0.2)

        if selection_score >= adaptive_threshold:
            result = self._select_by_intent(intent_result, user_expertise, base_prompt)
            result.selection_reason = f"Hybrid selection: score={selection_score:.2f}"
            return result
        else:
            result = self._select_by_confidence(
                intent_result, user_expertise, base_prompt
            )
            result.selection_reason = f"Hybrid fallback: score={selection_score:.2f}"
            return result

    def _calculate_hybrid_score(
        self, intent_result: IntentResult, query_complexity: float
    ) -> float:
        """Calcula score híbrido para selección"""
        base_score = intent_result.confidence

        if intent_result.processing_time_ms < 100:
            time_bonus = 0.1
        elif intent_result.processing_time_ms < 200:
            time_bonus = 0.05
        else:
            time_bonus = 0.0

        pattern_bonus = min(0.1, len(intent_result.matched_patterns) * 0.02)
        complexity_penalty = max(0.0, (query_complexity - 0.8) * 0.2)

        hybrid_score = base_score + time_bonus + pattern_bonus - complexity_penalty
        return max(0.0, min(1.0, hybrid_score))

    def _select_fallback(
        self, intent_result: IntentResult, user_expertise: str, base_prompt: str
    ) -> TemplateSelectionResult:
        """Selección de fallback cuando otras estrategias fallan"""
        fallback_prompt = (
            base_prompt
            if base_prompt
            else self.template_selector._get_default_academic_template()
        )

        if hasattr(self.template_selector, "_adapt_template_for_expertise"):
            fallback_prompt = self.template_selector._adapt_template_for_expertise(
                fallback_prompt, user_expertise
            )

        return TemplateSelectionResult(
            template_prompt=fallback_prompt,
            template_metadata=self.template_selector.get_template_metadata(
                IntentType.UNKNOWN
            ),
            selection_reason="Fallback strategy: intent detection failed",
            confidence_score=0.0,
            fallback_used=True,
            processing_time_ms=0.0,
        )

    def _create_fallback_result(
        self, base_prompt: str, error_reason: str, processing_time: float
    ) -> TemplateSelectionResult:
        """Crea resultado de fallback en caso de error"""
        return TemplateSelectionResult(
            template_prompt=base_prompt or "Responde de manera académica y rigurosa.",
            template_metadata=TemplateMetadata(
                sections=["Error Response"],
                citation_requirements={},
                quality_criteria=["Basic Response"],
                expected_length="medium",
                academic_rigor="basic",
            ),
            selection_reason=f"Error fallback: {error_reason}",
            confidence_score=0.0,
            fallback_used=True,
            processing_time_ms=processing_time,
        )

    def _update_metrics(self, result: TemplateSelectionResult, processing_time: float):
        """Actualiza métricas de performance"""
        self.selection_metrics["total_selections"] += 1

        if not result.fallback_used:
            self.selection_metrics["successful_selections"] += 1
        else:
            self.selection_metrics["fallback_uses"] += 1

        total = self.selection_metrics["total_selections"]
        current_avg = self.selection_metrics["average_processing_time"]
        self.selection_metrics["average_processing_time"] = (
            current_avg * (total - 1) + processing_time
        ) / total

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de performance del orchestrator"""
        total = self.selection_metrics["total_selections"]
        if total == 0:
            return {
                "status": "no_data",
                "message": "No template selections recorded yet",
            }

        success_rate = self.selection_metrics["successful_selections"] / total
        fallback_rate = self.selection_metrics["fallback_uses"] / total

        return {
            "total_selections": total,
            "success_rate": round(success_rate, 3),
            "fallback_rate": round(fallback_rate, 3),
            "average_processing_time_ms": round(
                self.selection_metrics["average_processing_time"], 2
            ),
            "strategy": self.selection_strategy.value,
            "confidence_threshold": self.confidence_threshold,
        }


# Instancia global
template_orchestrator = TemplateOrchestrator()
