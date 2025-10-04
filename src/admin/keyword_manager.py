# -*- coding: utf-8 -*-
"""
Gestor principal de keywords para agentes
"""

from typing import Dict, List, Any, Tuple, Optional
from src.admin.keyword_storage import KeywordStorage
from src.agents.base.agent import AgentCapability
from src.utils.logger import setup_logger

logger = setup_logger()

class KeywordManager:
    """Gestor central de keywords para agentes"""
    
    def __init__(self, storage_path: str = "config/agent_keywords.json"):
        self.storage = KeywordStorage(storage_path)
        self._cache = None
        self._load_cache()
    
    def _load_cache(self):
        """Carga configuración en cache"""
        self._cache = self.storage.load_config()
        logger.debug("Keyword configuration loaded into cache")
    
    def reload_config(self):
        """Recarga configuración desde disco"""
        self._load_cache()
        logger.info("Keyword configuration reloaded")
    
    def get_agent_keywords(self, agent_name: str) -> Dict[str, List[str]]:
        """Obtiene keywords de un agente por capacidad"""
        if not self._cache:
            self._load_cache()
        
        agent_config = self._cache.get("agents", {}).get(agent_name, {})
        capabilities = agent_config.get("capabilities", {})
        
        result = {}
        for cap_name, cap_config in capabilities.items():
            if cap_config.get("enabled", True):
                result[cap_name] = cap_config.get("keywords", [])
        
        return result
    
    def get_capability_keywords(self, agent_name: str, capability: str) -> List[str]:
        """Obtiene keywords de una capacidad específica"""
        agent_keywords = self.get_agent_keywords(agent_name)
        return agent_keywords.get(capability, [])
    
    def calculate_query_score(self, agent_name: str, query: str) -> Tuple[float, Dict[str, List[str]]]:
        """Calcula score de una query para un agente y retorna matches"""
        agent_keywords = self.get_agent_keywords(agent_name)
        
        if not agent_keywords:
            return 0.0, {}
        
        query_lower = query.lower()
        matches = {}
        capability_matches = 0
        
        for capability, keywords in agent_keywords.items():
            capability_matches_list = []
            
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    capability_matches_list.append(keyword)
            
            if capability_matches_list:
                matches[capability] = capability_matches_list
                capability_matches += 1
        
        # Score = capabilities matched / total capabilities
        total_capabilities = len(agent_keywords)
        score = capability_matches / total_capabilities if total_capabilities > 0 else 0.0
        
        return score, matches
    
    def test_query_activation(self, query: str) -> Dict[str, Any]:
        """Prueba qué agentes se activarían con una query"""
        results = {}
        
        if not self._cache:
            self._load_cache()
        
        for agent_name, agent_config in self._cache.get("agents", {}).items():
            if not agent_config.get("enabled", True):
                continue
            
            score, matches = self.calculate_query_score(agent_name, query)
            threshold = agent_config.get("threshold", 0.3)
            
            results[agent_name] = {
                "score": score,
                "threshold": threshold,
                "would_activate": score >= threshold,
                "matches": matches,
                "total_capabilities": len(agent_config.get("capabilities", {})),
                "matched_capabilities": len(matches)
            }
        
        return results
    
    def add_keyword(self, agent_name: str, capability: str, keyword: str) -> bool:
        """Agrega una keyword"""
        if not keyword or not keyword.strip():
            logger.warning(f"Cannot add empty keyword")
            return False
        
        keyword = keyword.strip().lower()
        
        success = self.storage.add_keyword(agent_name, capability, keyword)
        if success:
            self._load_cache()  # Recargar cache
            logger.info(f"Added keyword '{keyword}' to {agent_name}.{capability}")
        
        return success
    
    def remove_keyword(self, agent_name: str, capability: str, keyword: str) -> bool:
        """Elimina una keyword"""
        success = self.storage.remove_keyword(agent_name, capability, keyword)
        if success:
            self._load_cache()  # Recargar cache
            logger.info(f"Removed keyword '{keyword}' from {agent_name}.{capability}")
        
        return success
    
    def update_threshold(self, agent_name: str, threshold: float) -> bool:
        """Actualiza el threshold de un agente"""
        if not 0.0 <= threshold <= 1.0:
            logger.warning(f"Invalid threshold: {threshold}. Must be between 0.0 and 1.0")
            return False
        
        if not self._cache:
            self._load_cache()
        
        if agent_name not in self._cache.get("agents", {}):
            logger.warning(f"Agent {agent_name} not found")
            return False
        
        self._cache["agents"][agent_name]["threshold"] = threshold
        success = self.storage.save_config(self._cache)
        
        if success:
            logger.info(f"Updated threshold for {agent_name} to {threshold}")
        
        return success
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Obtiene configuración completa de un agente"""
        if not self._cache:
            self._load_cache()
        
        return self._cache.get("agents", {}).get(agent_name, {})
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema"""
        if not self._cache:
            self._load_cache()
        
        agents = self._cache.get("agents", {})
        total_agents = len(agents)
        active_agents = sum(1 for config in agents.values() if config.get("enabled", True))
        
        total_keywords = 0
        total_capabilities = 0
        
        for agent_config in agents.values():
            capabilities = agent_config.get("capabilities", {})
            total_capabilities += len(capabilities)
            
            for cap_config in capabilities.values():
                if cap_config.get("enabled", True):
                    total_keywords += len(cap_config.get("keywords", []))
        
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "total_capabilities": total_capabilities,
            "total_keywords": total_keywords,
            "last_updated": self._cache.get("global_settings", {}).get("last_updated"),
            "config_valid": len(self.storage.validate_config(self._cache)) == 0
        }
    
    def export_config(self) -> Dict[str, Any]:
        """Exporta configuración completa"""
        if not self._cache:
            self._load_cache()
        
        return self._cache.copy()
    
    def import_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Importa configuración y valida"""
        errors = self.storage.validate_config(config)
        
        if errors:
            logger.warning(f"Configuration validation failed: {errors}")
            return False, errors
        
        success = self.storage.save_config(config)
        if success:
            self._load_cache()
            logger.info("Configuration imported successfully")
        
        return success, []
    
    def reset_to_defaults(self) -> bool:
        """Resetea configuración a valores por defecto"""
        default_config = self.storage._get_default_config()
        success = self.storage.save_config(default_config)
        
        if success:
            self._load_cache()
            logger.info("Configuration reset to defaults")
        
        return success
