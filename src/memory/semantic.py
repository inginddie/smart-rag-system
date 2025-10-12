#!/usr/bin/env python3
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    content: str
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    access_count: int = 0
    importance: float = 1.0

class SemanticMemory:
    def __init__(self, max_memories: int = 100, similarity_threshold: float = 0.7):
        self.max_memories = max_memories
        self.similarity_threshold = similarity_threshold
        self._memories: List[MemoryEntry] = []
        logger.info('initialized')
    
    def add_memory(self, content: str, embedding=None, metadata=None, importance=1.0):
        memory = MemoryEntry(content=content, embedding=embedding, metadata=metadata or {}, importance=importance)
        self._memories.append(memory)
        if len(self._memories) > self.max_memories:
            self._prune_memories()
        return memory.timestamp
    
    def retrieve_similar(self, query: str, query_embedding=None, top_k=5):
        if not self._memories:
            return []
        if query_embedding is None:
            return self._keyword_search(query, top_k)
        results = []
        for memory in self._memories:
            if memory.embedding is not None:
                similarity = self._cosine_similarity(query_embedding, memory.embedding)
                if similarity >= self.similarity_threshold:
                    memory.access_count += 1
                    results.append((memory, similarity))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _keyword_search(self, query, top_k):
        query_words = set(query.lower().split())
        results = []
        for memory in self._memories:
            content_words = set(memory.content.lower().split())
            overlap = len(query_words & content_words)
            if overlap > 0:
                score = overlap / len(query_words)
                memory.access_count += 1
                results.append((memory, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _cosine_similarity(self, vec1, vec2):
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))
    
    def _prune_memories(self):
        self._memories.sort(key=lambda m: (m.importance * (1 + m.access_count * 0.1)), reverse=True)
        self._memories = self._memories[:self.max_memories]
    
    def get_all_memories(self):
        return self._memories.copy()
    
    def clear(self):
        self._memories.clear()
    
    def get_stats(self):
        if not self._memories:
            return {'total_memories': 0, 'avg_importance': 0, 'avg_access_count': 0, 'max_memories': self.max_memories}
        return {
            'total_memories': len(self._memories),
            'avg_importance': float(np.mean([m.importance for m in self._memories])),
            'avg_access_count': float(np.mean([m.access_count for m in self._memories])),
            'max_memories': self.max_memories,
            'similarity_threshold': self.similarity_threshold
        }
