#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para ConversationMemory
"""

import pytest
from src.memory.conversation import ConversationMemory


class TestConversationMemory:
    """Tests para memoria conversacional"""
    
    @pytest.fixture
    def memory(self):
        """Fixture de memoria conversacional"""
        return ConversationMemory(max_conversation_length=10)
    
    def test_initialization(self, memory):
        """Test: Inicialización correcta"""
        assert memory.max_conversation_length == 10
        assert memory.ttl_days == 30
        assert len(memory.get_all_sessions()) == 0
    
    def test_add_message(self, memory):
        """Test: Añadir mensaje a conversación"""
        memory.add_to_conversation(
            session_id="test_session",
            role="user",
            content="Hello"
        )
        
        history = memory.get_conversation_history("test_session")
        assert len(history) == 1
        assert history[0]['role'] == 'user'
        assert history[0]['content'] == 'Hello'
    
    def test_conversation_flow(self, memory):
        """Test: Flujo completo de conversación"""
        session_id = "test_session"
        
        # Usuario pregunta
        memory.add_to_conversation(session_id, "user", "What is AI?")
        
        # Asistente responde
        memory.add_to_conversation(session_id, "assistant", "AI is...")
        
        # Usuario pregunta de nuevo
        memory.add_to_conversation(session_id, "user", "Tell me more")
        
        history = memory.get_conversation_history(session_id)
        assert len(history) == 3
        assert history[0]['role'] == 'user'
        assert history[1]['role'] == 'assistant'
        assert history[2]['role'] == 'user'
    
    def test_max_conversation_length(self, memory):
        """Test: Límite de longitud de conversación"""
        session_id = "test_session"
        
        # Añadir más mensajes que el límite
        for i in range(15):
            memory.add_to_conversation(
                session_id,
                "user" if i % 2 == 0 else "assistant",
                f"Message {i}"
            )
        
        history = memory.get_conversation_history(session_id)
        assert len(history) == 10  # Debe respetar el límite
        assert history[0]['content'] == 'Message 5'  # Los primeros se eliminan
    
    def test_get_recent_context(self, memory):
        """Test: Obtener contexto reciente"""
        session_id = "test_session"
        
        memory.add_to_conversation(session_id, "user", "Question 1")
        memory.add_to_conversation(session_id, "assistant", "Answer 1")
        memory.add_to_conversation(session_id, "user", "Question 2")
        
        context = memory.get_recent_context(session_id, max_messages=2)
        
        assert "Question 2" in context
        assert "Answer 1" in context
        assert "Question 1" not in context  # Solo los 2 más recientes
    
    def test_multiple_sessions(self, memory):
        """Test: Múltiples sesiones independientes"""
        memory.add_to_conversation("session1", "user", "Hello from session 1")
        memory.add_to_conversation("session2", "user", "Hello from session 2")
        
        sessions = memory.get_all_sessions()
        assert len(sessions) == 2
        assert "session1" in sessions
        assert "session2" in sessions
        
        history1 = memory.get_conversation_history("session1")
        history2 = memory.get_conversation_history("session2")
        
        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0]['content'] != history2[0]['content']
    
    def test_clear_session(self, memory):
        """Test: Limpiar sesión"""
        memory.add_to_conversation("test_session", "user", "Hello")
        
        assert len(memory.get_all_sessions()) == 1
        
        result = memory.clear_session("test_session")
        
        assert result is True
        assert len(memory.get_all_sessions()) == 0
    
    def test_session_metadata(self, memory):
        """Test: Metadata de sesión"""
        memory.add_to_conversation("test_session", "user", "Hello")
        
        metadata = memory.get_session_metadata("test_session")
        
        assert metadata is not None
        assert 'created_at' in metadata
        assert 'last_updated' in metadata
        assert 'message_count' in metadata
        assert metadata['message_count'] == 1
    
    def test_get_stats(self, memory):
        """Test: Estadísticas del sistema"""
        memory.add_to_conversation("session1", "user", "Hello")
        memory.add_to_conversation("session1", "assistant", "Hi")
        memory.add_to_conversation("session2", "user", "Test")
        
        stats = memory.get_stats()
        
        assert stats['total_sessions'] == 2
        assert stats['total_messages'] == 3
        assert stats['avg_messages_per_session'] == 1.5
    
    def test_empty_session(self, memory):
        """Test: Sesión inexistente"""
        history = memory.get_conversation_history("nonexistent")
        assert history == []
        
        context = memory.get_recent_context("nonexistent")
        assert context == ""
    
    def test_message_with_metadata(self, memory):
        """Test: Mensaje con metadata"""
        memory.add_to_conversation(
            "test_session",
            "user",
            "Hello",
            metadata={'agent': 'TestAgent', 'confidence': 0.9}
        )
        
        history = memory.get_conversation_history("test_session")
        assert history[0]['metadata']['agent'] == 'TestAgent'
        assert history[0]['metadata']['confidence'] == 0.9
