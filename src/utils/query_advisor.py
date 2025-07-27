# -*- coding: utf-8 -*-
"""
Query Advisor - Intelligent Query Suggestions and Analysis
"""

import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.utils.intent_detector import IntentType, IntentResult
from src.utils.logger import setup_logger

logger = setup_logger()


@dataclass
class EffectivenessScore:
    """Score de efectividad de una consulta"""
    score: float
    confidence_factors: Dict[str, float]
    improvement_areas: List[str]
    reasoning: str


@dataclass
class QuerySuggestion:
    """Sugerencia de mejora para consulta"""
    reformulated_query: str
    reason: str
    expected_improvement: str
    based_on_expansion: bool
    priority: int  # 1=high, 2=medium, 3=low


@dataclass
class ContextualTip:
    """Tip contextual por tipo de intención"""
    tip_text: str
    category: str
    example: str
    intent_type: IntentType


class ImprovementArea(Enum):
    """Áreas de mejora para consultas"""
    SPECIFICITY = "specificity"
    CONTEXT = "context"
    STRUCTURE = "structure"
    TERMINOLOGY = "terminology"
    SCOPE = "scope"


class QueryAdvisor:
    """Generador de sugerencias inteligentes para consultas académicas"""
    
    def __init__(self):
        self.effectiveness_threshold = 0.7
        self.suggestion_templates = self._load_suggestion_templates()
        self.contextual_tips = self._load_contextual_tips()
        
    def analyze_query_effectiveness(self, 
                                  query: str, 
                                  result: Dict,
                                  intent_result: Optional[IntentResult] = None) -> EffectivenessScore:
        """Analiza la efectividad de una consulta académica"""
        start_time = time.perf_counter()
        
        try:
            # Factores de efectividad con pesos
            factors = {}
            improvement_areas = []
            
            # Factor 1: Confianza de detección de intención (30%)
            intent_confidence = 0.5  # Default
            if intent_result:
                intent_confidence = intent_result.confidence
            factors['intent_confidence'] = intent_confidence * 0.3
            
            if intent_confidence < 0.6:
                improvement_areas.append(ImprovementArea.STRUCTURE.value)
            
            # Factor 2: Calidad del contexto recuperado (40%)
            context_quality = self._assess_context_quality(result.get('context', []))
            factors['context_quality'] = context_quality * 0.4
            
            if context_quality < 0.6:
                improvement_areas.append(ImprovementArea.TERMINOLOGY.value)
            
            # Factor 3: Especificidad de la consulta (20%)
            query_specificity = self._calculate_query_specificity(query)
            factors['query_specificity'] = query_specificity * 0.2
            
            if query_specificity < 0.5:
                improvement_areas.append(ImprovementArea.SPECIFICITY.value)
            
            # Factor 4: Utilización de expansión (10%)
            expansion_effectiveness = self._assess_expansion_effectiveness(result)
            factors['expansion_effectiveness'] = expansion_effectiveness * 0.1
            
            if expansion_effectiveness < 0.3:
                improvement_areas.append(ImprovementArea.SCOPE.value)
            
            # Score total
            total_score = sum(factors.values())
            
            # Reasoning
            reasoning = self._generate_effectiveness_reasoning(factors, total_score)
            
            processing_time = (time.perf_counter() - start_time) * 1000
            logger.debug(f"Effectiveness analysis completed in {processing_time:.1f}ms: {total_score:.3f}")
            
            return EffectivenessScore(
                score=round(total_score, 3),
                confidence_factors=factors,
                improvement_areas=list(set(improvement_areas)),
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Error analyzing query effectiveness: {e}")
            return EffectivenessScore(
                score=0.5,
                confidence_factors={},
                improvement_areas=[ImprovementArea.STRUCTURE.value],
                reasoning="Error en análisis de efectividad"
            )
    
    def generate_suggestions(self, 
                           query: str, 
                           intent_result: Optional[IntentResult],
                           effectiveness: EffectivenessScore) -> List[QuerySuggestion]:
        """Genera sugerencias de mejora para la consulta"""
        suggestions = []
        
        if not intent_result or effectiveness.score > self.effectiveness_threshold:
            return suggestions
        
        intent_type = intent_result.intent_type
        
        # Sugerencias basadas en áreas de mejora
        for area in effectiveness.improvement_areas:
            suggestion = self._create_suggestion_for_area(query, intent_type, area)
            if suggestion:
                suggestions.append(suggestion)
        
        # Sugerencias específicas por tipo de intención
        intent_suggestions = self._get_intent_specific_suggestions(query, intent_type)
        suggestions.extend(intent_suggestions)
        
        # Ordenar por prioridad y limitar
        suggestions.sort(key=lambda x: x.priority)
        return suggestions[:3]  # Máximo 3 sugerencias
    
    def get_contextual_tips(self, 
                          intent_type: IntentType, 
                          complexity_score: float = 0.5) -> List[ContextualTip]:
        """Obtiene tips contextuales por tipo de intención"""
        tips = []
        
        # Tips específicos por intención
        if intent_type in self.contextual_tips:
            intent_tips = self.contextual_tips[intent_type]
            tips.extend(intent_tips)
        
        # Tips adicionales basados en complejidad
        if complexity_score > 0.7:
            tips.append(ContextualTip(
                tip_text="Para consultas complejas, considera dividirla en sub-preguntas específicas",
                category="complexity",
                example="En lugar de preguntar todo sobre IA, pregunta específicamente sobre algoritmos",
                intent_type=intent_type
            ))
        
        return tips[:2]  # Máximo 2 tips
    
    def _assess_context_quality(self, context_docs: List) -> float:
        """Evalúa la calidad del contexto recuperado"""
        if not context_docs:
            return 0.0
        
        quality_score = 0.0
        doc_count = len(context_docs)
        
        # Factor 1: Número de documentos (optimal: 3-7)
        if 3 <= doc_count <= 7:
            doc_score = 1.0
        elif doc_count < 3:
            doc_score = doc_count / 3.0
        else:
            doc_score = max(0.5, 1.0 - (doc_count - 7) * 0.1)
        
        quality_score += doc_score * 0.4
        
        # Factor 2: Diversidad de contenido
        content_lengths = [len(doc.page_content) for doc in context_docs]
        avg_length = sum(content_lengths) / len(content_lengths)
        length_score = min(1.0, avg_length / 500)  # Optimal ~500 chars
        
        quality_score += length_score * 0.3
        
        # Factor 3: Presencia de metadata académica
        metadata_score = 0.0
        for doc in context_docs:
            if hasattr(doc, 'metadata') and doc.metadata:
                if any(key in doc.metadata for key in ['file_name', 'source_file']):
                    metadata_score += 1.0
        
        if doc_count > 0:
            metadata_score = metadata_score / doc_count
        
        quality_score += metadata_score * 0.3
        
        return min(1.0, quality_score)
    
    def _calculate_query_specificity(self, query: str) -> float:
        """Calcula la especificidad de la consulta"""
        words = query.split()
        word_count = len(words)
        
        # Factores de especificidad
        specificity_score = 0.0
        
        # Factor 1: Longitud (optimal: 8-20 palabras)
        if 8 <= word_count <= 20:
            length_score = 1.0
        elif word_count < 8:
            length_score = word_count / 8.0
        else:
            length_score = max(0.3, 1.0 - (word_count - 20) * 0.05)
        
        specificity_score += length_score * 0.4
        
        # Factor 2: Presencia de términos técnicos
        technical_terms = [
            "machine learning", "deep learning", "nlp", "natural language",
            "algorithm", "model", "framework", "methodology", "approach",
            "requirements", "software", "engineering", "artificial intelligence"
        ]
        
        found_technical = sum(1 for term in technical_terms if term in query.lower())
        technical_score = min(1.0, found_technical / 3.0)
        specificity_score += technical_score * 0.3
        
        # Factor 3: Estructura de pregunta clara
        question_indicators = ["qué", "cómo", "cuál", "por qué", "what", "how", "which", "why"]
        has_question_structure = any(indicator in query.lower() for indicator in question_indicators)
        structure_score = 1.0 if has_question_structure else 0.7
        
        specificity_score += structure_score * 0.3
        
        return min(1.0, specificity_score)
    
    def _assess_expansion_effectiveness(self, result: Dict) -> float:
        """Evalúa la efectividad de la expansión de consulta"""
        expansion_info = result.get('expansion_info')
        
        if not expansion_info:
            return 0.5  # No expansion available
        
        expansion_count = expansion_info.get('expansion_count', 0)
        
        if expansion_count == 0:
            return 0.3
        elif 1 <= expansion_count <= 6:
            return 1.0
        else:
            return max(0.5, 1.0 - (expansion_count - 6) * 0.1)
    
    def _generate_effectiveness_reasoning(self, factors: Dict[str, float], total_score: float) -> str:
        """Genera explicación del score de efectividad"""
        if total_score >= 0.8:
            return "Consulta bien estructurada con alta probabilidad de resultados relevantes"
        elif total_score >= 0.6:
            return "Consulta aceptable con oportunidades de mejora específicas"
        else:
            return "Consulta necesita reformulación para mejorar relevancia de resultados"
    
    def _create_suggestion_for_area(self, query: str, intent_type: IntentType, area: str) -> Optional[QuerySuggestion]:
        """Crea sugerencia específica por área de mejora"""
        suggestions_map = {
            ImprovementArea.SPECIFICITY.value: {
                "template": "Sé más específico: '{query} en el contexto de requirements engineering'",
                "reason": "Consulta muy general",
                "improvement": "Mayor relevancia de resultados"
            },
            ImprovementArea.CONTEXT.value: {
                "template": "Agrega contexto: '{query} aplicado a historias de usuario'",
                "reason": "Falta contexto académico",
                "improvement": "Resultados más enfocados"
            },
            ImprovementArea.STRUCTURE.value: {
                "template": "Estructura como pregunta: '¿Cómo {query}?'",
                "reason": "Estructura poco clara",
                "improvement": "Mejor detección de intención"
            },
            ImprovementArea.TERMINOLOGY.value: {
                "template": "Usa términos técnicos: reemplaza palabras generales por específicas",
                "reason": "Terminología muy general",
                "improvement": "Mejor matching con literatura académica"
            }
        }
        
        if area not in suggestions_map:
            return None
        
        suggestion_data = suggestions_map[area]
        
        return QuerySuggestion(
            reformulated_query=suggestion_data["template"].format(query=query),
            reason=suggestion_data["reason"],
            expected_improvement=suggestion_data["improvement"],
            based_on_expansion=False,
            priority=2
        )
    
    def _get_intent_specific_suggestions(self, query: str, intent_type: IntentType) -> List[QuerySuggestion]:
        """Obtiene sugerencias específicas por tipo de intención"""
        if intent_type not in self.suggestion_templates:
            return []
        
        templates = self.suggestion_templates[intent_type]
        suggestions = []
        
        for template_data in templates:
            suggestion = QuerySuggestion(
                reformulated_query=template_data["template"].format(original=query),
                reason=template_data["reason"],
                expected_improvement=template_data["improvement"],
                based_on_expansion=template_data.get("expansion_based", False),
                priority=template_data.get("priority", 2)
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _load_suggestion_templates(self) -> Dict[IntentType, List[Dict]]:
        """Carga templates de sugerencias por tipo de intención"""
        return {
            IntentType.DEFINITION: [
                {
                    "template": "¿Qué es {original} y cuáles son sus características principales?",
                    "reason": "Definición más completa",
                    "improvement": "Respuesta estructurada con características",
                    "priority": 1
                }
            ],
            IntentType.COMPARISON: [
                {
                    "template": "Compara {original} en términos de ventajas, desventajas y casos de uso",
                    "reason": "Comparación más sistemática",
                    "improvement": "Análisis estructurado con criterios claros",
                    "priority": 1
                }
            ],
            IntentType.STATE_OF_ART: [
                {
                    "template": "Analiza el estado del arte de {original} en los últimos 3 años",
                    "reason": "Enfoque temporal específico",
                    "improvement": "Información más actualizada y relevante",
                    "priority": 1
                }
            ],
            IntentType.GAP_ANALYSIS: [
                {
                    "template": "¿Qué limitaciones y oportunidades de investigación existen en {original}?",
                    "reason": "Enfoque dual en limitaciones y oportunidades",
                    "improvement": "Identificación completa de gaps",
                    "priority": 1
                }
            ]
        }
    
    def _load_contextual_tips(self) -> Dict[IntentType, List[ContextualTip]]:
        """Carga tips contextuales por tipo de intención"""
        return {
            IntentType.DEFINITION: [
                ContextualTip(
                    tip_text="Para definiciones académicas, incluye el contexto específico del dominio",
                    category="structure",
                    example="'¿Qué es machine learning en requirements engineering?' vs '¿Qué es machine learning?'",
                    intent_type=IntentType.DEFINITION
                )
            ],
            IntentType.COMPARISON: [
                ContextualTip(
                    tip_text="Especifica los criterios de comparación para obtener análisis más útiles",
                    category="clarity",
                    example="'Compara X vs Y en términos de performance, usabilidad y costo'",
                    intent_type=IntentType.COMPARISON
                )
            ],
            IntentType.STATE_OF_ART: [
                ContextualTip(
                    tip_text="Indica un marco temporal para obtener información más actualizada",
                    category="scope",
                    example="'Estado del arte en NLP en los últimos 2 años'",
                    intent_type=IntentType.STATE_OF_ART
                )
            ],
            IntentType.GAP_ANALYSIS: [
                ContextualTip(
                    tip_text="Enfócate en limitaciones específicas para identificar oportunidades claras",
                    category="focus",
                    example="'¿Qué limitaciones técnicas tienen los métodos actuales de X?'",
                    intent_type=IntentType.GAP_ANALYSIS
                )
            ]
        }


# Instancia global
query_advisor = QueryAdvisor()