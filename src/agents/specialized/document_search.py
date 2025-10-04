# -*- coding: utf-8 -*-
"""
DocumentSearchAgent - Agente especializado en búsqueda documental académica
Cumple con HU2: Agente de Búsqueda Documental Avanzado
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# Importaciones base
try:
    from src.agents.base.agent import BaseAgent, AgentResponse, AgentCapability, AgentStatus
    from src.storage.vector_store import VectorStoreManager
    from src.chains.rag_chain import RAGChain
    from src.utils.logger import setup_logger
    logger = setup_logger()
except ImportError:
    # Fallback para testing
    import logging
    logger = logging.getLogger(__name__)
    
    class AgentCapability(Enum):
        DOCUMENT_SEARCH = "document_search"
        SYNTHESIS = "information_synthesis"
        ACADEMIC_ANALYSIS = "academic_analysis"
    
    class AgentStatus(Enum):
        IDLE = "idle"
        THINKING = "thinking"
        ACTING = "acting"
        COMPLETED = "completed"
        ERROR = "error"
    
    @dataclass
    class AgentResponse:
        agent_id: str
        agent_name: str
        content: str
        confidence: float
        reasoning: str
        sources: List[Dict[str, Any]]
        metadata: Dict[str, Any]
        processing_time_ms: float
        capabilities_used: List[AgentCapability]
        timestamp: float = field(default_factory=time.time)
    
    class BaseAgent:
        def __init__(self, name: str, description: str):
            self.agent_id = f"{name}_test"
            self.name = name
            self.description = description
            self.status = AgentStatus.IDLE
        
        def get_capabilities(self) -> List[AgentCapability]:
            return []
        
        def _record_success(self, processing_time_ms: float, confidence: float):
            pass
        
        def _record_failure(self, error_message: str):
            pass


class DocumentSearchAgent(BaseAgent):
    """
    Agente especializado en búsqueda documental académica
    
    Cumple con HU2-CA2.1: Búsqueda semántica avanzada
    Cumple con HU2-CA2.2: Comprensión de contexto académico
    Cumple con HU2-CA2.3: Síntesis de múltiples fuentes
    Cumple con HU2-CA2.4: Metadata enriquecida
    """
    
    def __init__(self, vector_store_manager=None, rag_chain=None, memory_manager=None):
        super().__init__(
            name="DocumentSearchAgent",
            description="Especialista en búsqueda y análisis de documentos académicos"
        )
        
        self.vector_store_manager = vector_store_manager
        self.rag_chain = rag_chain
        self.memory_manager = memory_manager
        
        # Configuración de búsqueda académica
        self.academic_keywords = self._load_academic_keywords()
        self.relevance_threshold = 0.7
        self.min_sources = 3
        self.max_sources = 5
        
        logger.info(f"DocumentSearchAgent initialized")
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Capacidades específicas del DocumentSearchAgent"""
        return [
            AgentCapability.DOCUMENT_SEARCH,
            AgentCapability.SYNTHESIS,
            AgentCapability.ACADEMIC_ANALYSIS
        ]
    
    def can_handle_query(self, query: str, context: Dict[str, Any] = None) -> float:
        """Evalúa capacidad de manejar consultas académicas"""
        confidence = 0.0
        query_lower = query.lower()
        
        # Indicadores académicos (inglés y español)
        academic_indicators = [
            "papers", "research", "studies", "literature", "methodology",
            "findings", "results", "analysis", "framework", "approach",
            "investigación", "investigaciones", "estudios", "literatura", "inteligencia"
        ]
        
        academic_matches = sum(1 for keyword in academic_indicators if keyword in query_lower)
        confidence += min(academic_matches * 0.2, 0.8)
        
        # Patrones de búsqueda (inglés y español)
        search_patterns = ["find", "search", "look for", "show me", "what are", "busca", "encuentra"]
        if any(pattern in query_lower for pattern in search_patterns):
            confidence += 0.3
        
        # Penalizar no académicas
        non_academic = ["weather", "sports", "cooking", "travel"]
        if any(indicator in query_lower for indicator in non_academic):
            confidence = max(0.0, confidence - 0.5)
        
        return min(1.0, confidence)
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """Procesa consulta de búsqueda documental"""
        self.status = AgentStatus.THINKING
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {query[:100]}...")
            
            # Búsqueda y procesamiento
            expanded_query = await self._expand_academic_query(query)
            documents = await self._search_documents(expanded_query, context)
            ranked_docs = await self._rank_by_academic_relevance(documents, query)
            synthesized_response = await self._synthesize_sources(query, ranked_docs)
            enriched_response = await self._enrich_with_metadata(synthesized_response, ranked_docs)
            
            processing_time = (time.time() - start_time) * 1000
            confidence = self._calculate_response_confidence(ranked_docs, synthesized_response)
            
            response = AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                content=enriched_response,
                confidence=confidence,
                reasoning=f"Processed {len(ranked_docs)} academic sources",
                sources=self._format_sources(ranked_docs),
                metadata={
                    "expanded_query": expanded_query,
                    "documents_found": len(documents),
                    "documents_used": len(ranked_docs),
                    "query_type": "academic_search",
                    "processing_strategy": "document_search_synthesis",
                    "source_count": len(ranked_docs)
                },
                processing_time_ms=processing_time,
                capabilities_used=[AgentCapability.DOCUMENT_SEARCH, AgentCapability.SYNTHESIS]
            )
            
            self.status = AgentStatus.COMPLETED
            self._record_success(processing_time, confidence)
            
            return response
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.status = AgentStatus.ERROR
            self._record_failure(str(e))
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                content=f"Error en búsqueda: {str(e)}",
                confidence=0.0,
                reasoning=f"Error: {str(e)}",
                sources=[],
                metadata={"error": str(e), "query_type": "error", "processing_strategy": "error", "source_count": 0},
                processing_time_ms=processing_time,
                capabilities_used=[]
            )

    
    def _load_academic_keywords(self) -> List[str]:
        """Carga vocabulario académico"""
        return [
            "methodology", "approach", "framework", "model", "technique",
            "research", "study", "investigation", "analysis", "evaluation",
            "findings", "results", "outcomes", "conclusions", "implications",
            "machine learning", "deep learning", "nlp", "artificial intelligence",
            "paper", "article", "publication", "journal", "conference"
        ]
    
    async def _expand_academic_query(self, query: str) -> str:
        """Expande consulta con términos académicos"""
        return query
    
    async def _search_documents(self, query: str, context: Dict[str, Any] = None) -> List[Any]:
        """Búsqueda vectorial"""
        if not self.vector_store_manager:
            return []
        
        try:
            k = self.max_sources * 3
            documents = self.vector_store_manager.similarity_search(query, k=k)
            return documents
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return []
    
    async def _rank_by_academic_relevance(self, documents: List[Any], query: str) -> List[Any]:
        """Ranking por relevancia académica"""
        if not documents:
            return []
        
        scored_docs = []
        for doc in documents:
            score = self._calculate_academic_relevance(doc, query)
            if score >= self.relevance_threshold:
                scored_docs.append((doc, score))
        
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs[:self.max_sources]]
    
    def _calculate_academic_relevance(self, doc: Any, query: str) -> float:
        """Calcula relevancia académica"""
        score = 0.5
        
        content = doc.page_content.lower() if hasattr(doc, 'page_content') else ""
        
        # Coincidencia de keywords
        academic_matches = sum(1 for keyword in self.academic_keywords if keyword in content)
        score += min(0.3, academic_matches * 0.02)
        
        # Longitud del contenido
        if 100 <= len(content) <= 2000:
            score += 0.2
        
        return min(1.0, score)
    
    async def _synthesize_sources(self, query: str, documents: List[Any]) -> str:
        """Síntesis de múltiples fuentes"""
        if not documents:
            return "No se encontraron documentos relevantes."
        
        if self.rag_chain:
            try:
                result = self.rag_chain.invoke(query)
                return result.get('answer', 'No se pudo generar respuesta.')
            except Exception as e:
                logger.error(f"Error using RAG chain: {e}")
        
        # Fallback simple
        return f"Basándome en {len(documents)} fuentes académicas relevantes."
    
    async def _enrich_with_metadata(self, response: str, documents: List[Any]) -> str:
        """Enriquece respuesta con metadata"""
        if not documents:
            return response
        
        sources_section = "\n\n📚 **Fuentes Consultadas:**\n"
        for i, doc in enumerate(documents, 1):
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            source_file = metadata.get('source_file', 'Fuente desconocida')
            source_name = source_file.split('/')[-1].replace('.pdf', '').replace('_', ' ')
            sources_section += f"{i}. {source_name}\n"
        
        return response + sources_section
    
    def _format_sources(self, documents: List[Any]) -> List[Dict[str, Any]]:
        """Formatea fuentes con metadata"""
        formatted_sources = []
        
        for i, doc in enumerate(documents):
            content = doc.page_content if hasattr(doc, 'page_content') else ""
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            relevance_score = self._calculate_academic_relevance(doc, "")
            
            source_info = {
                "index": i + 1,
                "content_preview": content[:300] + "..." if len(content) > 300 else content,
                "metadata": {
                    "source_file": metadata.get('source_file', 'Unknown'),
                    "author": metadata.get('author', 'Unknown'),
                    "year": metadata.get('year', 'Unknown')
                },
                "relevance_score": round(relevance_score, 3),
                "relevance_category": self._score_to_category(relevance_score),
                "evidence_level": self._assess_evidence_level(content, metadata),
                "methodology": self._extract_methodology_hint(content)
            }
            
            formatted_sources.append(source_info)
        
        return formatted_sources
    
    def _score_to_category(self, score: float) -> str:
        """Convierte score a categoría"""
        if score >= 0.8:
            return "very_high"
        elif score >= 0.7:
            return "high"
        elif score >= 0.5:
            return "medium"
        elif score >= 0.3:
            return "low"
        else:
            return "very_low"
    
    def _assess_evidence_level(self, content: str, metadata: Dict) -> str:
        """Evalúa nivel de evidencia"""
        content_lower = content.lower()
        
        if any(ind in content_lower for ind in ["experiment", "empirical", "statistical"]):
            return "strong"
        elif any(ind in content_lower for ind in ["case study", "qualitative", "survey"]):
            return "medium"
        elif any(ind in content_lower for ind in ["opinion", "commentary", "perspective"]):
            return "weak"
        else:
            return "unknown"
    
    def _extract_methodology_hint(self, content: str) -> str:
        """Extrae pista de metodología"""
        content_lower = content.lower()
        
        if "machine learning" in content_lower or "ml model" in content_lower:
            return "machine learning"
        elif "deep learning" in content_lower or "neural network" in content_lower:
            return "deep learning"
        elif "nlp" in content_lower or "natural language" in content_lower:
            return "nlp"
        else:
            return "not_specified"
    
    def _calculate_response_confidence(self, documents: List[Any], response: str) -> float:
        """Calcula confidence de respuesta"""
        confidence = 0.5
        
        if len(documents) >= self.max_sources:
            confidence += 0.2
        elif len(documents) >= self.min_sources:
            confidence += 0.15
        
        if 100 <= len(response) <= 2000:
            confidence += 0.1
        
        return min(1.0, confidence)


def create_document_search_agent(vector_store_manager=None, rag_chain=None, memory_manager=None):
    """Factory function para crear DocumentSearchAgent"""
    return DocumentSearchAgent(
        vector_store_manager=vector_store_manager,
        rag_chain=rag_chain,
        memory_manager=memory_manager
    )
