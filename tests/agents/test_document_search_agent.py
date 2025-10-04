# -*- coding: utf-8 -*-
"""
Tests para DocumentSearchAgent
Cumple con Tarea 2.5: Tests para DocumentSearchAgent
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock

# Test básico sin dependencias complejas
def test_document_search_agent_creation():
    """Test creación básica del DocumentSearchAgent"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    
    assert agent.name == "DocumentSearchAgent"
    assert agent.description == "Especialista en búsqueda y análisis de documentos académicos"
    assert agent.relevance_threshold == 0.7
    assert agent.min_sources == 3
    assert agent.max_sources == 5

def test_document_search_agent_capabilities():
    """Test que el agente tiene las capacidades correctas"""
    from src.agents.specialized.document_search import DocumentSearchAgent, AgentCapability
    
    agent = DocumentSearchAgent()
    capabilities = agent.get_capabilities()
    
    assert AgentCapability.DOCUMENT_SEARCH in capabilities
    assert AgentCapability.SYNTHESIS in capabilities
    assert AgentCapability.ACADEMIC_ANALYSIS in capabilities
    assert len(capabilities) == 3

def test_can_handle_academic_query():
    """Test evaluación de consultas académicas"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    
    # Consulta académica clara
    score1 = agent.can_handle_query("find research papers on machine learning")
    assert score1 >= 0.7, f"Expected >=0.7 for academic query, got {score1}"
    
    # Consulta académica con términos técnicos
    score2 = agent.can_handle_query("search for studies on deep learning and nlp")
    assert score2 >= 0.5, f"Expected >=0.5 for technical query, got {score2}"
    
    # Consulta no académica
    score3 = agent.can_handle_query("what's the weather today")
    assert score3 < 0.3, f"Expected <0.3 for non-academic query, got {score3}"

def test_can_handle_query_spanish():
    """Test evaluación de consultas en español"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    
    score = agent.can_handle_query("busca investigaciones sobre inteligencia artificial")
    assert score > 0.5, f"Expected >0.5 for Spanish academic query, got {score}"

def test_academic_keywords_loaded():
    """Test que se cargan keywords académicos"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    keywords = agent._load_academic_keywords()
    
    assert len(keywords) > 0
    assert "methodology" in keywords
    assert "research" in keywords
    assert "machine learning" in keywords

@pytest.mark.asyncio
async def test_expand_academic_query():
    """Test expansión de consulta académica"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    
    # Query con término expandible
    expanded = await agent._expand_academic_query("find papers using method X")
    assert "method" in expanded.lower()
    assert len(expanded) >= len("find papers using method X")

@pytest.mark.asyncio
async def test_process_query_without_dependencies():
    """Test procesamiento básico sin dependencias externas"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    
    # Sin vector store, debe manejar gracefully
    response = await agent.process_query("test query")
    
    assert response.agent_name == "DocumentSearchAgent"
    assert response.confidence >= 0.0
    assert isinstance(response.sources, list)
    assert isinstance(response.metadata, dict)

def test_calculate_academic_relevance():
    """Test cálculo de relevancia académica"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    
    # Mock document con contenido académico
    mock_doc = Mock()
    mock_doc.page_content = "This research paper presents a methodology for machine learning analysis"
    mock_doc.metadata = {"source_file": "paper.pdf", "author": "Smith"}
    
    score = agent._calculate_academic_relevance(mock_doc, "machine learning")
    
    assert 0.0 <= score <= 1.0
    assert score > 0.5, "Academic document should have relevance >0.5"

def test_score_to_category():
    """Test conversión de score a categoría"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    
    assert agent._score_to_category(0.9) == "very_high"
    assert agent._score_to_category(0.75) == "high"
    assert agent._score_to_category(0.6) == "medium"
    assert agent._score_to_category(0.4) == "low"
    assert agent._score_to_category(0.2) == "very_low"

def test_assess_evidence_level():
    """Test evaluación de nivel de evidencia"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    
    # Evidencia fuerte
    strong_content = "This experiment shows statistical significance in the results"
    assert agent._assess_evidence_level(strong_content, {}) == "strong"
    
    # Evidencia media
    medium_content = "This case study analyzes the qualitative aspects"
    assert agent._assess_evidence_level(medium_content, {}) == "medium"
    
    # Evidencia débil
    weak_content = "In my opinion, this perspective suggests"
    assert agent._assess_evidence_level(weak_content, {}) == "weak"

def test_extract_methodology_hint():
    """Test extracción de pista de metodología"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    
    # Machine learning
    ml_content = "We trained a machine learning model for classification"
    assert agent._extract_methodology_hint(ml_content) == "machine learning"
    
    # Deep learning
    dl_content = "Using a deep neural network architecture"
    assert agent._extract_methodology_hint(dl_content) == "deep learning"
    
    # NLP
    nlp_content = "Natural language processing techniques were applied"
    assert agent._extract_methodology_hint(nlp_content) == "nlp"

def test_format_sources():
    """Test formateo de fuentes con metadata"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    
    # Mock documents
    mock_docs = []
    for i in range(3):
        doc = Mock()
        doc.page_content = f"Academic content {i} with research methodology"
        doc.metadata = {
            "source_file": f"paper_{i}.pdf",
            "author": f"Author {i}",
            "year": "2023"
        }
        mock_docs.append(doc)
    
    formatted = agent._format_sources(mock_docs)
    
    assert len(formatted) == 3
    assert all("relevance_score" in source for source in formatted)
    assert all("evidence_level" in source for source in formatted)
    assert all("methodology" in source for source in formatted)
    assert all("metadata" in source for source in formatted)

def test_calculate_response_confidence():
    """Test cálculo de confidence de respuesta"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    
    # Mock documents
    mock_docs = [Mock() for _ in range(5)]
    for doc in mock_docs:
        doc.page_content = "Academic research content"
        doc.metadata = {}
    
    response = "This is a comprehensive response based on multiple sources"
    
    confidence = agent._calculate_response_confidence(mock_docs, response)
    
    assert 0.0 <= confidence <= 1.0
    assert confidence > 0.5, "Response with 5 sources should have confidence >0.5"

@pytest.mark.asyncio
async def test_search_documents_without_vector_store():
    """Test búsqueda sin vector store (debe manejar gracefully)"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent(vector_store_manager=None)
    
    documents = await agent._search_documents("test query")
    
    assert isinstance(documents, list)
    assert len(documents) == 0

@pytest.mark.asyncio
async def test_synthesize_sources_empty():
    """Test síntesis con lista vacía de documentos"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    
    synthesis = await agent._synthesize_sources("test query", [])
    
    assert isinstance(synthesis, str)
    assert len(synthesis) > 0
    assert "no se encontraron" in synthesis.lower()

@pytest.mark.asyncio
async def test_synthesize_sources_with_docs():
    """Test síntesis con documentos"""
    from src.agents.specialized.document_search import DocumentSearchAgent
    
    agent = DocumentSearchAgent()
    
    # Mock documents
    mock_docs = []
    for i in range(3):
        doc = Mock()
        doc.page_content = f"Academic content {i} about machine learning research"
        doc.metadata = {"source_file": f"paper_{i}.pdf"}
        mock_docs.append(doc)
    
    synthesis = await agent._synthesize_sources("machine learning", mock_docs)
    
    assert isinstance(synthesis, str)
    assert len(synthesis) > 0

def test_factory_function():
    """Test factory function para crear agente"""
    from src.agents.specialized.document_search import create_document_search_agent
    
    agent = create_document_search_agent()
    
    assert agent is not None
    assert agent.name == "DocumentSearchAgent"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])