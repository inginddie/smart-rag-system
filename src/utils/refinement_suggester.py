# -*- coding: utf-8 -*-
"""
Refinement Suggester - HU5 Query Preprocessing Component
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.utils.query_validator import ValidationResult, ValidationIssue
from src.utils.logger import setup_logger

logger = setup_logger()


class RefinementStrategy(Enum):
    """Estrategias de refinamiento"""
    SPECIFICITY = "specificity"
    CONTEXT_ADDITION = "context_addition"
    TERMINOLOGY_ENHANCEMENT = "terminology_enhancement"
    STRUCTURE_IMPROVEMENT = "structure_improvement"
    DOMAIN_ALIGNMENT = "domain_alignment"


@dataclass
class RefinementSuggestion:
    """Sugerencia de refinamiento específica"""
    suggested_query: str
    reason: str
    confidence: float
    expected_improvement: str
    strategy: RefinementStrategy
    priority: int  # 1=high, 2=medium, 3=low


@dataclass
class RefinementResult:
    """Resultado completo de refinamiento"""
    suggestions_available: bool
    suggestions: List[RefinementSuggestion]
    quick_fixes: List[str]
    processing_time_ms: float
    strategies_applied: List[RefinementStrategy]


class RefinementSuggester:
    """Generador de sugerencias de refinamiento para queries"""
    
    def __init__(self):
        self.suggestion_templates = self._load_suggestion_templates()
        self.domain_contexts = self._load_domain_contexts()
        self.terminology_enhancements = self._load_terminology_enhancements()
    
    def generate_refinements(self, query: str, validation_result: ValidationResult) -> RefinementResult:
        """Genera sugerencias de refinamiento basadas en issues de validación"""
        start_time = time.perf_counter()
        
        try:
            suggestions = []
            quick_fixes = []
            strategies_applied = []
            
            # Generar sugerencias por cada issue encontrado
            for issue in validation_result.issues:
                strategy_suggestions = self._generate_suggestions_for_issue(query, issue)
                suggestions.extend(strategy_suggestions)
                
                # Agregar estrategia si generó sugerencias
                if strategy_suggestions:
                    strategy = self._get_strategy_for_issue(issue)
                    if strategy not in strategies_applied:
                        strategies_applied.append(strategy)
            
            # Generar quick fixes
            quick_fixes = self._generate_quick_fixes(query, validation_result.issues)
            
            # Ordenar sugerencias por prioridad y confidence
            suggestions.sort(key=lambda x: (x.priority, -x.confidence))
            
            # Limitar número de sugerencias
            max_suggestions = 3
            suggestions = suggestions[:max_suggestions]
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return RefinementResult(
                suggestions_available=len(suggestions) > 0,
                suggestions=suggestions,
                quick_fixes=quick_fixes[:5],  # Max 5 quick fixes
                processing_time_ms=processing_time,
                strategies_applied=strategies_applied
            )
            
        except Exception as e:
            logger.error(f"Error generating refinements: {e}")
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return RefinementResult(
                suggestions_available=False,
                suggestions=[],
                quick_fixes=[],
                processing_time_ms=processing_time,
                strategies_applied=[]
            )
    
    def _generate_suggestions_for_issue(self, query: str, issue: ValidationIssue) -> List[RefinementSuggestion]:
        """Genera sugerencias para un issue específico"""
        suggestions = []
        
        if issue == ValidationIssue.TOO_VAGUE:
            suggestions.extend(self._generate_specificity_suggestions(query))
        
        elif issue == ValidationIssue.TOO_GENERAL:
            suggestions.extend(self._generate_context_suggestions(query))
        
        elif issue == ValidationIssue.OUT_OF_DOMAIN:
            suggestions.extend(self._generate_domain_alignment_suggestions(query))
        
        elif issue == ValidationIssue.MISSING_CONTEXT:
            suggestions.extend(self._generate_structure_suggestions(query))
        
        return suggestions
    
    def _generate_specificity_suggestions(self, query: str) -> List[RefinementSuggestion]:
        """Genera sugerencias para queries muy vagas"""
        suggestions = []
        query_lower = query.lower().strip()
        
        # Patrones específicos para términos comunes
        if any(term in query_lower for term in ["ia", "ai"]):
            suggestions.extend([
                RefinementSuggestion(
                    suggested_query="¿Qué técnicas de IA se aplican al análisis de historias de usuario?",
                    reason="Especifica aplicación concreta de IA",
                    confidence=0.85,
                    expected_improvement="Resultados más relevantes y específicos",
                    strategy=RefinementStrategy.SPECIFICITY,
                    priority=1
                ),
                RefinementSuggestion(
                    suggested_query="¿Cómo mejora la IA el proceso de requirements engineering?",
                    reason="Agrega contexto de proceso específico",
                    confidence=0.80,
                    expected_improvement="Enfoque en aplicación práctica",
                    strategy=RefinementStrategy.SPECIFICITY,
                    priority=2
                )
            ])
        
        elif any(term in query_lower for term in ["ml", "machine learning"]):
            suggestions.extend([
                RefinementSuggestion(
                    suggested_query="¿Qué algoritmos de machine learning son efectivos para clasificar historias de usuario?",
                    reason="Especifica algoritmos y aplicación",
                    confidence=0.90,
                    expected_improvement="Respuesta técnica específica",
                    strategy=RefinementStrategy.SPECIFICITY,
                    priority=1
                ),
                RefinementSuggestion(
                    suggested_query="Compara técnicas de machine learning supervisado vs no supervisado para requirements",
                    reason="Estructura comparativa específica",
                    confidence=0.75,
                    expected_improvement="Análisis comparativo detallado",
                    strategy=RefinementStrategy.SPECIFICITY,
                    priority=2
                )
            ])
        
        elif any(term in query_lower for term in ["nlp", "natural language"]):
            suggestions.append(
                RefinementSuggestion(
                    suggested_query="¿Qué técnicas de NLP se usan para extraer información de historias de usuario?",
                    reason="Especifica técnicas y aplicación",
                    confidence=0.85,
                    expected_improvement="Enfoque en aplicación específica",
                    strategy=RefinementStrategy.SPECIFICITY,
                    priority=1
                )
            )
        
        # Sugerencia genérica para otros casos
        if not suggestions:
            suggestions.append(
                RefinementSuggestion(
                    suggested_query=f"¿Cómo se aplica {query} específicamente en el desarrollo de software?",
                    reason="Agrega contexto de aplicación específica",
                    confidence=0.60,
                    expected_improvement="Mayor relevancia al dominio académico",
                    strategy=RefinementStrategy.SPECIFICITY,
                    priority=3
                )
            )
        
        return suggestions
    
    def _generate_context_suggestions(self, query: str) -> List[RefinementSuggestion]:
        """Genera sugerencias para agregar contexto académico"""
        suggestions = []
        
        # Agregar contexto de dominio
        domain_contexts = [
            "para requirements engineering",
            "en desarrollo de software",
            "aplicado a historias de usuario",
            "en ingeniería de software"
        ]
        
        for context in domain_contexts[:2]:  # Solo 2 sugerencias de contexto
            suggestions.append(
                RefinementSuggestion(
                    suggested_query=f"{query} {context}",
                    reason=f"Agrega contexto específico: {context}",
                    confidence=0.70,
                    expected_improvement="Resultados más enfocados al dominio",
                    strategy=RefinementStrategy.CONTEXT_ADDITION,
                    priority=2
                )
            )
        
        return suggestions
    
    def _generate_domain_alignment_suggestions(self, query: str) -> List[RefinementSuggestion]:
        """Genera sugerencias para alinear con dominio académico"""
        suggestions = []
        
        # Sugerencias de alineación al dominio académico
        domain_aligned_queries = [
            "¿Qué técnicas de IA son relevantes para development de software?",
            "¿Cómo se pueden aplicar métodos de machine learning al análisis de requirements?",
            "¿Qué frameworks de IA son útiles para mejorar historias de usuario?"
        ]
        
        for i, aligned_query in enumerate(domain_aligned_queries):
            suggestions.append(
                RefinementSuggestion(
                    suggested_query=aligned_query,
                    reason="Consulta alineada con dominio académico específico",
                    confidence=0.75,
                    expected_improvement="Resultados dentro del corpus académico",
                    strategy=RefinementStrategy.DOMAIN_ALIGNMENT,
                    priority=1 if i == 0 else 2
                )
            )
        
        return suggestions[:2]  # Solo 2 sugerencias
    
    def _generate_structure_suggestions(self, query: str) -> List[RefinementSuggestion]:
        """Genera sugerencias para mejorar estructura de la consulta"""
        suggestions = []
        
        # Mejorar estructura preguntando cómo/qué/cuál
        if not any(word in query.lower() for word in ["qué", "cómo", "cuál", "what", "how", "which"]):
            suggestions.extend([
                RefinementSuggestion(
                    suggested_query=f"¿Cómo {query.lower()}?",
                    reason="Estructura como pregunta específica",
                    confidence=0.65,
                    expected_improvement="Respuesta más directa y específica",
                    strategy=RefinementStrategy.STRUCTURE_IMPROVEMENT,
                    priority=2
                ),
                RefinementSuggestion(
                    suggested_query=f"¿Qué aspectos de {query.lower()} son más importantes?",
                    reason="Enfoca en aspectos específicos",
                    confidence=0.60,
                    expected_improvement="Análisis más detallado",
                    strategy=RefinementStrategy.STRUCTURE_IMPROVEMENT,
                    priority=3
                )
            ])
        
        return suggestions
    
    def _generate_quick_fixes(self, query: str, issues: List[ValidationIssue]) -> List[str]:
        """Genera quick fixes textuales para problemas comunes"""
        fixes = []
        
        if ValidationIssue.TOO_VAGUE in issues:
            fixes.append("Ser más específico sobre qué aspecto te interesa")
            fixes.append("Agregar contexto de aplicación (ej: 'para requirements')")
        
        if ValidationIssue.TOO_GENERAL in issues:
            fixes.append("Especificar el dominio de aplicación")
            fixes.append("Usar términos técnicos más precisos")
        
        if ValidationIssue.OUT_OF_DOMAIN in issues:
            fixes.append("Enfocar la consulta en IA/software/requirements")
            fixes.append("Usar terminología académica del dominio")
        
        if ValidationIssue.MISSING_CONTEXT in issues:
            fixes.append("Estructurar como pregunta clara (¿Qué...?, ¿Cómo...?)")
            fixes.append("Especificar el objetivo de la consulta")
        
        return fixes
    
    def _get_strategy_for_issue(self, issue: ValidationIssue) -> RefinementStrategy:
        """Mapea issues a estrategias de refinamiento"""
        mapping = {
            ValidationIssue.TOO_VAGUE: RefinementStrategy.SPECIFICITY,
            ValidationIssue.TOO_GENERAL: RefinementStrategy.CONTEXT_ADDITION,
            ValidationIssue.OUT_OF_DOMAIN: RefinementStrategy.DOMAIN_ALIGNMENT,
            ValidationIssue.MISSING_CONTEXT: RefinementStrategy.STRUCTURE_IMPROVEMENT
        }
        return mapping.get(issue, RefinementStrategy.SPECIFICITY)
    
    def _load_suggestion_templates(self) -> Dict:
        """Carga templates de sugerencias por categoría"""
        return {
            "vague_ai": [
                "¿Qué técnicas de IA se usan para {context}?",
                "¿Cómo aplica la IA al {domain}?",
                "¿Cuáles son los algoritmos de IA más efectivos para {application}?"
            ],
            "vague_ml": [
                "¿Qué métodos de ML son útiles para {context}?",
                "Compara técnicas de ML supervisado vs no supervisado para {application}",
                "¿Cómo se evalúa la efectividad de modelos de ML en {domain}?"
            ],
            "general_methods": [
                "¿Qué {term} específicas son mejores para {context}?",
                "Compara diferentes {term} para {application}",
                "¿Cuáles son las ventajas de cada {term} en {domain}?"
            ]
        }
    
    def _load_domain_contexts(self) -> List[str]:
        """Carga contextos de dominio académico"""
        return [
            "requirements engineering",
            "desarrollo de software",
            "historias de usuario",
            "ingeniería de software",
            "análisis de requirements",
            "automatización de procesos de software",
            "metodologías ágiles",
            "calidad de software"
        ]
    
    def _load_terminology_enhancements(self) -> Dict[str, List[str]]:
        """Carga mejoras terminológicas"""
        return {
            "métodos": ["técnicas", "enfoques", "metodologías", "estrategias"],
            "herramientas": ["frameworks", "bibliotecas", "toolkits", "plataformas"],
            "algoritmos": ["modelos", "técnicas algorítmicas", "approaches computacionales"],
            "análisis": ["evaluación", "assessment", "estudio", "investigación"]
        }
    
    def get_suggestion_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de sugerencias generadas"""
        # En una implementación completa, esto se obtendría de un tracker
        return {
            "total_suggestions_generated": 0,
            "most_common_strategy": "specificity",
            "average_confidence": 0.75,
            "suggestion_adoption_rate": 0.6
        }


# Instancia global
refinement_suggester = RefinementSuggester()
