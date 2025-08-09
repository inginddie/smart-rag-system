# -*- coding: utf-8 -*-
"""
Query Validator - Pre-processing validation and refinement suggestions
"""

import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set

from config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger()


class ValidationIssueType(Enum):
    """Types of validation issues"""

    TOO_VAGUE = "too_vague"
    TOO_GENERAL = "too_general"
    OUT_OF_DOMAIN = "out_of_domain"
    LACKS_CONTEXT = "lacks_context"
    SPELLING_ISSUES = "spelling_issues"


@dataclass
class ValidationIssue:
    """Individual validation issue"""

    issue_type: ValidationIssueType
    severity: int  # 1=low, 2=medium, 3=high
    message: str
    suggestion: Optional[str] = None


@dataclass
class RefinementSuggestion:
    """Query refinement suggestion"""

    improved_query: str
    reason: str
    category: str
    priority: int  # 1=high, 2=medium, 3=low


@dataclass
class ValidationResult:
    """Result of query validation"""

    is_valid: bool
    confidence: float
    issues: List[ValidationIssue]
    suggestions: List[RefinementSuggestion]
    requires_user_input: bool
    processing_time_ms: float


class QueryValidator:
    """Pre-processing validation and refinement suggestions"""

    def __init__(self):
        self.min_query_length = getattr(settings, "min_query_length", 3)
        self.domain_confidence_threshold = getattr(
            settings, "domain_confidence_threshold", 0.7
        )
        self.max_suggestions = getattr(settings, "max_suggestions", 3)

        # Academic domain keywords from corpus
        self.academic_keywords = self._load_academic_keywords()
        self.general_terms = self._load_general_terms()
        self.domain_indicators = self._load_domain_indicators()

    def _load_academic_keywords(self) -> Set[str]:
        """Load academic keywords from settings and extend with domain-specific terms"""
        base_keywords = set(
            getattr(
                settings,
                "academic_domain_keywords",
                [
                    "machine learning",
                    "AI",
                    "requirements",
                    "software",
                    "algorithm",
                    "methodology",
                    "framework",
                    "analysis",
                ],
            )
        )

        # Extended academic vocabulary
        extended_keywords = {
            "artificial intelligence",
            "deep learning",
            "neural networks",
            "natural language processing",
            "nlp",
            "ml",
            "ai",
            "requirements engineering",
            "software engineering",
            "user stories",
            "acceptance criteria",
            "functional requirements",
            "non-functional requirements",
            "software quality",
            "testing",
            "validation",
            "verification",
            "agile",
            "scrum",
            "methodology",
            "framework",
            "algorithm",
            "model",
            "approach",
            "technique",
            "evaluation",
            "metrics",
            "performance",
            "accuracy",
            "implementation",
            "development",
            "automation",
        }

        return base_keywords.union(extended_keywords)

    def _load_general_terms(self) -> Set[str]:
        """Terms that are too general for academic queries"""
        return {
            "methods",
            "techniques",
            "approaches",
            "ways",
            "tools",
            "systems",
            "solutions",
            "processes",
            "strategies",
            "concepts",
            "ideas",
            "things",
            "stuff",
            "ways",
        }

    def _load_domain_indicators(self) -> Set[str]:
        """Terms that indicate academic/technical domain"""
        return {
            "research",
            "study",
            "analysis",
            "evaluation",
            "assessment",
            "comparison",
            "review",
            "survey",
            "investigation",
            "experiment",
            "empirical",
            "theoretical",
            "practical",
            "methodology",
            "framework",
            "model",
            "algorithm",
            "implementation",
            "validation",
            "verification",
        }

    def validate_query(self, query: str) -> ValidationResult:
        """
        Comprehensive query validation with suggestions

        Args:
            query: User's input query

        Returns:
            ValidationResult with issues and suggestions
        """
        start_time = time.perf_counter()

        try:
            query = query.strip()
            issues = []
            suggestions = []

            # 1. Check if query is too short/vague
            vague_issues = self._check_vague_query(query)
            issues.extend(vague_issues)

            # 2. Check for overly general terms
            general_issues = self._check_general_terms(query)
            issues.extend(general_issues)

            # 3. Check domain relevance
            domain_issues = self._check_domain_relevance(query)
            issues.extend(domain_issues)

            # 4. Check for lack of context
            context_issues = self._check_missing_context(query)
            issues.extend(context_issues)

            # Generate suggestions based on issues
            if issues:
                suggestions = self._generate_suggestions(query, issues)

            # Determine if user input is required
            high_severity_issues = [i for i in issues if i.severity >= 2]
            requires_user_input = len(high_severity_issues) > 0

            # Calculate overall validation confidence
            confidence = self._calculate_confidence(query, issues)
            is_valid = (
                confidence >= self.domain_confidence_threshold
                and not requires_user_input
            )

            processing_time = (time.perf_counter() - start_time) * 1000

            logger.debug(
                f"Query validation completed: valid={is_valid}, issues={len(issues)}, time={processing_time:.1f}ms"
            )

            return ValidationResult(
                is_valid=is_valid,
                confidence=confidence,
                issues=issues,
                suggestions=suggestions[: self.max_suggestions],
                requires_user_input=requires_user_input,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Error in query validation: {e}")
            processing_time = (time.perf_counter() - start_time) * 1000

            return ValidationResult(
                is_valid=True,  # Fail open
                confidence=0.5,
                issues=[],
                suggestions=[],
                requires_user_input=False,
                processing_time_ms=processing_time,
            )

    def _check_vague_query(self, query: str) -> List[ValidationIssue]:
        """Check if query is too vague (too short or single words)"""
        issues = []
        words = query.split()
        meaningful_words = [
            w
            for w in words
            if len(w) > 2
            and w.lower()
            not in {
                "the",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
            }
        ]

        # Single word queries (especially acronyms)
        if len(meaningful_words) <= 1:
            if query.lower() in ["ia", "ai", "ml", "nlp", "dl"]:
                issues.append(
                    ValidationIssue(
                        issue_type=ValidationIssueType.TOO_VAGUE,
                        severity=3,
                        message=f"La consulta '{query}' es muy vaga. Necesita más contexto específico.",
                        suggestion="Especifica el contexto: '¿Qué aplicaciones de {query} existen para historias de usuario?'",
                    )
                )

        # Very short queries
        elif len(meaningful_words) < self.min_query_length:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.TOO_VAGUE,
                    severity=2,
                    message="La consulta es muy corta. Agrega más contexto para mejores resultados.",
                    suggestion="Incluye contexto específico: propósito, dominio o aplicación",
                )
            )

        return issues

    def _check_general_terms(self, query: str) -> List[ValidationIssue]:
        """Check for overly general terms"""
        issues = []
        query_lower = query.lower()

        found_general = [term for term in self.general_terms if term in query_lower]

        if found_general and len(query.split()) <= 5:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.TOO_GENERAL,
                    severity=2,
                    message=f"Términos muy generales detectados: {', '.join(found_general)}",
                    suggestion="Usa términos más específicos del dominio académico",
                )
            )

        return issues

    def _check_domain_relevance(self, query: str) -> List[ValidationIssue]:
        """Check if query is relevant to academic corpus domain"""
        issues = []
        query_lower = query.lower()

        # Check for academic/technical indicators
        has_academic_terms = any(
            keyword in query_lower for keyword in self.academic_keywords
        )
        has_domain_indicators = any(
            indicator in query_lower for indicator in self.domain_indicators
        )

        # Simple heuristics for out-of-domain detection
        out_of_domain_indicators = [
            "recipe",
            "cooking",
            "food",
            "restaurant",
            "weather",
            "sports",
            "entertainment",
            "movie",
            "music",
            "travel",
            "fashion",
            "medicina",
            "doctor",
            "salud",
            "enfermedad",
        ]

        has_out_of_domain = any(
            indicator in query_lower for indicator in out_of_domain_indicators
        )

        if has_out_of_domain and not has_academic_terms:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.OUT_OF_DOMAIN,
                    severity=3,
                    message="Esta consulta parece estar fuera del dominio académico del corpus (IA/Software/Requirements).",
                    suggestion="Reformula hacia temas de inteligencia artificial, ingeniería de software o análisis de requirements",
                )
            )
        elif (
            not has_academic_terms
            and not has_domain_indicators
            and len(query.split()) > 3
        ):
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.OUT_OF_DOMAIN,
                    severity=1,
                    message="La consulta podría beneficiarse de terminología más académica/técnica.",
                    suggestion="Considera incluir términos como: machine learning, AI, requirements, software engineering",
                )
            )

        return issues

    def _check_missing_context(self, query: str) -> List[ValidationIssue]:
        """Check if query lacks academic context"""
        issues = []
        query_lower = query.lower()

        # Patterns that indicate need for context
        comparative_without_context = bool(
            re.search(r"\b(compar|vs|versus|diferencia)\b", query_lower)
        )
        definition_without_scope = bool(
            re.search(r"\b(qué es|what is|define)\b", query_lower)
        )

        if (
            comparative_without_context
            and "para" not in query_lower
            and "in" not in query_lower
        ):
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.LACKS_CONTEXT,
                    severity=2,
                    message="Comparación sin contexto específico detectada.",
                    suggestion="Agrega contexto: 'para historias de usuario', 'en requirements engineering', etc.",
                )
            )

        if definition_without_scope and len(query.split()) <= 4:
            issues.append(
                ValidationIssue(
                    issue_type=ValidationIssueType.LACKS_CONTEXT,
                    severity=1,
                    message="Definición sin contexto de aplicación.",
                    suggestion="Especifica el dominio: 'en el contexto de requirements engineering'",
                )
            )

        return issues

    def _generate_suggestions(
        self, query: str, issues: List[ValidationIssue]
    ) -> List[RefinementSuggestion]:
        """Generate specific refinement suggestions based on issues"""
        suggestions = []
        query_lower = query.lower()

        # Handle vague queries
        vague_issues = [
            i for i in issues if i.issue_type == ValidationIssueType.TOO_VAGUE
        ]
        if vague_issues:
            if query_lower in ["ia", "ai"]:
                suggestions.append(
                    RefinementSuggestion(
                        improved_query="¿Qué técnicas de inteligencia artificial se usan para análisis de historias de usuario?",
                        reason="Agrega contexto específico y propósito académico",
                        category="specificity",
                        priority=1,
                    )
                )
                suggestions.append(
                    RefinementSuggestion(
                        improved_query="¿Cuáles son las aplicaciones de IA en requirements engineering?",
                        reason="Enfoca en dominio académico específico",
                        category="context",
                        priority=1,
                    )
                )
            elif query_lower in ["ml", "machine learning"]:
                suggestions.append(
                    RefinementSuggestion(
                        improved_query="¿Qué algoritmos de machine learning se aplican para automatizar historias de usuario?",
                        reason="Especifica aplicación práctica en el dominio",
                        category="application",
                        priority=1,
                    )
                )

        # Handle general terms
        general_issues = [
            i for i in issues if i.issue_type == ValidationIssueType.TOO_GENERAL
        ]
        if general_issues and "métodos" in query_lower:
            suggestions.append(
                RefinementSuggestion(
                    improved_query=query.replace(
                        "métodos", "técnicas de machine learning"
                    ).replace("methods", "ML techniques"),
                    reason="Reemplaza términos generales por específicos",
                    category="terminology",
                    priority=2,
                )
            )

        # Handle missing context
        context_issues = [
            i for i in issues if i.issue_type == ValidationIssueType.LACKS_CONTEXT
        ]
        if context_issues:
            if "compar" in query_lower and "para" not in query_lower:
                suggestions.append(
                    RefinementSuggestion(
                        improved_query=f"{query} para análisis de requirements",
                        reason="Agrega contexto de aplicación específico",
                        category="context",
                        priority=2,
                    )
                )

        return suggestions

    def _calculate_confidence(self, query: str, issues: List[ValidationIssue]) -> float:
        """Calculate overall confidence in query quality"""
        base_confidence = 1.0

        # Reduce confidence based on issue severity
        for issue in issues:
            if issue.severity == 3:
                base_confidence -= 0.3
            elif issue.severity == 2:
                base_confidence -= 0.2
            elif issue.severity == 1:
                base_confidence -= 0.1

        # Bonus for academic terms
        query_lower = query.lower()
        academic_bonus = min(
            0.2, len([kw for kw in self.academic_keywords if kw in query_lower]) * 0.05
        )

        # Bonus for appropriate length
        word_count = len(query.split())
        if 6 <= word_count <= 20:
            length_bonus = 0.1
        else:
            length_bonus = 0.0

        final_confidence = max(
            0.0, min(1.0, base_confidence + academic_bonus + length_bonus)
        )
        return final_confidence

    def get_domain_suggestions(self, query: str) -> List[str]:
        """Get domain-specific term suggestions based on corpus"""
        query_lower = query.lower()
        suggestions = []

        # Map general terms to specific academic terms
        term_mapping = {
            "methods": [
                "machine learning techniques",
                "algorithmic approaches",
                "computational methods",
            ],
            "tools": ["frameworks", "libraries", "development environments"],
            "techniques": ["algorithms", "methodologies", "approaches"],
            "systems": ["architectures", "frameworks", "platforms"],
            "analysis": ["evaluation", "assessment", "validation"],
        }

        for general_term, specific_terms in term_mapping.items():
            if general_term in query_lower:
                suggestions.extend(specific_terms)

        return suggestions[:5]


# Global instance
query_validator = QueryValidator()
