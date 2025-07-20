# -*- coding: utf-8 -*-
"""
Academic Query Intent Detection System

Este módulo implementa un sistema híbrido de detección de intención para consultas académicas.
Combina pattern matching (rápido y interpretable) con scoring sofisticado para determinar
qué tipo de respuesta académica necesita el usuario.

Tipos de intención soportados:
- definition: Definiciones y explicaciones conceptuales
- comparison: Comparaciones metodológicas o técnicas  
- state_of_art: Análisis del estado del arte
- gap_analysis: Identificación de limitaciones y oportunidades de investigación
"""

import re
import time
from enum import Enum
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass

from config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger()


class IntentType(Enum):
    """Tipos de intención académica soportados"""
    DEFINITION = "definition"
    COMPARISON = "comparison" 
    STATE_OF_ART = "state_of_art"
    GAP_ANALYSIS = "gap_analysis"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    """Resultado de la detección de intención"""
    intent_type: IntentType
    confidence: float
    reasoning: str
    processing_time_ms: float
    matched_patterns: List[str]
    fallback_used: bool = False


class LinguisticFeatures(NamedTuple):
    """Features lingüísticas extraídas de la consulta"""
    question_words: List[str]
    academic_verbs: List[str] 
    comparison_markers: List[str]
    temporal_indicators: List[str]
    specificity_score: float


class QueryPreprocessor:
    """
    Preprocesa consultas académicas para optimizar la detección de intención.
    Normaliza texto, corrige errores comunes y extrae features lingüísticas.
    """
    
    def __init__(self):
        # Palabras interrogativas comunes en consultas académicas
        self.question_words = {
            'en': ['what', 'how', 'why', 'when', 'where', 'which', 'who'],
            'es': ['qué', 'cómo', 'por qué', 'cuándo', 'dónde', 'cuál', 'quién']
        }
        
        # Verbos académicos que indican intención
        self.academic_verbs = [
            'analyze', 'compare', 'evaluate', 'assess', 'examine', 'investigate',
            'explore', 'study', 'review', 'survey', 'synthesize',
            'analiza', 'compara', 'evalúa', 'examina', 'investiga', 'explora'
        ]
        
        # Marcadores de comparación
        self.comparison_markers = [
            'vs', 'versus', 'against', 'compared to', 'relative to', 'than',
            'difference', 'similarity', 'contrast', 'unlike', 'similar to'
        ]
        
        # Indicadores temporales para estado del arte
        self.temporal_indicators = [
            'current', 'recent', 'latest', 'modern', 'contemporary', 'today',
            'now', 'present', 'actual', 'reciente', 'último', 'moderno'
        ]
    
    def preprocess(self, query: str) -> Tuple[str, LinguisticFeatures]:
        """
        Preprocesa la consulta y extrae features lingüísticas.
        
        Args:
            query: Consulta original del usuario
            
        Returns:
            Tuple con (consulta_limpia, features_extraídas)
        """
        # 1. Normalización básica
        cleaned = self._normalize_text(query)
        
        # 2. Extracción de features lingüísticas
        features = self._extract_linguistic_features(cleaned)
        
        return cleaned, features
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza el texto para procesamiento consistente"""
        # Convertir a minúsculas
        text = text.lower().strip()
        
        # Normalizar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        # Normalizar signos de puntuación comunes
        text = re.sub(r'[¿?]+', '?', text)
        text = re.sub(r'[¡!]+', '!', text) 
        
        return text
    
    def _extract_linguistic_features(self, text: str) -> LinguisticFeatures:
        """Extrae features lingüísticas que ayudan en la clasificación"""
        words = text.split()
        
        # Encontrar palabras interrogativas
        question_words = [
            word for word in words 
            if any(word.startswith(qw) for lang_qw in self.question_words.values() for qw in lang_qw)
        ]
        
        # Encontrar verbos académicos
        academic_verbs = [
            word for word in words
            if any(verb in word for verb in self.academic_verbs)
        ]
        
        # Encontrar marcadores de comparación
        comparison_markers = [
            marker for marker in self.comparison_markers
            if marker in text
        ]
        
        # Encontrar indicadores temporales
        temporal_indicators = [
            indicator for indicator in self.temporal_indicators  
            if indicator in text
        ]
        
        # Calcular score de especificidad (consultas más largas y específicas)
        specificity_score = min(1.0, len(words) / 10.0)  # Normalizado a 0-1
        
        return LinguisticFeatures(
            question_words=question_words,
            academic_verbs=academic_verbs,
            comparison_markers=comparison_markers,
            temporal_indicators=temporal_indicators,
            specificity_score=specificity_score
        )


class KeywordBasedClassifier:
    """
    Clasificador basado en patterns y keywords académicos específicos.
    Optimizado para alta precisión en casos claros y velocidad de respuesta.
    """
    
    def __init__(self):
        self.intent_keywords = settings.intent_keywords
        self.pattern_weights = settings.intent_pattern_weights
        
        # Compilar patterns regex para eficiencia
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compila patterns regex para cada tipo de intención"""
        self.compiled_patterns = {}
        
        # Patterns para definición
        self.compiled_patterns[IntentType.DEFINITION] = [
            (re.compile(r'\b(?:what\s+is|qué\s+es)\b'), 0.9),
            (re.compile(r'\b(?:define|definition\s+of)\b'), 0.85),
            (re.compile(r'\b(?:concept\s+of|meaning\s+of)\b'), 0.8),
            (re.compile(r'\b(?:explain|explica)\b'), 0.7),
        ]
        
        # Patterns para comparación
        self.compiled_patterns[IntentType.COMPARISON] = [
            (re.compile(r'\b(?:compare|compara)\b'), 0.9),
            (re.compile(r'\b(?:vs\.?|versus)\b'), 0.85),
            (re.compile(r'\b(?:difference\s+between|diferencia\s+entre)\b'), 0.9),
            (re.compile(r'\b(?:advantages?\s+and\s+disadvantages?|pros\s+and\s+cons)\b'), 0.85),
            (re.compile(r'\b(?:contrast|better\s+than)\b'), 0.8),
        ]
        
        # Patterns para estado del arte
        self.compiled_patterns[IntentType.STATE_OF_ART] = [
            (re.compile(r'\b(?:state\s+of\s+(?:the\s+)?art|estado\s+del\s+arte)\b'), 0.95),
            (re.compile(r'\b(?:current\s+approaches?|enfoques\s+actuales)\b'), 0.8),
            (re.compile(r'\b(?:latest\s+research|recent\s+developments)\b'), 0.85),
            (re.compile(r'\b(?:survey\s+of|overview\s+of|review\s+of)\b'), 0.8),
            (re.compile(r'\b(?:literatura\s+actual|tendencias)\b'), 0.8),
        ]
        
        # Patterns para análisis de gaps
        self.compiled_patterns[IntentType.GAP_ANALYSIS] = [
            (re.compile(r'\b(?:limitations?|limitaciones)\b'), 0.85),
            (re.compile(r'\b(?:gaps?|brechas)\b'), 0.9),
            (re.compile(r'\b(?:future\s+work|trabajo\s+futuro)\b'), 0.85),
            (re.compile(r'\b(?:what\s+is\s+missing|qué\s+falta)\b'), 0.9),
            (re.compile(r'\b(?:challenges?|open\s+problems)\b'), 0.8),
            (re.compile(r'\b(?:research\s+gaps?|oportunidades)\b'), 0.9),
        ]
    
    def classify(self, query: str, features: LinguisticFeatures) -> IntentResult:
        """
        Clasifica la intención usando pattern matching y scoring.
        
        Args:
            query: Consulta preprocesada
            features: Features lingüísticas extraídas
            
        Returns:
            IntentResult con la clasificación y metadata
        """
        start_time = time.perf_counter()
        
        # Calcular scores para cada tipo de intención
        intent_scores = {}
        matched_patterns = {}
        
        for intent_type in [IntentType.DEFINITION, IntentType.COMPARISON, 
                           IntentType.STATE_OF_ART, IntentType.GAP_ANALYSIS]:
            score, patterns = self._calculate_intent_score(query, intent_type, features)
            intent_scores[intent_type] = score
            matched_patterns[intent_type] = patterns
        
        # Seleccionar la intención con mayor score
        best_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k])
        best_score = intent_scores[best_intent]
        
        # Normalizar confidence (scores pueden superar 1.0)
        confidence = min(1.0, best_score)
        
        # Generar explicación del reasoning
        reasoning = self._generate_reasoning(best_intent, matched_patterns[best_intent], confidence)
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        return IntentResult(
            intent_type=best_intent if confidence >= settings.intent_confidence_threshold else IntentType.UNKNOWN,
            confidence=confidence,
            reasoning=reasoning,
            processing_time_ms=processing_time,
            matched_patterns=matched_patterns[best_intent],
            fallback_used=confidence < settings.intent_confidence_threshold
        )
    
    def _calculate_intent_score(self, query: str, intent_type: IntentType, 
                               features: LinguisticFeatures) -> Tuple[float, List[str]]:
        """Calcula el score para un tipo específico de intención"""
        total_score = 0.0
        matched_patterns = []
        
        # Score basado en patterns regex
        for pattern, weight in self.compiled_patterns[intent_type]:
            if pattern.search(query):
                total_score += weight
                matched_patterns.append(pattern.pattern)
        
        # Bonus por features lingüísticas específicas
        if intent_type == IntentType.DEFINITION:
            total_score += len(features.question_words) * 0.2
            
        elif intent_type == IntentType.COMPARISON:
            total_score += len(features.comparison_markers) * 0.3
            
        elif intent_type == IntentType.STATE_OF_ART:
            total_score += len(features.temporal_indicators) * 0.2
            total_score += len(features.academic_verbs) * 0.1
            
        elif intent_type == IntentType.GAP_ANALYSIS:
            # Gap analysis se beneficia de especificidad alta
            total_score += features.specificity_score * 0.3
        
        return total_score, matched_patterns
    
    def _generate_reasoning(self, intent_type: IntentType, patterns: List[str], 
                           confidence: float) -> str:
        """Genera explicación human-readable del reasoning"""
        base_explanations = {
            IntentType.DEFINITION: "Detecté palabras clave que indican solicitud de definición o explicación conceptual",
            IntentType.COMPARISON: "Identifiqué marcadores de comparación entre métodos o enfoques",
            IntentType.STATE_OF_ART: "Reconocí indicadores de análisis del estado actual de la investigación",
            IntentType.GAP_ANALYSIS: "Detecté términos relacionados con limitaciones y oportunidades de investigación",
            IntentType.UNKNOWN: "No pude identificar un patrón claro de intención académica"
        }
        
        explanation = base_explanations[intent_type]
        
        if patterns:
            explanation += f" (patterns encontrados: {len(patterns)})"
            
        explanation += f" con confianza {confidence:.2f}"
        
        return explanation


class IntentDetector:
    """
    Sistema principal de detección de intención que orquesta el preprocessing
    y clasificación, con manejo de errores y fallbacks.
    """
    
    def __init__(self):
        self.preprocessor = QueryPreprocessor()
        self.classifier = KeywordBasedClassifier()
        self.enabled = settings.enable_intent_detection
    
    async def detect_intent(self, query: str) -> IntentResult:
        """
        Detecta la intención de una consulta académica.
        
        Args:
            query: Consulta del usuario
            
        Returns:
            IntentResult con la intención detectada y metadata
        """
        # Si intent detection está deshabilitado, retornar UNKNOWN
        if not self.enabled:
            return IntentResult(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                reasoning="Intent detection está deshabilitado",
                processing_time_ms=0.0,
                matched_patterns=[],
                fallback_used=True
            )
        
        try:
            start_time = time.perf_counter()
            
            # Validar input
            if not query or not query.strip():
                return self._create_fallback_result("Consulta vacía")
            
            # Preprocessing
            cleaned_query, features = self.preprocessor.preprocess(query)
            
            # Clasificación
            result = self.classifier.classify(cleaned_query, features)
            
            # Verificar SLA de tiempo
            total_time = (time.perf_counter() - start_time) * 1000
            if total_time > settings.intent_max_processing_time_ms:
                logger.warning(f"Intent detection tardó {total_time:.1f}ms, excediendo SLA de {settings.intent_max_processing_time_ms}ms")
            
            # Log para debugging y métricas
            logger.debug(f"Intent detected: {result.intent_type.value} (confidence: {result.confidence:.2f}, time: {result.processing_time_ms:.1f}ms)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error en detección de intención para query '{query[:50]}...': {e}")
            return self._create_fallback_result(f"Error en clasificación: {str(e)}")
    
    def _create_fallback_result(self, reason: str) -> IntentResult:
        """Crea un resultado de fallback cuando la clasificación falla"""
        return IntentResult(
            intent_type=IntentType.UNKNOWN,
            confidence=0.0,
            reasoning=reason,
            processing_time_ms=0.0,
            matched_patterns=[],
            fallback_used=True
        )


# Instancia global para uso en toda la aplicación
intent_detector = IntentDetector()