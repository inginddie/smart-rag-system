#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para SemanticMemory
"""

import pytest
import numpy as np
from src.memory.semantic import SemanticMemory, MemoryEntry


class TestSemanticMemory:
    """Tests para memoria semántica"""
    
    @pytest.fixture
    def memory(self):
        """Fixture de memoria semántica"""
        return SemanticMemory(max_memories=10, similarity_threshold=0.5)
    
    def test_initialization(self, memory):
        """Test: Inicialización correcta"""
        assert memory.max_memories == 10
        assert memory.similarity_threshold == 0.5
        assert len(memory.get_all_memories()) == 0
    
    def test_add_memory(self, memory):
        """Test: Añadir memoria"""
        memory_id = memory.add_memory(
            content="Python is a programming language",
            importance=0.8
        )
        
        assert memory_id is not None
        assert len(memory.get_all_memories()) == 1
    
    def test_add_memory_with_metadata(self, memory):
        """Test: Añadir memoria con metadata"""
        memory.add_memory(
            content="Test content",
            metadata={'source': 'test', 'type': 'fact'},
            importance=0.9
        )
        
        memories = memory.get_all_memories()
        assert memories[0].metadata['source'] == 'test'
        assert memories[0].importance == 0.9
    
    def test_keyword_search(self, memory):
        """Test: Búsqueda por keywords"""
        memory.add_memory("Python is great for data science")
        memory.add_memory("Java is used for enterprise applications")
        memory.add_memory("JavaScript runs in browsers")
        
        results = memory.retrieve_similar("Python data", top_k=2)
        
        assert len(results) > 0
        assert "Python" in results[0][0].content
    
    def test_retrieve_with_embeddings(self, memory):
        """Test: Recuperación con embeddings"""
        # Crear embeddings simulados
        emb1 = np.array([1.0, 0.0, 0.0])
        emb2 = np.array([0.9, 0.1, 0.0])  # Similar a emb1
        emb3 = np.array([0.0, 0.0, 1.0])  # Diferente
        
        memory.add_memory("Content 1", embedding=emb1)
        memory.add_memory("Content 2", embedding=emb2)
        memory.add_memory("Content 3", embedding=emb3)
        
        # Buscar con embedding similar a emb1
        query_emb = np.array([0.95, 0.05, 0.0])
        results = memory.retrieve_similar("query", query_embedding=query_emb, top_k=2)
        
        assert len(results) > 0
        # Los resultados más similares deben estar primero
        assert results[0][1] > 0.5  # Score de similitud alto
    
    def test_max_memories_pruning(self, memory):
        """Test: Poda cuando se excede el límite"""
        # Añadir más memorias que el límite
        for i in range(15):
            memory.add_memory(
                f"Memory {i}",
                importance=0.5 if i < 10 else 0.9  # Últimas 5 más importantes
            )
        
        memories = memory.get_all_memories()
        assert len(memories) == 10  # Debe respetar el límite
        
        # Las memorias más importantes deben permanecer
        contents = [m.content for m in memories]
        assert "Memory 14" in contents  # Alta importancia
    
    def test_access_count(self, memory):
        """Test: Contador de accesos"""
        memory.add_memory("Test content")
        
        # Realizar búsquedas
        memory.retrieve_similar("Test", top_k=1)
        memory.retrieve_similar("content", top_k=1)
        
        memories = memory.get_all_memories()
        assert memories[0].access_count >= 1
    
    def test_clear_memories(self, memory):
        """Test: Limpiar todas las memorias"""
        memory.add_memory("Memory 1")
        memory.add_memory("Memory 2")
        
        assert len(memory.get_all_memories()) == 2
        
        memory.clear()
        
        assert len(memory.get_all_memories()) == 0
    
    def test_get_stats(self, memory):
        """Test: Estadísticas del sistema"""
        memory.add_memory("Memory 1", importance=0.8)
        memory.add_memory("Memory 2", importance=0.6)
        
        # Realizar algunas búsquedas
        memory.retrieve_similar("Memory", top_k=2)
        
        stats = memory.get_stats()
        
        assert stats['total_memories'] == 2
        assert 'avg_importance' in stats
        assert 'avg_access_count' in stats
    
    def test_empty_memory_stats(self, memory):
        """Test: Estadísticas con memoria vacía"""
        stats = memory.get_stats()
        
        assert stats['total_memories'] == 0
        assert stats['avg_importance'] == 0
    
    def test_similarity_threshold(self, memory):
        """Test: Umbral de similitud"""
        emb1 = np.array([1.0, 0.0])
        emb2 = np.array([0.3, 0.7])  # Baja similitud
        
        memory.add_memory("Content 1", embedding=emb1)
        memory.add_memory("Content 2", embedding=emb2)
        
        # Buscar con embedding similar a emb1
        query_emb = np.array([0.9, 0.1])
        results = memory.retrieve_similar("query", query_embedding=query_emb, top_k=5)
        
        # Solo debe retornar memorias sobre el threshold
        for _, score in results:
            assert score >= memory.similarity_threshold
    
    def test_top_k_limit(self, memory):
        """Test: Límite de resultados top_k"""
        for i in range(10):
            memory.add_memory(f"Memory about Python {i}")
        
        results = memory.retrieve_similar("Python", top_k=3)
        
        assert len(results) <= 3
