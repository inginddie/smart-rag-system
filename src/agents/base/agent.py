# -*- coding: utf-8 -*-
"""
Clase base para todos los agentes del sistema.
Esta abstracción permite crear agentes especializados manteniendo interfaz común.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import uuid
import time
import asyncio
from src.utils.logger import setup_logger

logger = setup_logger()

class AgentStatus(Enum):
    """Estados posibles de un agente"""
    IDLE = "idle"
    THINKING = "thinking" 
    ACTING = "acting"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"

@dataclass
class AgentResponse:
    """Respuesta estándar de un agente"""
    agent_id: str
    agent_name: str
    content: str
    confidence: float
    metadata: Dict[str, Any]
    reasoning: Optional[str] = None
    sources: Optional[List[Dict]] = None
    next_actions: Optional[List[str]] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass 
class AgentMessage:
    """Mensaje entre agentes"""
    id: str
    sender: str
    recipient: str
    content: str
    message_type: str
    metadata: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class BaseAgent(ABC):
    """
    Clase base abstracta para todos los agentes del sistema Agentic RAG.
    
    Funcionalidades principales:
    - Gestión de estado y ciclo de vida
    - Interfaz común para comunicación
    - Sistema de memoria integrado
    - Manejo de herramientas
    - Logging y trazabilidad
    """
    
    def __init__(self, 
                 name: str,
                 description: str,
                 tools: Optional[List] = None,
                 memory_manager = None,
                 max_iterations: int = 5):
        
        self.agent_id = f"{name}_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.tools = tools or []
        self.memory_manager = memory_manager
        self.max_iterations = max_iterations
        
        # Historial de interacciones
        self.interaction_history: List[AgentMessage] = []
        self.performance_metrics = {
            "queries_processed": 0,
            "average_response_time": 0.0,
            "success_rate": 0.0,
            "errors": 0
        }
        
        logger.info(f"Initialized agent: {self.name} (ID: {self.agent_id})")
    
    @abstractmethod
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Procesa una consulta y devuelve una respuesta.
        Cada agente especializado debe implementar esta lógica.
        """
        pass
    
    @abstractmethod 
    def get_capabilities(self) -> List[str]:
        """Devuelve lista de capacidades del agente"""
        pass
    
    def can_handle_query(self, query: str, context: Dict[str, Any] = None) -> float:
        """
        Determina si el agente puede manejar una consulta.
        Retorna score de confianza entre 0.0 y 1.0
        """
        capabilities = self.get_capabilities()
        query_lower = query.lower()
        
        # Lógica básica de matching por palabras clave
        matches = 0
        for capability in capabilities:
            if capability.lower() in query_lower:
                matches += 1
        
        return min(1.0, matches / len(capabilities) if capabilities else 0.0)
    
    def add_tool(self, tool):
        """Agrega una herramienta al agente"""
        self.tools.append(tool)
        logger.debug(f"Added tool to {self.name}: {tool.__class__.__name__}")
    
    def get_tool(self, tool_name: str):
        """Obtiene una herramienta por nombre"""
        for tool in self.tools:
            if hasattr(tool, 'name') and tool.name == tool_name:
                return tool
            elif tool.__class__.__name__ == tool_name:
                return tool
        return None
    
    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        """Usa una herramienta específica"""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found in agent {self.name}")
        
        logger.debug(f"{self.name} using tool: {tool_name}")
        
        # Si la herramienta es async
        if asyncio.iscoroutinefunction(tool):
            return await tool(**kwargs)
        elif hasattr(tool, 'run'):
            if asyncio.iscoroutinefunction(tool.run):
                return await tool.run(**kwargs)
            else:
                return tool.run(**kwargs)
        else:
            return tool(**kwargs)
    
    def update_status(self, new_status: AgentStatus):
        """Actualiza el estado del agente"""
        old_status = self.status
        self.status = new_status
        logger.debug(f"{self.name} status: {old_status.value} -> {new_status.value}")
    
    def remember(self, key: str, value: Any, context: str = "general"):
        """Guarda información en memoria"""
        if self.memory_manager:
            self.memory_manager.store_memory(
                agent_id=self.agent_id,
                key=key,
                value=value,
                context=context
            )
    
    def recall(self, key: str, context: str = "general") -> Any:
        """Recupera información de memoria"""
        if self.memory_manager:
            return self.memory_manager.get_memory(
                agent_id=self.agent_id,
                key=key,
                context=context
            )
        return None
    
    def send_message(self, recipient: str, content: str, 
                    message_type: str = "info", 
                    metadata: Dict[str, Any] = None) -> AgentMessage:
        """Envía mensaje a otro agente"""
        message = AgentMessage(
            id=uuid.uuid4().hex,
            sender=self.agent_id,
            recipient=recipient,
            content=content,
            message_type=message_type,
            metadata=metadata or {}
        )
        
        self.interaction_history.append(message)
        logger.debug(f"{self.name} -> {recipient}: {message_type}")
        
        return message
    
    def receive_message(self, message: AgentMessage):
        """Recibe mensaje de otro agente"""
        self.interaction_history.append(message)
        logger.debug(f"{self.name} received {message.message_type} from {message.sender}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del agente"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "tools_count": len(self.tools),
            "interactions": len(self.interaction_history),
            "performance": self.performance_metrics
        }
    
    def reset(self):
        """Reinicia el estado del agente"""
        self.status = AgentStatus.IDLE
        self.interaction_history.clear()
        logger.info(f"Agent {self.name} reset")
        
    def __str__(self) -> str:
        return f"Agent({self.name}, status={self.status.value}, tools={len(self.tools)})"
    
    def __repr__(self) -> str:
        return self.__str__()