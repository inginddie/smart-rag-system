#!/usr/bin/env python3
"""Memory Manager - Orquesta memoria conversacional y semántica"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from src.memory.conversation import ConversationMemory
from src.memory.semantic import SemanticMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """Gestor unificado de memoria conversacional y semántica"""
    
    def __init__(self, max_conversation_length=50, max_semantic_memories=100, conversation_ttl_days=30):
        self.conversation_memory = ConversationMemory(max_conversation_length=max_conversation_length, ttl_days=conversation_ttl_days)
        self.semantic_memory = SemanticMemory(max_memories=max_semantic_memories)
        logger.info("MemoryManager initialized")
    
    def add_message(self, session_id, role, content, metadata=None):
        self.conversation_memory.add_to_conversation(session_id=session_id, role=role, content=content, metadata=metadata)
    
    def get_conversation_history(self, session_id, limit=None):
        return self.conversation_memory.get_conversation_history(session_id=session_id, limit=limit)
    
    def get_recent_context(self, session_id, max_messages=5):
        return self.conversation_memory.get_recent_context(session_id=session_id, max_messages=max_messages)
    
    def store_memory(self, agent_id, key, value, context=None, importance=1.0):
        content = f"[{agent_id}] {key}: {value}"
        if context:
            content += f" | Context: {context}"
        metadata = {'agent_id': agent_id, 'key': key, 'value': value, 'context': context}
        return self.semantic_memory.add_memory(content=content, metadata=metadata, importance=importance)
    
    def get_memory(self, agent_id, key, context=None):
        query = f"[{agent_id}] {key}"
        if context:
            query += f" {context}"
        results = self.semantic_memory.retrieve_similar(query, top_k=1)
        if results:
            memory, score = results[0]
            if memory.metadata.get('agent_id') == agent_id and memory.metadata.get('key') == key:
                return memory.metadata.get('value')
        return None
    
    def search_memories(self, query, agent_id=None, top_k=5):
        results = self.semantic_memory.retrieve_similar(query, top_k=top_k * 2)
        if agent_id:
            results = [(mem, score) for mem, score in results if mem.metadata.get('agent_id') == agent_id]
        formatted = []
        for memory, score in results[:top_k]:
            formatted.append({
                'content': memory.content,
                'score': score,
                'metadata': memory.metadata,
                'timestamp': memory.timestamp,
                'access_count': memory.access_count
            })
        return formatted
    
    def clear_session(self, session_id):
        return self.conversation_memory.clear_session(session_id)
    
    def get_all_sessions(self):
        return self.conversation_memory.get_all_sessions()
    
    def clear_all_memories(self):
        self.semantic_memory.clear()
        for session_id in self.get_all_sessions():
            self.clear_session(session_id)
        logger.info("Cleared all memories")
    
    def get_stats(self):
        return {
            'conversation': self.conversation_memory.get_stats(),
            'semantic': self.semantic_memory.get_stats(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_session_summary(self, session_id):
        history = self.get_conversation_history(session_id)
        metadata = self.conversation_memory.get_session_metadata(session_id)
        if not history:
            return {'session_id': session_id, 'exists': False}
        user_messages = [m for m in history if m['role'] == 'user']
        assistant_messages = [m for m in history if m['role'] == 'assistant']
        return {
            'session_id': session_id,
            'exists': True,
            'total_messages': len(history),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'metadata': metadata,
            'first_message': history[0] if history else None,
            'last_message': history[-1] if history else None
        }
