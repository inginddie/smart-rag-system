# -*- coding: utf-8 -*-
"""
Embeddings con soporte para modelos locales
"""
from typing import List
from config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger()

def get_embeddings():
    """Obtiene el modelo de embeddings configurado con fallback a local"""
    
    # Try OpenAI first if API key is valid
    if settings.openai_api_key and len(settings.openai_api_key) > 20:
        try:
            from langchain_openai import OpenAIEmbeddings
            embeddings = OpenAIEmbeddings(
                model=settings.embedding_model,
                openai_api_key=settings.openai_api_key
            )
            logger.info(f"Initialized OpenAI embeddings with model: {settings.embedding_model}")
            return embeddings
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI embeddings: {e}")
            logger.info("Falling back to local embeddings...")
    
    # Fallback to local embeddings
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        logger.info(f"Initializing local embeddings with model: {model_name}")
        
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        logger.info("✅ Local embeddings initialized successfully")
        return embeddings
        
    except Exception as e:
        logger.error(f"Failed to initialize local embeddings: {e}")
        raise RuntimeError(f"Could not initialize any embedding model: {e}")

# Singleton instance
_embeddings_instance = None

def embeddings():
    """Get or create embeddings instance"""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = get_embeddings()
    return _embeddings_instance

# Compatibility class for backward compatibility
class EmbeddingManager:
    """Manager class for embeddings (backward compatibility)"""
    
    def __init__(self):
        self._embeddings = None
    
    @property
    def embeddings(self):
        """Get embeddings instance"""
        if self._embeddings is None:
            self._embeddings = get_embeddings()
        return self._embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        return self.embeddings.embed_query(text)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        return self.embeddings.embed_documents(texts)
