# -*- coding: utf-8 -*-
"""
Gestor de persistencia para keywords de agentes
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
from src.utils.logger import setup_logger

logger = setup_logger()

class KeywordStorage:
    """Maneja la persistencia de keywords de agentes"""
    
    def __init__(self, config_path: str = "config/agent_keywords.json"):
        self.config_path = Path(config_path)
        self.backup_dir = Path("config/backups")
        self._ensure_directories()
        self._load_default_config()
    
    def _ensure_directories(self):
        """Crea directorios necesarios"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_default_config(self):
        """Carga configuración por defecto si no existe"""
        if not self.config_path.exists():
            default_config = self._get_default_config()
            self.save_config(default_config)
            logger.info(f"Created default keyword configuration at {self.config_path}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto del sistema"""
        return {
            "agents": {
                "DocumentSearchAgent": {
                    "capabilities": {
                        "DOCUMENT_SEARCH": {
                            "keywords": ["search", "find", "document", "paper", "buscar", "encontrar", "documento", "articulo"],
                            "enabled": True,
                            "weight": 1.0
                        },
                        "SYNTHESIS": {
                            "keywords": ["synthesize", "combine", "integrate", "sintetizar", "combinar", "integrar"],
                            "enabled": True,
                            "weight": 1.0
                        },
                        "ACADEMIC_ANALYSIS": {
                            "keywords": ["academic", "research", "study", "academico", "investigacion", "estudio"],
                            "enabled": True,
                            "weight": 1.0
                        }
                    },
                    "threshold": 0.3,
                    "enabled": True
                }
            },
            "global_settings": {
                "case_sensitive": False,
                "partial_match": True,
                "last_updated": datetime.now().isoformat(),
                "updated_by": "system"
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Carga configuración desde archivo"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.debug(f"Loaded keyword configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading keyword config: {e}")
            return self._get_default_config()
    
    def save_config(self, config: Dict[str, Any], backup: bool = True) -> bool:
        """Guarda configuración a archivo"""
        try:
            # Crear backup si se solicita
            if backup and self.config_path.exists():
                self._create_backup()
            
            # Actualizar metadata
            config["global_settings"]["last_updated"] = datetime.now().isoformat()
            
            # Guardar configuración
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved keyword configuration to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving keyword config: {e}")
            return False
    
    def _create_backup(self):
        """Crea backup de la configuración actual"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"agent_keywords_{timestamp}.json"
            
            with open(self.config_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            
            logger.info(f"Created backup at {backup_path}")
            
            # Limpiar backups antiguos (mantener solo los últimos 10)
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.warning(f"Could not create backup: {e}")
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Limpia backups antiguos"""
        try:
            backup_files = list(self.backup_dir.glob("agent_keywords_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
                logger.debug(f"Removed old backup: {old_backup}")
                
        except Exception as e:
            logger.warning(f"Error cleaning up backups: {e}")
    
    def add_keyword(self, agent_name: str, capability: str, keyword: str) -> bool:
        """Agrega una keyword a una capacidad"""
        config = self.load_config()
        
        try:
            agent_config = config["agents"][agent_name]
            capability_config = agent_config["capabilities"][capability]
            
            if keyword not in capability_config["keywords"]:
                capability_config["keywords"].append(keyword)
                return self.save_config(config)
            
            return True  # Ya existe
            
        except KeyError as e:
            logger.error(f"Invalid agent/capability: {e}")
            return False
    
    def remove_keyword(self, agent_name: str, capability: str, keyword: str) -> bool:
        """Elimina una keyword de una capacidad"""
        config = self.load_config()
        
        try:
            agent_config = config["agents"][agent_name]
            capability_config = agent_config["capabilities"][capability]
            
            if keyword in capability_config["keywords"]:
                capability_config["keywords"].remove(keyword)
                return self.save_config(config)
            
            return True  # No existe
            
        except KeyError as e:
            logger.error(f"Invalid agent/capability: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Valida configuración y retorna lista de errores"""
        errors = []
        
        # Validar estructura básica
        if "agents" not in config:
            errors.append("Missing 'agents' section")
            return errors
        
        if "global_settings" not in config:
            errors.append("Missing 'global_settings' section")
        
        # Validar agentes
        for agent_name, agent_config in config["agents"].items():
            if not isinstance(agent_config, dict):
                errors.append(f"Agent {agent_name} config must be a dictionary")
                continue
            
            if "capabilities" not in agent_config:
                errors.append(f"Agent {agent_name} missing 'capabilities'")
                continue
            
            # Validar capacidades
            for cap_name, cap_config in agent_config["capabilities"].items():
                if "keywords" not in cap_config:
                    errors.append(f"Capability {agent_name}.{cap_name} missing 'keywords'")
                    continue
                
                keywords = cap_config["keywords"]
                if not isinstance(keywords, list) or len(keywords) == 0:
                    errors.append(f"Capability {agent_name}.{cap_name} must have non-empty keyword list")
                
                # Validar que las keywords no estén vacías
                for keyword in keywords:
                    if not isinstance(keyword, str) or not keyword.strip():
                        errors.append(f"Invalid keyword in {agent_name}.{cap_name}: '{keyword}'")
        
        return errors
