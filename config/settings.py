# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional
import sys

from pydantic import BaseSettings, Field, validator, ValidationError

try:
    from pydantic_settings import BaseSettings as SettingsBase
except ImportError:
    SettingsBase = BaseSettings

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        print("Advertencia: python-dotenv no está instalado, las variables de entorno no se cargarán desde .env", file=sys.stderr)
        return False

load_dotenv()


class Settings(SettingsBase):
    """Configuración centralizada con selección inteligente de modelos"""

    openai_api_key: str = Field(..., env="OPENAI_API_KEY", description="Clave API para OpenAI, no puede estar vacía")

    simple_model: str = Field(default="gpt-4o-mini", env="SIMPLE_MODEL", description="Modelo simple para tareas básicas")
    complex_model: str = Field(default="gpt-4o", env="COMPLEX_MODEL", description="Modelo complejo para tareas avanzadas")
    default_model: str = Field(default="gpt-4o-mini", env="DEFAULT_MODEL", description="Modelo por defecto")

    embedding_model: str = Field(
        default="text-embedding-3-large", env="EMBEDDING_MODEL", description="Modelo para embeddings"
    )

    vector_db_path: Optional[Path] = Field(default=Path("./data/vector_db"), env="VECTOR_DB_PATH", description="Ruta al directorio de la base de datos vectorial")
    documents_path: Optional[Path] = Field(default=Path("./data/documents"), env="DOCUMENTS_PATH", description="Ruta al directorio de documentos")

    @validator("openai_api_key")
    def openai_api_key_must_not_be_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError("La variable OPENAI_API_KEY no puede estar vacía.")
        return v

    @validator("vector_db_path", "documents_path", pre=True, always=True)
    def ensure_path_object(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v

    @validator("vector_db_path", "documents_path")
    def create_path_if_not_exists(cls, v):
        if v and not v.exists():
            try:
                v.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(f"No se pudo crear el directorio {v}: {e}")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


try:
    settings = Settings()
except ValidationError as e:
    print("Error en la configuración:", e, file=sys.stderr)
    sys.exit(1)
