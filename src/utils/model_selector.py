# -*- coding: utf-8 -*-
from typing import Tuple
from config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger()

class ModelSelector:
    """Selector inteligente de modelos optimizado para investigación académica"""
    
    def __init__(self):
        # Palabras clave que indican consultas complejas (académicas)
        self.complex_keywords = [
            # Análisis académico profundo
            'analiza', 'analyze', 'análisis', 'analysis', 'evaluación', 'evaluation',
            'compara', 'compare', 'contrasta', 'contrast', 'diferencias', 'similarities',
            'síntesis', 'synthesis', 'integra', 'integrate', 'combina', 'combine',
            
            # Metodología y investigación
            'metodología', 'methodology', 'framework', 'approach', 'método', 'method',
            'estado del arte', 'state of art', 'literatura', 'literature', 'revisión', 'review',
            'gaps', 'brechas', 'limitaciones', 'limitations', 'futuro', 'future work',
            
            # Análisis crítico
            'crítico', 'critical', 'evalúa', 'evaluate', 'assessment', 'valoración',
            'investigación', 'research', 'estudio', 'study', 'findings', 'hallazgos',
            
            # Conceptos académicos específicos para tu tesis
            'paper', 'artículo', 'journal', 'conference', 'proceedings',
            'algoritmo', 'algorithm', 'modelo', 'model', 'técnica', 'technique',
            'historias de usuario', 'user stories', 'requirements', 'ágil', 'agile',
            'nlp', 'machine learning', 'deep learning', 'inteligencia artificial',
            
            # Palabras de comparación y relación
            'ventajas', 'desventajas', 'pros', 'contras', 'advantages', 'disadvantages',
            'relación', 'relationship', 'impacto', 'impact', 'influencia', 'influence'
        ]
    
    def select_model(self, query: str) -> Tuple[str, float, str]:
        """Selecciona el modelo apropiado basado en la complejidad de la consulta"""
        if not settings.enable_smart_selection:
            return settings.default_model, 0.5, "Smart selection disabled"
        
        query_lower = query.lower()
        complexity_score = 0.0
        
        # Calcular score basado en palabras clave académicas
        complex_matches = 0
        for keyword in self.complex_keywords:
            if keyword in query_lower:
                complex_matches += 1
                complexity_score += 0.15
        
        # Bonificación por longitud (consultas académicas suelen ser largas)
        word_count = len(query.split())
        if word_count > 15:
            complexity_score += 0.2
        elif word_count > 10:
            complexity_score += 0.1
        
        # Bonificación por patrones académicos específicos
        academic_patterns = ['compara', 'analiza', 'evalúa', 'sintetiza', 'gaps', 'limitaciones']
        for pattern in academic_patterns:
            if pattern in query_lower:
                complexity_score += 0.1
        
        # Normalizar entre 0 y 1
        complexity_score = min(1.0, complexity_score)
        
        # Seleccionar modelo basado en umbral
        if complexity_score >= settings.complexity_threshold:
            selected_model = settings.complex_model
            reasoning = f"High complexity ({complexity_score:.2f}) - Using {settings.complex_model} for academic analysis"
        else:
            selected_model = settings.simple_model
            reasoning = f"Low complexity ({complexity_score:.2f}) - Using {settings.simple_model} for simple query"
        
        logger.info(f"Model selection: {selected_model} | Score: {complexity_score:.2f} | Matches: {complex_matches}")
        return selected_model, complexity_score, reasoning