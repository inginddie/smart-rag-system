# -*- coding: utf-8 -*-
from typing import Optional
try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:  # pragma: no cover - optional dependency
    OpenAIEmbeddings = None  # type: ignore
from config.settings import settings
from src.utils.logger import setup_logger
from src.utils.exceptions import EmbeddingException
from src.utils.tracing import get_current_tracer
from src.utils.metrics import record_latency
import time

logger = setup_logger()

class EmbeddingManager:
    """Maneja los modelos de embedding"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.embedding_model
        self._embeddings = None
        
    @property
    def embeddings(self):
        """Lazy loading de embeddings"""
        if OpenAIEmbeddings is None:
            raise EmbeddingException(
                "OpenAIEmbeddings dependency is required but not installed"
            )

        if self._embeddings is None:
            try:
                self._embeddings = OpenAIEmbeddings(
                    model=self.model_name,
                    openai_api_key=settings.openai_api_key,
                )
                logger.info(
                    f"Initialized embeddings with model: {self.model_name}"
                )
            except Exception as e:
                logger.error(f"Error initializing embeddings: {e}")
                raise EmbeddingException(
                    f"Failed to initialize embeddings: {e}"
                )
        
        return self._embeddings
    
    def embed_query(self, text: str) -> list[float]:
        """Genera embedding para una consulta"""
        tracer = get_current_tracer()
        span = tracer.start_span("embed") if tracer else None
        start = time.perf_counter()
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise EmbeddingException(f"Failed to embed query: {e}")
        finally:
            duration = (time.perf_counter() - start) * 1000
            record_latency("embed", duration, settings.embed_sla_ms)
            if tracer and span:
                tracer.end_span(span, "success")
