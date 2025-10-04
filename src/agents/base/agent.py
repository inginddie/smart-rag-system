# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
import uuid
import time

try:
    from src.utils.logger import setup_logger
    logger = setup_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    IDLE = 'idle'
    THINKING = 'thinking'
    ACTING = 'acting'
    WAITING = 'waiting'
    ERROR = 'error'
    COMPLETED = 'completed'

class AgentCapability(Enum):
    DOCUMENT_SEARCH = 'document_search'
    COMPARISON_ANALYSIS = 'comparison_analysis'
    STATE_OF_ART = 'state_of_art_synthesis'
    SYNTHESIS = 'information_synthesis'
    REASONING = 'multi_step_reasoning'
    ACADEMIC_ANALYSIS = 'academic_analysis'
    LITERATURE_REVIEW = 'literature_review'
    METHODOLOGY_EXTRACTION = 'methodology_extraction'

@dataclass
class AgentStats:
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    avg_response_time_ms: float = 0.0
    avg_confidence: float = 0.0
    last_error: Optional[str] = None
    last_error_timestamp: Optional[float] = None
    capabilities: List[AgentCapability] = field(default_factory=list)
    uptime_start: float = field(default_factory=time.time)
    
    @property
    def success_rate(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return self.successful_queries / self.total_queries
    
    @property
    def error_rate(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return self.failed_queries / self.total_queries
    
    @property
    def uptime_hours(self) -> float:
        return (time.time() - self.uptime_start) / 3600
    
    def update_success(self, response_time_ms: float, confidence: float):
        self.total_queries += 1
        self.successful_queries += 1
        if self.total_queries == 1:
            self.avg_response_time_ms = response_time_ms
            self.avg_confidence = confidence
        else:
            total_time = self.avg_response_time_ms * (self.total_queries - 1)
            self.avg_response_time_ms = (total_time + response_time_ms) / self.total_queries
            total_conf = self.avg_confidence * (self.total_queries - 1)
            self.avg_confidence = (total_conf + confidence) / self.total_queries
    
    def update_failure(self, error_message: str):
        self.total_queries += 1
        self.failed_queries += 1
        self.last_error = error_message
        self.last_error_timestamp = time.time()

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
    
    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f'Confidence must be between 0.0 and 1.0, got {self.confidence}')
        if not isinstance(self.sources, list):
            raise ValueError('Sources must be a list')
        if not isinstance(self.capabilities_used, list):
            raise ValueError('Capabilities used must be a list')
        required_metadata = ['query_type', 'processing_strategy', 'source_count']
        for field_name in required_metadata:
            if field_name not in self.metadata:
                self.metadata[field_name] = 'unknown'

@dataclass 
class AgentMessage:
    id: str
    sender: str
    recipient: str
    content: str
    message_type: str
    metadata: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

class BaseAgent(ABC):
    def __init__(self, name: str, description: str):
        self.agent_id = f'{name}_{uuid.uuid4().hex[:8]}'
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.stats = AgentStats(capabilities=self.get_capabilities())
        self.interaction_history: List[AgentMessage] = []
        self.tools: Dict[str, Any] = {}
        self.memory_manager: Optional[Any] = None
        
        logger.info(f'Initialized agent: {self.name} (ID: {self.agent_id})')
    
    @abstractmethod
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        pass
    
    @abstractmethod 
    def get_capabilities(self) -> List[AgentCapability]:
        pass
    
    def can_handle_query(self, query: str, context: Dict[str, Any] = None) -> float:
        capabilities = self.get_capabilities()
        if not capabilities:
            return 0.0
        query_lower = query.lower()
        capability_matches = 0
        for capability in capabilities:
            keywords = self._get_capability_keywords(capability)
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    capability_matches += 1
                    break
        return min(0.8, capability_matches / len(capabilities))
    
    def _get_capability_keywords(self, capability: AgentCapability) -> List[str]:
        keyword_map = {
            AgentCapability.DOCUMENT_SEARCH: ['search', 'find', 'document', 'paper'],
            AgentCapability.COMPARISON_ANALYSIS: ['compare', 'versus', 'difference'],
            AgentCapability.STATE_OF_ART: ['state of art', 'literature review'],
            AgentCapability.SYNTHESIS: ['synthesize', 'combine', 'integrate'],
            AgentCapability.REASONING: ['analyze', 'reason', 'explain'],
            AgentCapability.ACADEMIC_ANALYSIS: ['academic', 'research', 'study'],
            AgentCapability.LITERATURE_REVIEW: ['literature', 'review', 'survey'],
            AgentCapability.METHODOLOGY_EXTRACTION: ['methodology', 'method', 'approach']
        }
        return keyword_map.get(capability, [])
    
    def get_stats(self) -> AgentStats:
        return self.stats
    
    def health_check(self) -> Dict[str, Any]:
        try:
            test_score = self.can_handle_query('test query')
            is_healthy = isinstance(test_score, float) and 0 <= test_score <= 1
            return {
                'agent_id': self.agent_id,
                'name': self.name,
                'status': self.status.value,
                'healthy': is_healthy,
                'uptime_hours': self.stats.uptime_hours,
                'total_queries': self.stats.total_queries,
                'success_rate': self.stats.success_rate,
                'capabilities': [cap.value for cap in self.get_capabilities()]
            }
        except Exception as e:
            return {
                'agent_id': self.agent_id,
                'name': self.name,
                'healthy': False,
                'error': str(e)
            }
    
    def _record_success(self, processing_time_ms: float, confidence: float):
        self.stats.update_success(processing_time_ms, confidence)
    
    def _record_failure(self, error_message: str):
        self.stats.update_failure(error_message)
    
    
    def update_status(self, status: AgentStatus):
        """Actualiza el estado del agente"""
        self.status = status
        logger.debug(f"Agent {self.name} status updated to {status.value}")
    
    def add_tool(self, tool: Any):
        """Agrega una herramienta al agente"""
        tool_name = tool.__class__.__name__
        self.tools[tool_name] = tool
        logger.debug(f"Tool {tool_name} added to agent {self.name}")
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Obtiene una herramienta por nombre"""
        return self.tools.get(tool_name)
    
    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        """Usa una herramienta registrada"""
        tool = self.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool {tool_name} not found")
        import asyncio
        if asyncio.iscoroutinefunction(tool):
            return await tool(**kwargs)
        else:
            return tool(**kwargs)
    
    def remember(self, key: str, value: Any, context: str = "default"):
        """Almacena información en memoria"""
        if self.memory_manager:
            self.memory_manager.store_memory(
                agent_id=self.agent_id,
                key=key,
                value=value,
                context=context
            )
    
    def recall(self, key: str, context: str = "default") -> Optional[Any]:
        """Recupera información de memoria"""
        if self.memory_manager:
            return self.memory_manager.get_memory(
                agent_id=self.agent_id,
                key=key,
                context=context
            )
        return None
    
    def send_message(self, recipient: str, content: str, message_type: str, metadata: Dict[str, Any] = None) -> AgentMessage:
        """Envía un mensaje a otro agente"""
        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.agent_id,
            recipient=recipient,
            content=content,
            message_type=message_type,
            metadata=metadata or {}
        )
        self.interaction_history.append(message)
        logger.debug(f"Agent {self.name} sent message to {recipient}")
        return message
    
    def receive_message(self, message: AgentMessage):
        """Recibe un mensaje de otro agente"""
        self.interaction_history.append(message)
        logger.debug(f"Agent {self.name} received message from {message.sender}")
    
    def reset(self):
        """Resetea el estado del agente"""
        self.status = AgentStatus.IDLE
        self.interaction_history.clear()
        logger.info(f"Agent {self.name} has been reset")
    
    def __str__(self) -> str:
        return f'Agent({self.name}, status={self.status.value}, queries={self.stats.total_queries})'
    
    def __repr__(self) -> str:
        return self.__str__()
