# -*- coding: utf-8 -*-
"""
Sistema de memoria distribuida para agentes.
Combina memoria a corto plazo (Redis) con memoria semántica (ChromaDB).
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import pickle
import hashlib
import time

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from src.storage.vector_store import VectorStoreManager
from src.utils.logger import setup_logger
from src.utils.exceptions import RAGException

logger = setup_logger()

@dataclass
class MemoryEntry:
    """Entrada individual en memoria"""
    key: str
    value: Any
    agent_id: str
    context: str
    timestamp: float
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class MemoryManager:
    """
    Gestor de memoria para agentes con soporte para:
    - Memoria a corto plazo (Redis)
    - Memoria semántica a largo plazo (ChromaDB)  
    - Cache de conversaciones
    - Memoria compartida entre agentes
    """
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379/0",
                 vector_store_manager: VectorStoreManager = None,
                 default_ttl: int = 3600):  # 1 hora por defecto
        
        self.default_ttl = default_ttl
        self.vector_store_manager = vector_store_manager or VectorStoreManager()
        
        # Inicializar Redis para memoria a corto plazo
        self._init_redis(redis_url)
        
        # Cache local para acceso rápido
        self._local_cache: Dict[str, MemoryEntry] = {}
        self._cache_max_size = 1000
        
        logger.info("MemoryManager initialized")
    
    def _init_redis(self, redis_url: str):
        """Inicializa conexión Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using local memory only")
            self.redis_client = None
            return
            
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using local memory only")
            self.redis_client = None
    
    def _generate_key(self, agent_id: str, key: str, context: str) -> str:
        """Genera clave única para memoria"""
        return f"agent:{agent_id}:ctx:{context}:key:{key}"
    
    def store_memory(self, 
                    agent_id: str, 
                    key: str, 
                    value: Any,
                    context: str = "general",
                    ttl: Optional[int] = None,
                    metadata: Dict[str, Any] = None) -> bool:
        """
        Almacena información en memoria a corto plazo
        """
        try:
            ttl = ttl or self.default_ttl
            expires_at = time.time() + ttl if ttl > 0 else None
            
            memory_entry = MemoryEntry(
                key=key,
                value=value,
                agent_id=agent_id,
                context=context,
                timestamp=time.time(),
                expires_at=expires_at,
                metadata=metadata
            )
            
            storage_key = self._generate_key(agent_id, key, context)
            
            # Almacenar en Redis si está disponible
            if self.redis_client:
                try:
                    serialized = json.dumps(asdict(memory_entry), default=str)
                    if ttl > 0:
                        self.redis_client.setex(storage_key, ttl, serialized)
                    else:
                        self.redis_client.set(storage_key, serialized)
                except Exception as e:
                    logger.error(f"Redis storage failed: {e}")
                    # Fallback a cache local
                    pass
            
            # Siempre almacenar en cache local también
            self._local_cache[storage_key] = memory_entry
            self._cleanup_local_cache()
            
            logger.debug(f"Stored memory: {agent_id}:{context}:{key}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    def get_memory(self, 
                  agent_id: str,
                  key: str, 
                  context: str = "general") -> Any:
        """
        Recupera información de memoria a corto plazo
        """
        storage_key = self._generate_key(agent_id, key, context)
        
        # Buscar primero en cache local
        if storage_key in self._local_cache:
            entry = self._local_cache[storage_key]
            if entry.expires_at is None or entry.expires_at > time.time():
                return entry.value
            else:
                # Entrada expirada
                del self._local_cache[storage_key]
        
        # Buscar en Redis
        if self.redis_client:
            try:
                serialized = self.redis_client.get(storage_key)
                if serialized:
                    entry_dict = json.loads(serialized)
                    entry = MemoryEntry(**entry_dict)
                    
                    # Agregar a cache local
                    self._local_cache[storage_key] = entry
                    return entry.value
                    
            except Exception as e:
                logger.error(f"Redis retrieval failed: {e}")
        
        return None
    
    def store_semantic_memory(self,
                            agent_id: str,
                            content: str,
                            metadata: Dict[str, Any] = None) -> bool:
        """
        Almacena información en memoria semántica (long-term)
        usando el vector store existente
        """
        try:
            from src.storage.document_processor import Document
            
            # Crear documento con metadata del agente
            doc_metadata = {
                "agent_id": agent_id,
                "memory_type": "semantic",
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            document = Document(
                page_content=content,
                metadata=doc_metadata
            )
            
            # Almacenar en vector store
            ids = self.vector_store_manager.add_documents([document])
            
            logger.debug(f"Stored semantic memory for {agent_id}")
            return len(ids) > 0
            
        except Exception as e:
            logger.error(f"Error storing semantic memory: {e}")
            return False
    
    def search_semantic_memory(self,
                              query: str,
                              agent_id: Optional[str] = None,
                              k: int = 5) -> List[Dict[str, Any]]:
        """
        Busca en memoria semántica usando similitud
        """
        try:
            # Buscar documentos similares
            results = self.vector_store_manager.similarity_search(query, k=k)
            
            # Filtrar por agente si se especifica
            filtered_results = []
            for i, doc in enumerate(results):
                if doc.metadata.get("memory_type") == "semantic":
                    if agent_id is None or doc.metadata.get("agent_id") == agent_id:
                        # Calcular relevance score real
                        relevance_score = self._calculate_memory_relevance(doc, query, position=i)
                        
                        filtered_results.append({
                            "content": doc.page_content,
                            "metadata": doc.metadata,
                            "relevance_score": round(relevance_score, 3)
                        })
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error searching semantic memory: {e}")
            return []
    
    def _calculate_memory_relevance(self, doc, query: str, position: int) -> float:
        """Calcula relevancia de una memoria basada en múltiples factores"""
        # Factor 1: Posición en resultados de vector similarity (0.0-0.4)
        # Los primeros resultados del vector store son más similares
        similarity_score = max(0.0, 0.4 * (1 - position / 10))
        
        # Factor 2: Freshness temporal (0.0-0.3)
        try:
            timestamp_str = doc.metadata.get("timestamp")
            if timestamp_str:
                from datetime import datetime
                memory_time = datetime.fromisoformat(timestamp_str)
                current_time = datetime.now()
                
                # Calcular días transcurridos
                days_elapsed = (current_time - memory_time).days
                
                # Memoria más reciente es más relevante (decay exponencial)
                if days_elapsed <= 1:
                    freshness_score = 0.3
                elif days_elapsed <= 7:
                    freshness_score = 0.2
                elif days_elapsed <= 30:
                    freshness_score = 0.1
                else:
                    freshness_score = 0.05
            else:
                freshness_score = 0.1  # Score neutral si no hay timestamp
        except:
            freshness_score = 0.1
        
        # Factor 3: Coincidencia de palabras clave (0.0-0.2)
        content_lower = doc.page_content.lower()
        query_lower = query.lower()
        
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())
        
        if query_words:
            keyword_overlap = len(query_words.intersection(content_words)) / len(query_words)
            keyword_score = min(0.2, keyword_overlap * 0.2)
        else:
            keyword_score = 0.0
        
        # Factor 4: Longitud y completitud del contenido (0.0-0.1)
        content_length = len(doc.page_content)
        if 20 <= content_length <= 500:
            content_score = 0.1
        elif content_length < 20:
            content_score = 0.02
        else:
            content_score = max(0.05, 0.1 * (500 / content_length))
        
        # Score total (0.0-1.0)
        total_score = similarity_score + freshness_score + keyword_score + content_score
        return min(1.0, total_score)
    
    def get_conversation_history(self, 
                               session_id: str,
                               limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene historial de conversación
        """
        try:
            history_key = f"conversation:{session_id}"
            
            if self.redis_client:
                # Obtener de Redis (lista)
                history = self.redis_client.lrange(history_key, -limit, -1)
                return [json.loads(entry) for entry in history]
            else:
                # Fallback: buscar en cache local
                cache_key = f"conv_hist:{session_id}"
                if cache_key in self._local_cache:
                    return self._local_cache[cache_key].value[-limit:]
                    
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            
        return []
    
    def add_to_conversation(self,
                          session_id: str, 
                          role: str,
                          content: str,
                          metadata: Dict[str, Any] = None):
        """
        Agrega entrada al historial de conversación
        """
        try:
            entry = {
                "role": role,
                "content": content,
                "timestamp": time.time(),
                "metadata": metadata or {}
            }
            
            history_key = f"conversation:{session_id}"
            
            if self.redis_client:
                # Agregar a lista en Redis
                self.redis_client.lpush(history_key, json.dumps(entry))
                # Mantener solo últimos 100 mensajes
                self.redis_client.ltrim(history_key, 0, 99)
                # Expirar después de 24 horas
                self.redis_client.expire(history_key, 86400)
            else:
                # Fallback: cache local
                cache_key = f"conv_hist:{session_id}"
                if cache_key in self._local_cache:
                    history = self._local_cache[cache_key].value
                else:
                    history = []
                
                history.append(entry)
                # Mantener solo últimos 100
                if len(history) > 100:
                    history = history[-100:]
                
                self._local_cache[cache_key] = MemoryEntry(
                    key=cache_key,
                    value=history,
                    agent_id="system",
                    context="conversation",
                    timestamp=time.time()
                )
                
        except Exception as e:
            logger.error(f"Error adding to conversation: {e}")
    
    def clear_agent_memory(self, agent_id: str, context: str = None):
        """
        Limpia memoria de un agente específico
        """
        try:
            pattern = f"agent:{agent_id}:*"
            if context:
                pattern = f"agent:{agent_id}:ctx:{context}:*"
            
            # Limpiar Redis
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            
            # Limpiar cache local
            keys_to_delete = [
                key for key in self._local_cache.keys() 
                if key.startswith(f"agent:{agent_id}")
            ]
            for key in keys_to_delete:
                del self._local_cache[key]
                
            logger.info(f"Cleared memory for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error clearing agent memory: {e}")
    
    def _cleanup_local_cache(self):
        """Limpia cache local si excede tamaño máximo"""
        if len(self._local_cache) > self._cache_max_size:
            # Eliminar entradas más antiguas
            sorted_entries = sorted(
                self._local_cache.items(),
                key=lambda x: x[1].timestamp
            )
            
            # Mantener solo las más recientes
            keep_count = int(self._cache_max_size * 0.8)
            to_keep = dict(sorted_entries[-keep_count:])
            
            self._local_cache.clear()
            self._local_cache.update(to_keep)
            
            logger.debug("Local cache cleaned up")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de memoria"""
        stats = {
            "local_cache_size": len(self._local_cache),
            "redis_available": self.redis_client is not None
        }
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats["redis_used_memory"] = info.get("used_memory_human", "unknown")
                stats["redis_connected_clients"] = info.get("connected_clients", 0)
            except:
                stats["redis_status"] = "error"
        
        return stats