#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Memoria Conversacional
Gestiona el historial de conversaciones con persistencia
"""

import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import deque
import logging

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Gestiona la memoria conversacional con persistencia en memoria
    Mantiene historial de conversaciones por sesión
    """
    
    def __init__(self, max_conversation_length: int = 50, ttl_days: int = 30):
        """
        Inicializa el sistema de memoria conversacional
        
        Args:
            max_conversation_length: Máximo de intercambios por sesión
            ttl_days: Días de retención de conversaciones
        """
        self.max_conversation_length = max_conversation_length
        self.ttl_days = ttl_days
        self._conversations: Dict[str, deque] = {}
        self._metadata: Dict[str, Dict] = {}
        
        logger.info(f"ConversationMemory initialized (max_length={max_conversation_length}, ttl={ttl_days}d)")
    
    def add_to_conversation(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Añade un mensaje a la conversación
        
        Args:
            session_id: ID de la sesión
            role: Rol del mensaje ('user' o 'assistant')
            content: Contenido del mensaje
            metadata: Metadata adicional del mensaje
        """
        if session_id not in self._conversations:
            self._conversations[session_id] = deque(maxlen=self.max_conversation_length)
            self._metadata[session_id] = {
                'created_at': datetime.utcnow().isoformat(),
                'last_updated': datetime.utcnow().isoformat(),
                'message_count': 0
            }
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        self._conversations[session_id].append(message)
        self._metadata[session_id]['last_updated'] = datetime.utcnow().isoformat()
        self._metadata[session_id]['message_count'] += 1
        
        logger.debug(f"Added message to session {session_id}: role={role}, length={len(content)}")
    
    def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Obtiene el historial de conversación
        
        Args:
            session_id: ID de la sesión
            limit: Límite de mensajes a retornar (más recientes)
        
        Returns:
            Lista de mensajes ordenados cronológicamente
        """
        if session_id not in self._conversations:
            logger.warning(f"Session {session_id} not found")
            return []
        
        messages = list(self._conversations[session_id])
        
        if limit:
            messages = messages[-limit:]
        
        logger.debug(f"Retrieved {len(messages)} messages for session {session_id}")
        return messages
    
    def get_recent_context(
        self, 
        session_id: str, 
        max_messages: int = 5
    ) -> str:
        """
        Obtiene contexto reciente formateado para el LLM
        
        Args:
            session_id: ID de la sesión
            max_messages: Máximo de mensajes a incluir
        
        Returns:
            Contexto formateado como string
        """
        messages = self.get_conversation_history(session_id, limit=max_messages)
        
        if not messages:
            return ""
        
        context_parts = []
        for msg in messages:
            role = msg['role'].capitalize()
            content = msg['content']
            context_parts.append(f"{role}: {content}")
        
        return "\n\n".join(context_parts)
    
    def clear_session(self, session_id: str) -> bool:
        """
        Limpia una sesión específica
        
        Args:
            session_id: ID de la sesión a limpiar
        
        Returns:
            True si se limpió exitosamente
        """
        if session_id in self._conversations:
            del self._conversations[session_id]
            del self._metadata[session_id]
            logger.info(f"Cleared session {session_id}")
            return True
        
        logger.warning(f"Session {session_id} not found for clearing")
        return False
    
    def get_session_metadata(self, session_id: str) -> Optional[Dict]:
        """
        Obtiene metadata de una sesión
        
        Args:
            session_id: ID de la sesión
        
        Returns:
            Metadata de la sesión o None
        """
        return self._metadata.get(session_id)
    
    def get_all_sessions(self) -> List[str]:
        """
        Obtiene lista de todas las sesiones activas
        
        Returns:
            Lista de IDs de sesión
        """
        return list(self._conversations.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema de memoria
        
        Returns:
            Diccionario con estadísticas
        """
        total_messages = sum(
            len(conv) for conv in self._conversations.values()
        )
        
        return {
            'total_sessions': len(self._conversations),
            'total_messages': total_messages,
            'max_conversation_length': self.max_conversation_length,
            'ttl_days': self.ttl_days,
            'avg_messages_per_session': total_messages / len(self._conversations) if self._conversations else 0
        }
