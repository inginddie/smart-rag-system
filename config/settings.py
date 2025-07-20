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
    """Configuración centralizada con selección inteligente de modelos"""

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

    # ======= NUEVAS CONFIGURACIONES PARA QUERY EXPANSION =======
    
    # Query Expansion Configuration
    enable_query_expansion: bool = Field(default=True, env="ENABLE_QUERY_EXPANSION")
    max_expansion_terms: int = Field(default=6, env="MAX_EXPANSION_TERMS")
    expansion_strategy: str = Field(default="moderate", env="EXPANSION_STRATEGY")
    expansion_max_processing_time_ms: int = Field(default=500, env="EXPANSION_MAX_PROCESSING_TIME_MS")
    
    # Query Expansion Display Options
    show_expanded_terms: bool = Field(default=True, env="SHOW_EXPANDED_TERMS")
    expansion_debug_mode: bool = Field(default=False, env="EXPANSION_DEBUG_MODE")

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

    class Config:
        env_file = ".env"
        case_sensitive = False
        # Permitir campos extra para compatibilidad
        extra = "ignore"


# Instancia global de configuración
settings = Settings()