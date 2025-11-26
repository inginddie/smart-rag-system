# -*- coding: utf-8 -*-
"""
PromptDesignManager - Gestión de prompts especializados por sector
Permite configurar dinámicamente el comportamiento del RAG según el dominio
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from src.admin.prompt_storage import prompt_storage, PromptStorage
from src.utils.logger import setup_logger

logger = setup_logger()


@dataclass
class PromptTestResult:
    """Resultado de prueba de prompt"""
    sector_id: str
    sector_name: str
    system_prompt: str
    intent_prompt: str
    test_query: str
    expected_behavior: str
    timestamp: str


class PromptDesignManager:
    """Gestor central de prompts especializados"""

    def __init__(self, storage: Optional[PromptStorage] = None):
        """
        Inicializa el gestor de prompts

        Args:
            storage: Instancia de PromptStorage (usa la global si no se proporciona)
        """
        self.storage = storage or prompt_storage

    def get_all_sectors(self) -> Dict[str, Any]:
        """
        Obtiene todos los sectores configurados

        Returns:
            Diccionario con todos los sectores
        """
        config = self.storage.load_prompts()
        return config.get("sectors", {})

    def get_sector_info(self, sector_id: str) -> Dict[str, Any]:
        """
        Obtiene información de un sector específico

        Args:
            sector_id: ID del sector

        Returns:
            Información del sector
        """
        return self.storage.get_sector_config(sector_id)

    def get_active_sector(self) -> Tuple[str, Dict[str, Any]]:
        """
        Obtiene el sector activo actual

        Returns:
            Tupla (sector_id, sector_config)
        """
        config = self.storage.load_prompts()
        active_id = config.get("active_sector", "academic_research")
        active_config = config["sectors"].get(active_id, {})
        return active_id, active_config

    def set_active_sector(self, sector_id: str) -> bool:
        """
        Cambia el sector activo

        Args:
            sector_id: ID del sector a activar

        Returns:
            True si se cambió exitosamente
        """
        try:
            self.storage.set_active_sector(sector_id)
            logger.info(f"Active sector changed to: {sector_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting active sector: {e}")
            return False

    def update_system_prompt(
        self, sector_id: str, new_system_prompt: str
    ) -> bool:
        """
        Actualiza el system prompt de un sector

        Args:
            sector_id: ID del sector
            new_system_prompt: Nuevo system prompt

        Returns:
            True si se actualizó exitosamente
        """
        try:
            sector_config = self.storage.get_sector_config(sector_id)
            sector_config["system_prompt"] = new_system_prompt
            self.storage.update_sector_config(sector_id, sector_config)
            logger.info(f"Updated system prompt for sector: {sector_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating system prompt: {e}")
            return False

    def update_intent_prompt(
        self,
        sector_id: str,
        intent_type: str,
        new_prompt: str,
        prompt_name: Optional[str] = None
    ) -> bool:
        """
        Actualiza el prompt de un tipo de intención específico

        Args:
            sector_id: ID del sector
            intent_type: Tipo de intención (DEFINITION, COMPARISON, etc.)
            new_prompt: Nuevo prompt
            prompt_name: Nombre descriptivo del prompt (opcional)

        Returns:
            True si se actualizó exitosamente
        """
        try:
            sector_config = self.storage.get_sector_config(sector_id)

            if "intent_prompts" not in sector_config:
                sector_config["intent_prompts"] = {}

            if intent_type not in sector_config["intent_prompts"]:
                sector_config["intent_prompts"][intent_type] = {
                    "name": prompt_name or intent_type,
                    "prompt": new_prompt,
                    "enabled": True
                }
            else:
                sector_config["intent_prompts"][intent_type]["prompt"] = new_prompt
                if prompt_name:
                    sector_config["intent_prompts"][intent_type]["name"] = prompt_name

            self.storage.update_sector_config(sector_id, sector_config)
            logger.info(f"Updated intent prompt {intent_type} for sector: {sector_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating intent prompt: {e}")
            return False

    def add_response_guideline(
        self, sector_id: str, guideline: str
    ) -> bool:
        """
        Agrega una nueva guideline de respuesta a un sector

        Args:
            sector_id: ID del sector
            guideline: Nueva guideline

        Returns:
            True si se agregó exitosamente
        """
        try:
            sector_config = self.storage.get_sector_config(sector_id)

            if "response_guidelines" not in sector_config:
                sector_config["response_guidelines"] = []

            if guideline not in sector_config["response_guidelines"]:
                sector_config["response_guidelines"].append(guideline)
                self.storage.update_sector_config(sector_id, sector_config)
                logger.info(f"Added guideline to sector: {sector_id}")
                return True
            else:
                logger.warning(f"Guideline already exists in sector: {sector_id}")
                return False

        except Exception as e:
            logger.error(f"Error adding guideline: {e}")
            return False

    def remove_response_guideline(
        self, sector_id: str, guideline: str
    ) -> bool:
        """
        Elimina una guideline de respuesta de un sector

        Args:
            sector_id: ID del sector
            guideline: Guideline a eliminar

        Returns:
            True si se eliminó exitosamente
        """
        try:
            sector_config = self.storage.get_sector_config(sector_id)

            if "response_guidelines" not in sector_config:
                return False

            if guideline in sector_config["response_guidelines"]:
                sector_config["response_guidelines"].remove(guideline)
                self.storage.update_sector_config(sector_id, sector_config)
                logger.info(f"Removed guideline from sector: {sector_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error removing guideline: {e}")
            return False

    def create_custom_sector(
        self,
        sector_id: str,
        name: str,
        description: str,
        system_prompt: str,
        guidelines: Optional[List[str]] = None
    ) -> bool:
        """
        Crea un nuevo sector personalizado

        Args:
            sector_id: ID único del sector
            name: Nombre del sector
            description: Descripción del sector
            system_prompt: System prompt base
            guidelines: Lista de guidelines (opcional)

        Returns:
            True si se creó exitosamente
        """
        try:
            sector_config = {
                "name": name,
                "description": description,
                "enabled": True,
                "system_prompt": system_prompt,
                "response_guidelines": guidelines or [],
                "intent_prompts": {
                    "GENERAL": {
                        "name": "Consulta General",
                        "prompt": f"{system_prompt}\n\nCONTEXTO: {{context}}",
                        "enabled": True
                    }
                }
            }

            self.storage.add_custom_sector(sector_id, sector_config)
            logger.info(f"Created custom sector: {sector_id}")
            return True

        except Exception as e:
            logger.error(f"Error creating custom sector: {e}")
            return False

    def delete_sector(self, sector_id: str) -> bool:
        """
        Elimina un sector

        Args:
            sector_id: ID del sector a eliminar

        Returns:
            True si se eliminó exitosamente
        """
        try:
            self.storage.delete_sector(sector_id)
            logger.info(f"Deleted sector: {sector_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting sector: {e}")
            return False

    def toggle_sector_enabled(self, sector_id: str) -> bool:
        """
        Habilita/deshabilita un sector

        Args:
            sector_id: ID del sector

        Returns:
            True si se cambió exitosamente
        """
        try:
            sector_config = self.storage.get_sector_config(sector_id)
            sector_config["enabled"] = not sector_config.get("enabled", False)
            self.storage.update_sector_config(sector_id, sector_config)
            logger.info(f"Toggled sector enabled: {sector_id}")
            return True
        except Exception as e:
            logger.error(f"Error toggling sector: {e}")
            return False

    def get_prompt_for_query(
        self,
        query: str,
        intent_type: str = "GENERAL",
        sector_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Obtiene el prompt apropiado para una query

        Args:
            query: Query del usuario
            intent_type: Tipo de intención detectada
            sector_id: ID del sector (usa el activo si no se especifica)

        Returns:
            Tupla (system_prompt, intent_prompt)
        """
        if not sector_id:
            sector_id, _ = self.get_active_sector()

        sector_config = self.storage.get_sector_config(sector_id)

        system_prompt = sector_config.get("system_prompt", "")

        # Agregar guidelines al system prompt
        guidelines = sector_config.get("response_guidelines", [])
        if guidelines:
            guidelines_text = "\n".join([f"- {g}" for g in guidelines])
            system_prompt += f"\n\n**DIRECTRICES DE RESPUESTA:**\n{guidelines_text}"

        # Obtener intent prompt
        intent_prompts = sector_config.get("intent_prompts", {})
        intent_config = intent_prompts.get(intent_type, intent_prompts.get("GENERAL", {}))

        intent_prompt = intent_config.get("prompt", "{context}")

        return system_prompt, intent_prompt

    def test_prompt_configuration(
        self,
        sector_id: str,
        test_query: str,
        intent_type: str = "GENERAL"
    ) -> PromptTestResult:
        """
        Prueba la configuración de prompts para un sector

        Args:
            sector_id: ID del sector
            test_query: Query de prueba
            intent_type: Tipo de intención

        Returns:
            Resultado de la prueba
        """
        sector_config = self.storage.get_sector_config(sector_id)
        system_prompt, intent_prompt = self.get_prompt_for_query(
            test_query, intent_type, sector_id
        )

        # Generar descripción del comportamiento esperado
        guidelines = sector_config.get("response_guidelines", [])
        expected_behavior = "El sistema responderá:\n"
        expected_behavior += f"- Usando el sector: {sector_config.get('name', sector_id)}\n"
        expected_behavior += f"- Con intención detectada: {intent_type}\n"
        if guidelines:
            expected_behavior += "\nSeguirá estas directrices:\n"
            expected_behavior += "\n".join([f"  • {g}" for g in guidelines])

        return PromptTestResult(
            sector_id=sector_id,
            sector_name=sector_config.get("name", sector_id),
            system_prompt=system_prompt,
            intent_prompt=intent_prompt,
            test_query=test_query,
            expected_behavior=expected_behavior,
            timestamp=datetime.now().isoformat()
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de configuración de prompts

        Returns:
            Diccionario con estadísticas
        """
        config = self.storage.load_prompts()
        sectors = config.get("sectors", {})
        active_sector_id = config.get("active_sector", "")

        enabled_sectors = sum(1 for s in sectors.values() if s.get("enabled", False))
        total_intent_prompts = sum(
            len(s.get("intent_prompts", {}))
            for s in sectors.values()
        )
        total_guidelines = sum(
            len(s.get("response_guidelines", []))
            for s in sectors.values()
        )

        active_sector = sectors.get(active_sector_id, {})

        return {
            "total_sectors": len(sectors),
            "enabled_sectors": enabled_sectors,
            "active_sector_id": active_sector_id,
            "active_sector_name": active_sector.get("name", "N/A"),
            "total_intent_prompts": total_intent_prompts,
            "total_guidelines": total_guidelines,
            "version": config.get("version", "1.0.0"),
            "last_updated": config.get("last_updated", "N/A")
        }

    def export_configuration(self) -> str:
        """
        Exporta la configuración completa

        Returns:
            JSON string con la configuración
        """
        return self.storage.export_config()

    def import_configuration(self, config_json: str) -> bool:
        """
        Importa configuración desde JSON

        Args:
            config_json: JSON string con configuración

        Returns:
            True si se importó exitosamente
        """
        try:
            self.storage.import_config(config_json)
            logger.info("Configuration imported successfully")
            return True
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False


# Instancia global
prompt_design_manager = PromptDesignManager()
