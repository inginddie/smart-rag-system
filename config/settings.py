# -*- coding: utf-8 -*-
import os
from pathlib import Path
from typing import Dict, Optional, List

from pydantic import Field

try:
    from pydantic_settings import BaseSettings
except (
    ImportError
):  # pragma: no cover - fallback for environments without pydantic_settings
    from pydantic import BaseSettings
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback if python-dotenv is missing

    def load_dotenv(*args, **kwargs):
        return False


load_dotenv()


class Settings(BaseSettings):
    """Configuración centralizada con Query Advisor y Analytics"""

    # OpenAI Configuration
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")

    # Modelos disponibles para selección inteligente
    simple_model: str = Field(default="gpt-4o-mini", env="SIMPLE_MODEL")
    complex_model: str = Field(default="gpt-4o", env="COMPLEX_MODEL")
    default_model: str = Field(default="gpt-4o-mini", env="DEFAULT_MODEL")

    # Precios por cada 1000 tokens de los modelos
    model_prices: Dict[str, float] = Field(
        default={"gpt-4o": 0.02, "gpt-4o-mini": 0.01}
    )

    # COMPATIBILIDAD: mantener model_name para código legacy
    @property
    def model_name(self) -> str:
        """Compatibilidad con código que usa model_name"""
        return self.default_model

    # Embedding
    embedding_model: str = Field(
        default="text-embedding-3-large", env="EMBEDDING_MODEL"
    )

    # Paths
    vector_db_path: str = Field(default="./data/vector_db", env="VECTOR_DB_PATH")
    documents_path: str = Field(default="./data/documents", env="DOCUMENTS_PATH")
    trace_db_path: str = Field(default="./data/traces.db", env="TRACE_DB_PATH")

    # RAG Configuration
    chunk_size: int = Field(default=2200, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=440, env="CHUNK_OVERLAP")
    max_documents: int = Field(default=10, env="MAX_DOCUMENTS")

    # Model Selection Configuration
    enable_smart_selection: bool = Field(default=True, env="ENABLE_SMART_SELECTION")
    complexity_threshold: float = Field(default=0.6, env="COMPLEXITY_THRESHOLD")

    # Intent Detection Configuration
    enable_intent_detection: bool = Field(default=True, env="ENABLE_INTENT_DETECTION")
    intent_confidence_threshold: float = Field(default=0.6, env="INTENT_CONFIDENCE_THRESHOLD")
    intent_max_processing_time_ms: int = Field(default=200, env="INTENT_MAX_PROCESSING_TIME_MS")
    
    # Academic Keywords for Intent Classification
    intent_keywords: Dict[str, List[str]] = Field(
        default={
            "definition": [
                "what is", "define", "qué es", "definition of", "concept of",
                "meaning of", "explain", "explica", "significado de"
            ],
            "comparison": [
                "compare", "compara", "versus", "vs", "difference between",
                "diferencia entre", "advantages and disadvantages", "pros and cons",
                "ventajas y desventajas", "contrast", "contrasta"
            ],
            "state_of_art": [
                "state of the art", "estado del arte", "current approaches",
                "enfoques actuales", "latest research", "recent developments",
                "literatura actual", "survey of", "review of", "overview of"
            ],
            "gap_analysis": [
                "limitations", "limitaciones", "gaps", "brechas", "future work",
                "trabajo futuro", "research gaps", "what is missing",
                "qué falta", "open problems", "challenges", "desafíos"
            ]
        }
    )
    
    # Intent Pattern Weights (for scoring)
    intent_pattern_weights: Dict[str, float] = Field(
        default={
            "question_start": 0.8,
            "imperative": 0.9,
            "comparison_phrase": 0.85,
            "explicit_indicator": 0.95,
            "academic_verb": 0.7
        }
    )

    # Query Expansion Configuration
    enable_query_expansion: bool = Field(default=True, env="ENABLE_QUERY_EXPANSION")
    max_expansion_terms: int = Field(default=6, env="MAX_EXPANSION_TERMS")
    expansion_strategy: str = Field(default="moderate", env="EXPANSION_STRATEGY")
    expansion_max_processing_time_ms: int = Field(default=500, env="EXPANSION_MAX_PROCESSING_TIME_MS")
    
    # Query Expansion Display Options
    show_expanded_terms: bool = Field(default=True, env="SHOW_EXPANDED_TERMS")
    expansion_debug_mode: bool = Field(default=False, env="EXPANSION_DEBUG_MODE")

    # ======= QUERY ADVISOR CONFIGURATION =======
    
    # Query Advisor Core Settings
    enable_query_advisor: bool = Field(default=True, env="ENABLE_QUERY_ADVISOR")
    advisor_effectiveness_threshold: float = Field(default=0.7, env="ADVISOR_EFFECTIVENESS_THRESHOLD")
    advisor_max_suggestions: int = Field(default=3, env="ADVISOR_MAX_SUGGESTIONS")
    advisor_max_tips: int = Field(default=2, env="ADVISOR_MAX_TIPS")
    
    # Effectiveness Scoring Weights
    advisor_scoring_weights: Dict[str, float] = Field(
        default={
            "intent_confidence": 0.3,
            "context_quality": 0.4,
            "query_specificity": 0.2,
            "expansion_effectiveness": 0.1
        }
    )
    
    # Suggestion Generation Settings
    advisor_suggestion_priority_weights: Dict[str, float] = Field(
        default={
            "specificity_improvements": 0.9,
            "context_additions": 0.8,
            "structure_fixes": 0.7,
            "terminology_enhancements": 0.6
        }
    )
    
    # Usage Analytics Configuration
    enable_usage_analytics: bool = Field(default=True, env="ENABLE_USAGE_ANALYTICS")
    analytics_retention_days: int = Field(default=30, env="ANALYTICS_RETENTION_DAYS")
    analytics_storage_path: str = Field(default="./data/usage_analytics.json", env="ANALYTICS_STORAGE_PATH")
    analytics_auto_save_interval: int = Field(default=10, env="ANALYTICS_AUTO_SAVE_INTERVAL")
    
    # Pattern Recognition Settings
    analytics_min_samples_for_pattern: int = Field(default=3, env="ANALYTICS_MIN_SAMPLES_FOR_PATTERN")
    analytics_success_threshold: float = Field(default=0.7, env="ANALYTICS_SUCCESS_THRESHOLD")
    
    # Recommendation Engine Settings
    enable_improvement_recommendations: bool = Field(default=True, env="ENABLE_IMPROVEMENT_RECOMMENDATIONS")
    recommendation_effectiveness_threshold: float = Field(default=0.6, env="RECOMMENDATION_EFFECTIVENESS_THRESHOLD")
    recommendation_adoption_threshold: float = Field(default=0.4, env="RECOMMENDATION_ADOPTION_THRESHOLD")
    
    # UI Display Settings for Query Advisor
    show_effectiveness_score: bool = Field(default=True, env="SHOW_EFFECTIVENESS_SCORE")
    show_suggestion_reasoning: bool = Field(default=True, env="SHOW_SUGGESTION_REASONING")
    show_contextual_tips: bool = Field(default=True, env="SHOW_CONTEXTUAL_TIPS")
    show_analytics_summary: bool = Field(default=True, env="SHOW_ANALYTICS_SUMMARY")
    
    # Advanced Query Advisor Features
    enable_learning_from_feedback: bool = Field(default=True, env="ENABLE_LEARNING_FROM_FEEDBACK")
    enable_personalized_suggestions: bool = Field(default=False, env="ENABLE_PERSONALIZED_SUGGESTIONS")
    advisor_debug_mode: bool = Field(default=False, env="ADVISOR_DEBUG_MODE")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # UI Configuration
    share_gradio: bool = Field(default=False, env="SHARE_GRADIO")
    server_port: int = Field(default=7860, env="SERVER_PORT")

    # Observability & SLA
    metrics_port: int = Field(default=8000, env="METRICS_PORT")
    ingest_sla_ms: int = Field(default=1000, env="INGEST_SLA_MS")
    embed_sla_ms: int = Field(default=1000, env="EMBED_SLA_MS")
    chunk_sla_ms: int = Field(default=1000, env="CHUNK_SLA_MS")
    search_sla_ms: int = Field(default=1000, env="SEARCH_SLA_MS")
    synthesize_sla_ms: int = Field(default=2000, env="SYNTHESIZE_SLA_MS")
    
    # Query Advisor SLA Settings
    advisor_analysis_sla_ms: int = Field(default=300, env="ADVISOR_ANALYSIS_SLA_MS")
    advisor_suggestion_sla_ms: int = Field(default=200, env="ADVISOR_SUGGESTION_SLA_MS")
    analytics_processing_sla_ms: int = Field(default=100, env="ANALYTICS_PROCESSING_SLA_MS")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    # ======= QUERY ADVISOR UTILITY METHODS =======
    
    def get_advisor_config(self) -> Dict:
        """Obtiene configuración específica del Query Advisor"""
        return {
            "enabled": self.enable_query_advisor,
            "effectiveness_threshold": self.advisor_effectiveness_threshold,
            "max_suggestions": self.advisor_max_suggestions,
            "max_tips": self.advisor_max_tips,
            "scoring_weights": self.advisor_scoring_weights,
            "suggestion_weights": self.advisor_suggestion_priority_weights,
            "debug_mode": self.advisor_debug_mode
        }
    
    def get_analytics_config(self) -> Dict:
        """Obtiene configuración específica de Analytics"""
        return {
            "enabled": self.enable_usage_analytics,
            "retention_days": self.analytics_retention_days,
            "storage_path": self.analytics_storage_path,
            "auto_save_interval": self.analytics_auto_save_interval,
            "min_samples_for_pattern": self.analytics_min_samples_for_pattern,
            "success_threshold": self.analytics_success_threshold
        }
    
    def get_ui_display_config(self) -> Dict:
        """Obtiene configuración de display UI para Query Advisor"""
        return {
            "show_effectiveness_score": self.show_effectiveness_score,
            "show_suggestion_reasoning": self.show_suggestion_reasoning,
            "show_contextual_tips": self.show_contextual_tips,
            "show_analytics_summary": self.show_analytics_summary
        }
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Verifica si una feature específica está habilitada"""
        feature_flags = {
            "query_advisor": self.enable_query_advisor,
            "usage_analytics": self.enable_usage_analytics,
            "improvement_recommendations": self.enable_improvement_recommendations,
            "learning_from_feedback": self.enable_learning_from_feedback,
            "personalized_suggestions": self.enable_personalized_suggestions,
            "intent_detection": self.enable_intent_detection,
            "query_expansion": self.enable_query_expansion,
            "smart_selection": self.enable_smart_selection
        }
        
        return feature_flags.get(feature, False)
    
    def get_sla_config(self) -> Dict:
        """Obtiene todas las configuraciones SLA incluyendo Query Advisor"""
        return {
            "ingest_ms": self.ingest_sla_ms,
            "embed_ms": self.embed_sla_ms,
            "chunk_ms": self.chunk_sla_ms,
            "search_ms": self.search_sla_ms,
            "synthesize_ms": self.synthesize_sla_ms,
            "advisor_analysis_ms": self.advisor_analysis_sla_ms,
            "advisor_suggestion_ms": self.advisor_suggestion_sla_ms,
            "analytics_processing_ms": self.analytics_processing_sla_ms
        }
    
    def validate_advisor_settings(self) -> List[str]:
        """Valida configuraciones del Query Advisor y retorna warnings"""
        warnings = []
        
        if not 0.0 <= self.advisor_effectiveness_threshold <= 1.0:
            warnings.append("advisor_effectiveness_threshold should be between 0.0 and 1.0")
        
        if not 0.0 <= self.analytics_success_threshold <= 1.0:
            warnings.append("analytics_success_threshold should be between 0.0 and 1.0")
        
        total_weight = sum(self.advisor_scoring_weights.values())
        if not 0.9 <= total_weight <= 1.1:
            warnings.append(f"advisor_scoring_weights should sum to ~1.0, currently: {total_weight}")
        
        if self.advisor_analysis_sla_ms < 50:
            warnings.append("advisor_analysis_sla_ms too low, may cause frequent SLA breaches")
        
        if self.analytics_retention_days < 1:
            warnings.append("analytics_retention_days should be at least 1")
        
        return warnings


# Instancia global de configuración
settings = Settings()