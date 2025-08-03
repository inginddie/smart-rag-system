# -*- coding: utf-8 -*-
"""
Academic Query Expansion System

Expande consultas académicas con sinónimos y términos relacionados manteniendo
coherencia semántica y respetando intención del usuario.
"""

import re
import time
from typing import Dict, List, Optional, Set, NamedTuple
from dataclasses import dataclass
from enum import Enum

from config.settings import settings
from src.utils.logger import setup_logger
from src.utils.intent_detector import IntentType

logger = setup_logger()


@dataclass
class ExpansionResult:
    """Resultado de expansión de consulta"""
    original_query: str
    expanded_terms: List[str]
    protected_terms: List[str]
    final_query: str
    processing_time_ms: float
    expansion_count: int
    strategy_used: str = "moderate"


class ExpansionStrategy(Enum):
    """Estrategias de expansión por tipo de intención"""
    CONSERVATIVE = "conservative"  # Pocos sinónimos de alta confianza
    MODERATE = "moderate"          # Balance sinónimos + variaciones
    COMPREHENSIVE = "comprehensive" # Expansión amplia + contexto


class AcademicVocabulary:
    """Vocabulario académico estructurado por dominios y contextos"""
    
    def __init__(self):
        self.domain_synonyms = self._load_domain_synonyms()
        self.acronym_expansions = self._load_acronym_expansions()
        self.contextual_variations = self._load_contextual_variations()
        
    def _load_domain_synonyms(self) -> Dict[str, List[str]]:
        """Sinónimos académicos por dominio específico"""
        return {
            # AI/ML Domain
            "machine learning": ["ML", "artificial intelligence", "AI", "predictive modeling", "algorithmic learning"],
            "deep learning": ["neural networks", "deep neural networks", "DNN", "artificial neural networks"],
            "natural language processing": ["NLP", "computational linguistics", "text processing", "language understanding"],
            "artificial intelligence": ["AI", "machine intelligence", "computational intelligence", "automated reasoning"],
            
            # Software Engineering Domain  
            "user stories": ["historias de usuario", "acceptance criteria", "user requirements", "functional requirements"],
            "requirements engineering": ["requirements analysis", "requirements specification", "RE", "software requirements"],
            "software development": ["programming", "coding", "software engineering", "application development"],
            "agile methodology": ["agile development", "scrum", "iterative development", "agile practices"],
            
            # Research Domain
            "state of the art": ["estado del arte", "current approaches", "latest research", "recent developments"],
            "literature review": ["systematic review", "survey", "research overview", "academic review"],
            "research gaps": ["research opportunities", "future work", "limitations", "open problems"],
            "methodology": ["approach", "method", "technique", "framework", "strategy"],
            
            # Technical Terms
            "framework": ["library", "toolkit", "platform", "architecture", "infrastructure"],
            "algorithm": ["method", "procedure", "technique", "approach", "process"],
            "evaluation": ["assessment", "analysis", "measurement", "validation", "testing"],
            "implementation": ["development", "coding", "programming", "deployment", "realization"]
        }
    
    def _load_acronym_expansions(self) -> Dict[str, List[str]]:
        """Expansiones de acrónimos académicos"""
        return {
            "ML": ["machine learning", "algorithmic learning"],
            "AI": ["artificial intelligence", "machine intelligence"],
            "NLP": ["natural language processing", "computational linguistics"],
            "RE": ["requirements engineering", "requirements analysis"],
            "SE": ["software engineering", "software development"],
            "DL": ["deep learning", "neural networks"],
            "CNN": ["convolutional neural networks", "convolutional networks"],
            "RNN": ["recurrent neural networks", "recurrent networks"],
            "BERT": ["bidirectional encoder representations", "transformer model"],
            "GPT": ["generative pre-trained transformer", "language model"]
        }
    
    def _load_contextual_variations(self) -> Dict[IntentType, Dict[str, List[str]]]:
        """Variaciones contextuales específicas por tipo de intención"""
        return {
            IntentType.DEFINITION: {
                # Para definiciones, agregar términos explicativos
                "concept": ["definition", "explanation", "meaning", "notion"],
                "approach": ["method", "technique", "strategy", "way"],
                "system": ["framework", "architecture", "platform", "tool"]
            },
            IntentType.COMPARISON: {
                # Para comparaciones, agregar términos contrastivos
                "versus": ["vs", "compared to", "against", "relative to"],
                "difference": ["distinction", "contrast", "variation", "disparity"],
                "advantage": ["benefit", "strength", "merit", "pro"],
                "disadvantage": ["limitation", "weakness", "drawback", "con"]
            },
            IntentType.STATE_OF_ART: {
                # Para estado del arte, agregar términos temporales y de tendencia
                "current": ["recent", "latest", "modern", "contemporary"],
                "trend": ["direction", "tendency", "pattern", "evolution"],
                "research": ["study", "investigation", "work", "analysis"]
            },
            IntentType.GAP_ANALYSIS: {
                # Para gaps, agregar términos de limitación y oportunidad
                "limitation": ["constraint", "restriction", "shortcoming", "weakness"],
                "opportunity": ["potential", "possibility", "chance", "prospect"],
                "future": ["upcoming", "prospective", "next", "forthcoming"]
            }
        }


class QueryExpander:
    """Expansor de consultas académicas con control semántico"""
    
    def __init__(self):
        self.vocabulary = AcademicVocabulary()
        self.expansion_enabled = getattr(settings, 'enable_query_expansion', True)
        self.max_expansion_terms = getattr(settings, 'max_expansion_terms', 10)
        self.expansion_strategy = getattr(settings, 'expansion_strategy', 'moderate')
        
    def expand_query(self, query: str, intent_type: Optional[IntentType] = None) -> ExpansionResult:
        start_time = time.perf_counter()
        
        try:
            # 1. Detectar términos protegidos (entre comillas)
            protected_terms = self._extract_protected_terms(query)
            
            # 2. Extraer términos candidatos para expansión
            candidate_terms = self._extract_expansion_candidates(query, protected_terms)
            
            # 3. Generar expansiones por término
            expanded_terms = self._generate_expansions(candidate_terms, intent_type)
            
            # 4. Filtrar y rankear expansiones
            filtered_expansions = self._filter_and_rank_expansions(
                expanded_terms, query, intent_type
            )
            
            # 5. Construir consulta final
            final_query = self._build_final_query(query, filtered_expansions, protected_terms)
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            result = ExpansionResult(
                original_query=query,
                expanded_terms=filtered_expansions,
                protected_terms=protected_terms,
                final_query=final_query,
                processing_time_ms=processing_time,
                expansion_count=len(filtered_expansions),
                strategy_used=self.expansion_strategy
            )
            
            logger.debug(f"Query expansion completed: {len(filtered_expansions)} terms added in {processing_time:.1f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error in query expansion: {e}")
            # Fallback gracioso - retornar consulta original
            return ExpansionResult(
                original_query=query,
                expanded_terms=[],
                protected_terms=[],
                final_query=query,
                processing_time_ms=(time.perf_counter() - start_time) * 1000,
                expansion_count=0,
                strategy_used=self.expansion_strategy
            )
    
    def _extract_protected_terms(self, query: str) -> List[str]:
        """Extrae términos entre comillas que no deben expandirse"""
        protected = []
        # Buscar términos entre comillas dobles
        quoted_terms = re.findall(r'"([^"]*)"', query)
        protected.extend(quoted_terms)
        
        # Buscar términos entre comillas simples
        single_quoted = re.findall(r"'([^']*)'", query)
        protected.extend(single_quoted)
        
        return protected
    
    def _extract_expansion_candidates(self, query: str, protected_terms: List[str]) -> List[str]:
        """Extrae términos candidatos para expansión (excluyendo protegidos)"""
        # Limpiar query removiendo términos protegidos temporalmente
        clean_query = query.lower()
        for protected in protected_terms:
            clean_query = clean_query.replace(f'"{protected.lower()}"', '')
            clean_query = clean_query.replace(f"'{protected.lower()}'", '')
        
        # Extraer candidatos potenciales
        candidates = []
        
        # Buscar matches exactos en vocabulario
        for term in self.vocabulary.domain_synonyms.keys():
            if term.lower() in clean_query:
                candidates.append(term)
        
        # Buscar acrónimos
        words = clean_query.split()
        for word in words:
            word_clean = re.sub(r'[^\w]', '', word).upper()
            if word_clean in self.vocabulary.acronym_expansions:
                candidates.append(word_clean)
        
        # Buscar términos contextuales si tenemos intent
        # (se implementará en _generate_expansions)
        
        return list(set(candidates))  # Eliminar duplicados
    
    def _generate_expansions(self, candidates: List[str], intent_type: Optional[IntentType]) -> List[str]:
        """Genera términos de expansión para candidatos identificados"""
        expansions = []
        
        # Expansiones por dominio
        for candidate in candidates:
            candidate_lower = candidate.lower()
            
            # Buscar en sinónimos de dominio
            if candidate_lower in self.vocabulary.domain_synonyms:
                domain_expansions = self.vocabulary.domain_synonyms[candidate_lower]
                expansions.extend(domain_expansions)
            
            # Buscar en expansiones de acrónimos
            if candidate.upper() in self.vocabulary.acronym_expansions:
                acronym_expansions = self.vocabulary.acronym_expansions[candidate.upper()]
                expansions.extend(acronym_expansions)
        
        # Expansiones contextuales por intent
        if intent_type and intent_type in self.vocabulary.contextual_variations:
            contextual_dict = self.vocabulary.contextual_variations[intent_type]
            for candidate in candidates:
                candidate_lower = candidate.lower()
                if candidate_lower in contextual_dict:
                    contextual_expansions = contextual_dict[candidate_lower]
                    expansions.extend(contextual_expansions)
        
        return list(set(expansions))  # Eliminar duplicados
    
    def _filter_and_rank_expansions(self, expansions: List[str], original_query: str, 
                                   intent_type: Optional[IntentType]) -> List[str]:
        """Filtra y rankea expansiones según relevancia y estrategia"""
        if not expansions:
            return []
        
        # Eliminar términos que ya están en la consulta original
        original_words = set(original_query.lower().split())
        filtered = [exp for exp in expansions if exp.lower() not in original_words]
        
        # Aplicar estrategia de expansión
        strategy = ExpansionStrategy(self.expansion_strategy)
        
        if strategy == ExpansionStrategy.CONSERVATIVE:
            max_terms = min(3, self.max_expansion_terms)
        elif strategy == ExpansionStrategy.MODERATE:
            max_terms = min(6, self.max_expansion_terms)
        else:  # COMPREHENSIVE
            max_terms = self.max_expansion_terms
        
        # Rankear por relevancia (simple: términos más cortos primero, luego alfabético)
        ranked = sorted(filtered, key=lambda x: (len(x), x.lower()))
        
        return ranked[:max_terms]
    
    def _build_final_query(self, original_query: str, expansions: List[str], 
                          protected_terms: List[str]) -> str:
        """Construye la consulta final combinando original + expansiones"""
        if not expansions:
            return original_query
        
        # Estrategia simple: agregar términos expandidos al final
        expansion_text = " " + " ".join(expansions)
        final_query = original_query + expansion_text
        
        return final_query.strip()


# Instancia global para uso en toda la aplicación
query_expander = QueryExpander()