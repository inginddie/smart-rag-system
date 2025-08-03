# -*- coding: utf-8 -*-
"""
Query Preprocessing & Validation System - HU5
"""

import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.utils.logger import setup_logger

logger = setup_logger()


class ValidationIssue(Enum):
    """Tipos de issues de validación"""
    TOO_VAGUE = "too_vague"
    OUT_OF_DOMAIN = "out_of_domain" 
    TOO_GENERAL = "too_general"
    MISSING_CONTEXT = "missing_context"


@dataclass
class RefinementSuggestion:
    """Sugerencia de refinamiento"""
    refined_query: str
    reason: str
    category: str
    priority: int  # 1=high, 2=medium, 3=low


@dataclass
class ValidationResult:
    """Resultado de validación de consulta"""
    is_valid: bool
    confidence: float
    issues: List[ValidationIssue]
    suggestions: List[RefinementSuggestion]
    requires_user_input: bool
    processing_time_ms: float


class QueryValidator:
    """Sistema de validación y preprocessamiento de consultas"""
    
    def __init__(self):
        self.min_query_length = 3
        self.domain_keywords = self._load_domain_keywords()
        self.vague_patterns = [
            r'^\s*\b(ia|ai|ml|nlp|dl)\s*$',
            r'^\s*\b(machine learning|deep learning)\s*$',
            r'^\s*\b(métodos|técnicas|algorithms?)\s*$'
        ]
        
    def validate_query(self, query: str) -> ValidationResult:
        """Valida consulta y genera sugerencias si es necesario"""
        start_time = time.perf_counter()
        
        try:
            issues = []
            suggestions = []
            
            # Check 1: Query muy vaga
            if self._is_too_vague(query):
                issues.append(ValidationIssue.TOO_VAGUE)
                suggestions.extend(self._generate_vague_suggestions(query))
            
            # Check 2: Términos muy generales
            if self._has_general_terms(query):
                issues.append(ValidationIssue.TOO_GENERAL)
                suggestions.extend(self._generate_specificity_suggestions(query))
            
            # Check 3: Fuera de dominio académico
            if self._is_out_of_domain(query):
                issues.append(ValidationIssue.OUT_OF_DOMAIN)
                suggestions.extend(self._generate_domain_suggestions(query))
            
            # Determinar si necesita input del usuario
            requires_input = len(issues) > 0 and any(
                issue in [ValidationIssue.TOO_VAGUE, ValidationIssue.OUT_OF_DOMAIN] 
                for issue in issues
            )
            
            # Calcular confidence
            confidence = self._calculate_confidence(query, issues)
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return ValidationResult(
                is_valid=len(issues) == 0,
                confidence=confidence,
                issues=issues,
                suggestions=suggestions[:3],  # Max 3 suggestions
                requires_user_input=requires_input,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in query validation: {e}")
            processing_time = (time.perf_counter() - start_time) * 1000
            
            # Fallback gracioso
            return ValidationResult(
                is_valid=True,  # Allow query to proceed
                confidence=0.5,
                issues=[],
                suggestions=[],
                requires_user_input=False,
                processing_time_ms=processing_time
            )
    
    def _is_too_vague(self, query: str) -> bool:
        """Detecta consultas demasiado vagas"""
        query_clean = query.strip().lower()
        
        # Check patterns
        for pattern in self.vague_patterns:
            if re.match(pattern, query_clean, re.IGNORECASE):
                return True
        
        # Check word count
        words = [w for w in query_clean.split() if len(w) > 2]
        return len(words) < self.min_query_length
    
    def _has_general_terms(self, query: str) -> bool:
        """Detecta términos muy generales que necesitan contexto"""
        general_terms = [
            "métodos", "técnicas", "approaches", "methods", 
            "algorithms", "algoritmos", "herramientas", "tools"
        ]
        
        query_lower = query.lower()
        return any(term in query_lower for term in general_terms) and len(query.split()) < 8
    
    def _is_out_of_domain(self, query: str) -> bool:
        """Detecta consultas fuera del dominio académico"""
        query_lower = query.lower()
        
        # Check for domain keywords
        domain_match = any(keyword in query_lower for keyword in self.domain_keywords)
        
        # Check for non-academic terms
        non_academic_terms = [
            "recetas", "cocina", "deportes", "música", "películas",
            "weather", "clima", "noticias", "news", "stocks"
        ]
        
        non_academic_match = any(term in query_lower for term in non_academic_terms)
        
        return non_academic_match or (not domain_match and len(query.split()) > 3)
    
    def _generate_vague_suggestions(self, query: str) -> List[RefinementSuggestion]:
        """Genera sugerencias para consultas vagas"""
        query_lower = query.lower().strip()
        suggestions = []
        
        if "ia" in query_lower or "ai" in query_lower:
            suggestions.extend([
                RefinementSuggestion(
                    refined_query="¿Qué técnicas de IA se usan para análisis de historias de usuario?",
                    reason="Especifica aplicación de IA",
                    category="specificity",
                    priority=1
                ),
                RefinementSuggestion(
                    refined_query="¿Cuáles son los algoritmos de IA más efectivos para requirements engineering?",
                    reason="Agrega contexto académico",
                    category="context",
                    priority=2
                )
            ])
        
        elif "ml" in query_lower or "machine learning" in query_lower:
            suggestions.extend([
                RefinementSuggestion(
                    refined_query="¿Cómo se aplica machine learning a la mejora de historias de usuario?",
                    reason="Especifica aplicación",
                    category="application",
                    priority=1
                ),
                RefinementSuggestion(
                    refined_query="Compara técnicas de machine learning supervisado vs no supervisado para requirements",
                    reason="Estructura comparativa",
                    category="structure",
                    priority=2
                )
            ])
        
        return suggestions
    
    def _generate_specificity_suggestions(self, query: str) -> List[RefinementSuggestion]:
        """Genera sugerencias para agregar especificidad"""
        suggestions = []
        
        if "métodos" in query.lower():
            suggestions.append(RefinementSuggestion(
                refined_query=f"{query} para requirements engineering",
                reason="Agrega contexto específico",
                category="context",
                priority=2
            ))
        
        if "técnicas" in query.lower():
            suggestions.append(RefinementSuggestion(
                refined_query=f"¿Qué {query.lower()} son más efectivas para historias de usuario?",
                reason="Estructura como pregunta específica",
                category="structure", 
                priority=2
            ))
        
        return suggestions
    
    def _generate_domain_suggestions(self, query: str) -> List[RefinementSuggestion]:
        """Genera sugerencias para traer consulta al dominio académico"""
        return [
            RefinementSuggestion(
                refined_query="¿Qué técnicas de IA aplican a desarrollo de software?",
                reason="Consulta parece fuera del dominio académico",
                category="domain",
                priority=1
            ),
            RefinementSuggestion(
                refined_query="¿Cómo mejoran las metodologías de IA el análisis de requirements?",
                reason="Enfoque en dominio académico específico",
                category="domain",
                priority=2
            )
        ]
    
    def _calculate_confidence(self, query: str, issues: List[ValidationIssue]) -> float:
        """Calcula confidence de que la query está bien formada"""
        base_confidence = 1.0
        
        # Penalty por cada issue
        for issue in issues:
            if issue == ValidationIssue.TOO_VAGUE:
                base_confidence -= 0.4
            elif issue == ValidationIssue.OUT_OF_DOMAIN:
                base_confidence -= 0.5
            elif issue == ValidationIssue.TOO_GENERAL:
                base_confidence -= 0.2
            elif issue == ValidationIssue.MISSING_CONTEXT:
                base_confidence -= 0.3
        
        # Bonus por buenas características
        words = query.split()
        if len(words) >= 8:
            base_confidence += 0.1
        
        if any(keyword in query.lower() for keyword in self.domain_keywords):
            base_confidence += 0.2
        
        return max(0.0, min(1.0, base_confidence))
    
    def _load_domain_keywords(self) -> List[str]:
        """Carga keywords del dominio académico"""
        return [
            "machine learning", "deep learning", "artificial intelligence",
            "requirements engineering", "software development", "user stories",
            "nlp", "natural language processing", "algorithm", "model",
            "framework", "methodology", "analysis", "evaluation",
            "historias de usuario", "ingeniería de software", "análisis",
            "metodología", "algoritmo", "modelo", "framework", "evaluación"
        ]


# Instancia global
query_validator = QueryValidator()
