# -*- coding: utf-8 -*-


class RAGException(Exception):
    """Excepción base para el sistema RAG"""

    pass


class VectorStoreException(RAGException):
    """Excepción para errores de la base vectorial"""

    pass


class DocumentProcessingException(RAGException):
    """Excepción para errores de procesamiento de documentos"""

    pass


class EmbeddingException(RAGException):
    """Excepción para errores de embedding"""

    pass


class ChainException(RAGException):
    """Excepción para errores en las cadenas RAG"""

    pass


class TracingException(RAGException):
    """Excepción para errores de trazado"""

    pass
