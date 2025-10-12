#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para MemoryManager
"""

import pytest
from src.memory.manager import MemoryManager


class TestMemoryManager:
    """Tests para gestor de memoria"""
    
    @pytest.fixture
    def manager(self):
        """Fixture de memory manager"""
        return MemoryManager(
            max_conversation_length=10,
            max_semantic_memories=20
        )
    
    def test_initialization(self, manager):
        """Test: Inicialización correcta"""
        assert manager.conversation_memory is not None
        assert manager.semantic_memory is not None
    
    # ==================== Conversational Memory Tests ====================
    
    def test_add_message(self, manager):
        """Test: Añadir mensaje"""
        manager.add_message("session1", "user", "Hello")
        
        history = manager.get_conversation_history("session1")
        assert len(history) == 1
        assert history[0]['content'] == "Hello"
    
    def test_conversation_flow(self, manager):
        """Test: Flujo de conversación"""
        session_id = "test_session"
        
        manager.add_message(session_id, "user", "What is AI?")
        manager.add_message(session_id, "assistant", "AI is artificial intelligence")
        manager.add_message(session_id, "user", "Tell me more")
        
        history = manager.get_conversation_history(session_id)
        assert len(history) == 3
    
    def test_get_recent_context(self, manager):
        """Test: Obtener contexto reciente"""
        session_id = "test_session"
        
        manager.add_message(session_id, "user", "Question 1")
        manager.add_message(session_id, "assistant", "Answer 1")
        manager.add_message(session_id, "user", "Question 2")
        
        context = manager.get_recent_context(session_id, max_messages=2)
        
        assert "Question 2" in context
        assert "Answer 1" in context
    
    # ==================== Semantic Memory Tests ====================
    
    def test_store_and_retrieve_memory(self, manager):
        """Test: Almacenar y recuperar memoria"""
        manager.store_memory(
            agent_id="TestAgent",
            key="user_preference",
            value="Python",
            context="programming language"
        )
        
        result = manager.get_memory(
            agent_id="TestAgent",
            key="user_preference"
        )
        
        assert result == "Python"
    
    def test_search_memories(self, manager):
        """Test: Buscar memorias"""
        manager.store_memory("Agent1", "fact1", "Python is great", importance=0.8)
        manager.store_memory("Agent1", "fact2", "Java is popular", importance=0.7)
        manager.store_memory("Agent2", "fact3", "Python for data", importance=0.9)
        
        results = manager.search_memories("Python", top_k=2)
        
        assert len(results) > 0
        assert any("Python" in r['content'] for r in results)
    
    def test_search_memories_by_agent(self, manager):
        """Test: Buscar memorias por agente"""
        manager.store_memory("Agent1", "fact1", "Data 1")
        manager.store_memory("Agent2", "fact2", "Data 2")
        
        results = manager.search_memories("Data", agent_id="Agent1", top_k=5)
        
        # Solo debe retornar memorias de Agent1
        for result in results:
            assert result['metadata']['agent_id'] == "Agent1"
    
    def test_memory_not_found(self, manager):
        """Test: Memoria no encontrada"""
        result = manager.get_memory("NonExistent", "key")
        assert result is None
    
    # ==================== Session Management Tests ====================
    
    def test_multiple_sessions(self, manager):
        """Test: Múltiples sesiones"""
        manager.add_message("session1", "user", "Hello 1")
        manager.add_message("session2", "user", "Hello 2")
        
        sessions = manager.get_all_sessions()
        assert len(sessions) == 2
        assert "session1" in sessions
        assert "session2" in sessions
    
    def test_clear_session(self, manager):
        """Test: Limpiar sesión"""
        manager.add_message("test_session", "user", "Hello")
        
        result = manager.clear_session("test_session")
        
        assert result is True
        assert "test_session" not in manager.get_all_sessions()
    
    def test_clear_all_memories(self, manager):
        """Test: Limpiar todas las memorias"""
        # Añadir datos
        manager.add_message("session1", "user", "Hello")
        manager.store_memory("Agent1", "key1", "value1")
        
        manager.clear_all_memories()
        
        assert len(manager.get_all_sessions()) == 0
        assert len(manager.semantic_memory.get_all_memories()) == 0
    
    # ==================== Statistics Tests ====================
    
    def test_get_stats(self, manager):
        """Test: Estadísticas completas"""
        manager.add_message("session1", "user", "Hello")
        manager.store_memory("Agent1", "key1", "value1")
        
        stats = manager.get_stats()
        
        assert 'conversation' in stats
        assert 'semantic' in stats
        assert 'timestamp' in stats
        assert stats['conversation']['total_sessions'] == 1
        assert stats['semantic']['total_memories'] == 1
    
    def test_get_session_summary(self, manager):
        """Test: Resumen de sesión"""
        session_id = "test_session"
        
        manager.add_message(session_id, "user", "Question 1")
        manager.add_message(session_id, "assistant", "Answer 1")
        manager.add_message(session_id, "user", "Question 2")
        
        summary = manager.get_session_summary(session_id)
        
        assert summary['exists'] is True
        assert summary['total_messages'] == 3
        assert summary['user_messages'] == 2
        assert summary['assistant_messages'] == 1
        assert summary['first_message']['content'] == "Question 1"
        assert summary['last_message']['content'] == "Question 2"
    
    def test_session_summary_nonexistent(self, manager):
        """Test: Resumen de sesión inexistente"""
        summary = manager.get_session_summary("nonexistent")
        
        assert summary['exists'] is False
    
    # ==================== Integration Tests ====================
    
    def test_conversation_and_semantic_integration(self, manager):
        """Test: Integración de memoria conversacional y semántica"""
        session_id = "integration_test"
        
        # Conversación
        manager.add_message(session_id, "user", "I like Python")
        manager.add_message(session_id, "assistant", "Great choice!")
        
        # Almacenar preferencia en memoria semántica
        manager.store_memory(
            agent_id="PreferenceAgent",
            key="language_preference",
            value="Python",
            context="User stated preference"
        )
        
        # Verificar ambas memorias
        history = manager.get_conversation_history(session_id)
        preference = manager.get_memory("PreferenceAgent", "language_preference")
        
        assert len(history) == 2
        assert preference == "Python"
    
    def test_memory_with_metadata(self, manager):
        """Test: Memoria con metadata"""
        manager.add_message(
            "test_session",
            "user",
            "Hello",
            metadata={'source': 'test', 'confidence': 0.9}
        )
        
        history = manager.get_conversation_history("test_session")
        assert history[0]['metadata']['source'] == 'test'
