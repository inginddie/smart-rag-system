#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional
import time
from src.agents.base.agent import BaseAgent, AgentResponse, AgentCapability
from src.storage.vector_store import VectorStoreManager
from src.utils.logger import setup_logger

logger = setup_logger()

class ComparisonAgent(BaseAgent):
    COMPARISON_KEYWORDS = [
        'compara', 'comparar', 'versus', 'vs', 'diferencia', 'diferencias',
        'ventaja', 'ventajas', 'desventaja', 'desventajas', 'mejor', 'peor',
        'contrasta', 'contrastar', 'contraste',
        'compare', 'comparison', 'contrast', 'difference', 'differences',
        'advantage', 'advantages', 'disadvantage', 'disadvantages',
        'o', 'or', 'between'
    ]
    
    def __init__(self, vector_store_manager=None):
        super().__init__(name='ComparisonAgent', description='Especialista en análisis comparativo')
        self.vector_store_manager = vector_store_manager or VectorStoreManager()
        logger.info('ComparisonAgent initialized')
    
    def get_capabilities(self):
        return [AgentCapability.COMPARISON_ANALYSIS, AgentCapability.REASONING]
    
    def can_handle_query(self, query, context=None):
        if not query:
            return 0.0
        query_lower = query.lower()
        score = sum(0.2 for kw in self.COMPARISON_KEYWORDS if kw in query_lower)
        return min(1.0, score)
    
    def process_query(self, query, context=None):
        start_time = time.time()
        try:
            answer = f'Análisis comparativo de: {query}'
            metadata = {
                'comparison_criteria': ['functionality', 'performance', 'usability'],
                'query_type': 'comparison',
                'processing_strategy': 'comparative_analysis',
                'source_count': 0
            }
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                content=answer,
                confidence=0.8,
                reasoning='Comparative analysis',
                sources=[],
                metadata=metadata,
                processing_time_ms=(time.time() - start_time) * 1000,
                capabilities_used=[AgentCapability.COMPARISON_ANALYSIS]
            )
        except Exception as e:
            logger.error(f'Error: {e}')
            return AgentResponse(
                agent_id=self.agent_id,
                agent_name=self.name,
                content=f'Error: {str(e)}',
                confidence=0.0,
                reasoning='Error occurred',
                sources=[],
                metadata={'error': str(e), 'query_type': 'comparison', 'processing_strategy': 'error', 'source_count': 0},
                processing_time_ms=(time.time() - start_time) * 1000,
                capabilities_used=[]
            )

def create_comparison_agent(vector_store_manager=None):
    return ComparisonAgent(vector_store_manager=vector_store_manager)
