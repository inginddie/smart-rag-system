# -*- coding: utf-8 -*-
"""
Academic Quality Validation System
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Tuple

from src.chains.prompt_templates import TemplateMetadata
from src.utils.intent_detector import IntentType
from src.utils.logger import setup_logger

logger = setup_logger()


@dataclass
class QualityScore:
    """Score de calidad académica"""

    total_score: float
    section_scores: Dict[str, float]
    quality_criteria: Dict[str, float]
    issues_found: List[str]
    recommendations: List[str]


class QualityLevel(Enum):
    """Niveles de calidad académica"""

    EXCELLENT = "excellent"  # 0.9+
    GOOD = "good"  # 0.7-0.89
    ACCEPTABLE = "acceptable"  # 0.5-0.69
    POOR = "poor"  # <0.5


class AcademicQualityValidator:
    """Validador de calidad académica para responses"""

    def __init__(self):
        self.section_weights = {
            "structure": 0.25,
            "citations": 0.25,
            "content_depth": 0.20,
            "academic_rigor": 0.15,
            "clarity": 0.15,
        }

        self.citation_patterns = [
            r"\([^)]+,\s*\d{4}\)",  # (Author, 2024)
            r"\[[^\]]+\]",  # [Title]
            r"\b(?:et\s+al\.)",  # et al.
            r"\b\d{4}\b",  # Years
        ]

    def validate_response(
        self,
        response: str,
        intent_type: IntentType,
        template_metadata: TemplateMetadata,
    ) -> QualityScore:
        """Valida calidad académica de una respuesta"""

        # Análisis por criterios
        structure_score = self._assess_structure(response, template_metadata)
        citation_score = self._assess_citations(response)
        depth_score = self._assess_content_depth(response, intent_type)
        rigor_score = self._assess_academic_rigor(response)
        clarity_score = self._assess_clarity(response)

        # Score total ponderado
        total_score = (
            structure_score * self.section_weights["structure"]
            + citation_score * self.section_weights["citations"]
            + depth_score * self.section_weights["content_depth"]
            + rigor_score * self.section_weights["academic_rigor"]
            + clarity_score * self.section_weights["clarity"]
        )

        # Identificar issues y recommendations
        issues = self._identify_issues(response, template_metadata)
        recommendations = self._generate_recommendations(
            {
                "structure": structure_score,
                "citations": citation_score,
                "depth": depth_score,
                "rigor": rigor_score,
                "clarity": clarity_score,
            }
        )

        return QualityScore(
            total_score=round(total_score, 3),
            section_scores={
                "structure": round(structure_score, 3),
                "citations": round(citation_score, 3),
                "content_depth": round(depth_score, 3),
                "academic_rigor": round(rigor_score, 3),
                "clarity": round(clarity_score, 3),
            },
            quality_criteria={
                criterion: 1.0 for criterion in template_metadata.quality_criteria
            },
            issues_found=issues,
            recommendations=recommendations,
        )

    def _assess_structure(self, response: str, metadata: TemplateMetadata) -> float:
        """Evalúa estructura de la respuesta"""
        score = 0.0
        total_checks = len(metadata.sections)

        if total_checks == 0:
            return 1.0

        # Verificar presencia de secciones esperadas
        for section in metadata.sections:
            section_patterns = [
                section.lower(),
                section.replace(" ", "").lower(),
                re.sub(r"[^a-z]", "", section.lower()),
            ]

            if any(pattern in response.lower() for pattern in section_patterns):
                score += 1.0

        structure_score = score / total_checks

        # Bonus por organización clara
        if self._has_clear_organization(response):
            structure_score = min(1.0, structure_score + 0.1)

        return structure_score

    def _assess_citations(self, response: str) -> float:
        """Evalúa calidad de citas académicas"""
        citation_count = 0

        for pattern in self.citation_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            citation_count += len(matches)

        # Score basado en densidad de citas
        word_count = len(response.split())
        if word_count == 0:
            return 0.0

        citation_density = citation_count / (word_count / 100)  # Citas per 100 words

        # Scoring curve
        if citation_density >= 2.0:
            return 1.0
        elif citation_density >= 1.0:
            return 0.8
        elif citation_density >= 0.5:
            return 0.6
        elif citation_density > 0:
            return 0.4
        else:
            return 0.0

    def _assess_content_depth(self, response: str, intent_type: IntentType) -> float:
        """Evalúa profundidad del contenido"""
        depth_indicators = {
            IntentType.DEFINITION: [
                "características",
                "atributos",
                "propiedades",
                "definición",
                "concepto",
                "término",
            ],
            IntentType.COMPARISON: [
                "ventajas",
                "desventajas",
                "diferencias",
                "similitudes",
                "comparación",
                "contraste",
                "versus",
            ],
            IntentType.STATE_OF_ART: [
                "tendencias",
                "enfoques",
                "métodos",
                "estado actual",
                "evolución",
                "desarrollo",
            ],
            IntentType.GAP_ANALYSIS: [
                "limitaciones",
                "gaps",
                "oportunidades",
                "futuro",
                "investigación",
                "challenges",
            ],
        }

        indicators = depth_indicators.get(intent_type, [])
        if not indicators:
            return 0.7  # Default score

        found_indicators = sum(
            1 for indicator in indicators if indicator in response.lower()
        )

        depth_score = min(1.0, found_indicators / len(indicators))

        # Bonus por longitud apropiada
        word_count = len(response.split())
        if 200 <= word_count <= 800:
            depth_score = min(1.0, depth_score + 0.1)

        return depth_score

    def _assess_academic_rigor(self, response: str) -> float:
        """Evalúa rigor académico"""
        rigor_indicators = [
            r"\b(?:study|research|investigation|analysis)\b",
            r"\b(?:methodology|approach|method)\b",
            r"\b(?:evidence|data|results|findings)\b",
            r"\b(?:however|nevertheless|furthermore|moreover)\b",
            r"\b(?:suggest|indicate|demonstrate|show)\b",
        ]

        found_indicators = 0
        for pattern in rigor_indicators:
            if re.search(pattern, response, re.IGNORECASE):
                found_indicators += 1

        rigor_score = min(1.0, found_indicators / len(rigor_indicators))

        # Penalty por language informal
        informal_patterns = [
            r"\b(?:awesome|cool|amazing|super)\b",
            r"\b(?:gonna|wanna|kinda)\b",
        ]

        for pattern in informal_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                rigor_score *= 0.8

        return rigor_score

    def _assess_clarity(self, response: str) -> float:
        """Evalúa claridad de la respuesta"""
        # Métricas de legibilidad básicas
        sentences = response.split(".")
        words = response.split()

        if len(sentences) == 0 or len(words) == 0:
            return 0.0

        avg_sentence_length = len(words) / len(sentences)

        # Optimal sentence length: 15-25 words
        if 15 <= avg_sentence_length <= 25:
            length_score = 1.0
        elif 10 <= avg_sentence_length < 15 or 25 < avg_sentence_length <= 30:
            length_score = 0.8
        else:
            length_score = 0.6

        # Check for transition words
        transition_words = [
            "además",
            "sin embargo",
            "por otro lado",
            "en consecuencia",
            "furthermore",
            "however",
            "moreover",
            "therefore",
        ]

        has_transitions = any(word in response.lower() for word in transition_words)
        transition_score = 1.0 if has_transitions else 0.7

        clarity_score = (length_score + transition_score) / 2
        return clarity_score

    def _has_clear_organization(self, response: str) -> bool:
        """Verifica si la respuesta tiene organización clara"""
        organization_indicators = [
            r"\*\*\d+\.",  # **1.
            r"\n\d+\.",  # \n1.
            r"\*\*[A-Z][^*]+\*\*",  # **Section**
            r"#{1,3}\s",  # Headers
        ]

        found_patterns = sum(
            1 for pattern in organization_indicators if re.search(pattern, response)
        )

        return found_patterns >= 2

    def _identify_issues(self, response: str, metadata: TemplateMetadata) -> List[str]:
        """Identifica issues específicos en la respuesta"""
        issues = []

        # Issue: Missing citations
        if not any(re.search(pattern, response) for pattern in self.citation_patterns):
            issues.append(
                "No citations found - academic responses should include references"
            )

        # Issue: Too short
        if len(response.split()) < 100:
            issues.append("Response too brief for academic depth")

        # Issue: Missing expected sections
        missing_sections = []
        for section in metadata.sections:
            if section.lower() not in response.lower():
                missing_sections.append(section)

        if missing_sections:
            issues.append(
                f"Missing expected sections: {', '.join(missing_sections[:2])}"
            )

        return issues

    def _generate_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """Genera recomendaciones para mejorar calidad"""
        recommendations = []

        if scores["citations"] < 0.6:
            recommendations.append("Add more academic citations and references")

        if scores["structure"] < 0.7:
            recommendations.append("Improve response structure with clear sections")

        if scores["depth"] < 0.6:
            recommendations.append("Provide more detailed analysis and examples")

        if scores["rigor"] < 0.7:
            recommendations.append("Use more formal academic language and terminology")

        if scores["clarity"] < 0.7:
            recommendations.append(
                "Improve clarity with better transitions and sentence structure"
            )

        return recommendations

    def get_quality_level(self, score: float) -> QualityLevel:
        """Determina nivel de calidad basado en score"""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.7:
            return QualityLevel.GOOD
        elif score >= 0.5:
            return QualityLevel.ACCEPTABLE
        else:
            return QualityLevel.POOR


# Instancia global
academic_quality_validator = AcademicQualityValidator()
