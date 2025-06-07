# -*- coding: utf-8 -*-
import os
from typing import Optional
from pydantic import Field
try:
    from pydantic_settings import BaseSettings
except ImportError:  # pragma: no cover - fallback for environments without pydantic_settings
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
    
    # COMPATIBILIDAD: mantener model_name para código legacy
    @property
    def model_name(self) -> str:
        """Compatibilidad con código que usa model_name"""
        return self.default_model
    
    # Embedding
    embedding_model: str = Field(default="text-embedding-3-large", env="EMBEDDING_MODEL")
    
    # Paths
    vector_db_path: str = Field(default="./data/vector_db", env="VECTOR_DB_PATH")
    documents_path: str = Field(default="./data/documents", env="DOCUMENTS_PATH")
    
    # RAG Configuration
    chunk_size: int = Field(default=2200, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=440, env="CHUNK_OVERLAP")
    max_documents: int = Field(default=10, env="MAX_DOCUMENTS")
    
    # Model Selection Configuration
    enable_smart_selection: bool = Field(default=True, env="ENABLE_SMART_SELECTION")
    complexity_threshold: float = Field(default=0.6, env="COMPLEXITY_THRESHOLD")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # UI Configuration
    share_gradio: bool = Field(default=False, env="SHARE_GRADIO")
    server_port: int = Field(default=7860, env="SERVER_PORT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Permitir campos extra para compatibilidad
        extra = "ignore"

# Instancia global de configuración
settings = Settings()