# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import time

class AgentCapability(Enum):
    DOCUMENT_SEARCH = "document_search"

@dataclass
class AgentStats:
    total_queries: int = 0
    successful_queries: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return self.successful_queries / self.total_queries