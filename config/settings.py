# -*- coding: utf-8 -*-
import os
from pathlib import Path
from typing import Dict, Optional

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
    PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseSettings, Field
    PYDANTIC_V2 = False

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

load_dotenv()

class Settings(BaseSettings):
    """Configuración centralizada con selección inteligente de modelos"""

    # OpenAI Configuration
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # Modelos disponibles para selección inteligente
    simple_model: str = Field(default="gpt-4o-mini", alias="SIMPLE_MODEL")
    complex_model: str = Field(default="gpt-4o", alias="COMPLEX_MODEL")
    default_model: str = Field(default="gpt-4o-mini", alias="DEFAULT_MODEL")

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
        default="text-embedding-3-large", alias="EMBEDDING_MODEL"
    )

    # Paths
    vector_db_path: str = Field(default="./data/vector_db", alias="VECTOR_DB_PATH")
    documents_path: str = Field(default="./data/documents", alias="DOCUMENTS_PATH")
    trace_db_path: str = Field(default="./data/traces.db", alias="TRACE_DB_PATH")

    # RAG Configuration
    chunk_size: int = Field(default=2200, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=440, alias="CHUNK_OVERLAP")
    max_documents: int = Field(default=10, alias="MAX_DOCUMENTS")

    # Model Selection Configuration
    enable_smart_selection: bool = Field(default=True, alias="ENABLE_SMART_SELECTION")
    complexity_threshold: float = Field(default=0.6, alias="COMPLEXITY_THRESHOLD")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # UI Configuration
    share_gradio: bool = Field(default=False, alias="SHARE_GRADIO")
    server_port: int = Field(default=7860, alias="SERVER_PORT")

    # Expert/Debug UI Configuration
    show_model_info_in_ui: bool = Field(default=False, alias="SHOW_MODEL_INFO_UI")
    expert_mode: bool = Field(default=False, alias="EXPERT_MODE")
    show_technical_errors: bool = Field(default=False, alias="SHOW_TECHNICAL_ERRORS")

    # Observability & SLA
    metrics_port: int = Field(default=8000, alias="METRICS_PORT")
    ingest_sla_ms: int = Field(default=1000, alias="INGEST_SLA_MS")
    embed_sla_ms: int = Field(default=1000, alias="EMBED_SLA_MS")
    chunk_sla_ms: int = Field(default=1000, alias="CHUNK_SLA_MS")
    search_sla_ms: int = Field(default=1000, alias="SEARCH_SLA_MS")
    synthesize_sla_ms: int = Field(default=2000, alias="SYNTHESIZE_SLA_MS")

    if PYDANTIC_V2:
        model_config = {
            "env_file": ".env",
            "case_sensitive": False,
            "extra": "ignore"
        }
    else:
        class Config:
            env_file = ".env"
            case_sensitive = False
            extra = "ignore"

# Instancia global de configuración
settings = Settings()