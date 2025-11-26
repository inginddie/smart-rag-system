# -*- coding: utf-8 -*-
"""
DynamicPromptOrchestrator - Orquestador de prompts dinámicos
Integra el sistema de Prompt Design con el pipeline RAG existente
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from src.admin.prompt_design_manager import prompt_design_manager, PromptDesignManager
from src.utils.intent_detector import IntentType, IntentResult
from src.utils.logger import setup_logger

logger = setup_logger()


@dataclass
class DynamicPromptResult:
    """Resultado de selección de prompt dinámico"""
    system_prompt: str
    user_prompt: str
    sector_id: str
    sector_name: str
    intent_type: str
    context_template: str
    guidelines: list
    metadata: Dict[str, Any]


class DynamicPromptOrchestrator:
    """
    Orquestador que selecciona prompts dinámicamente según:
    - Sector activo configurado por el usuario
    - Tipo de intención detectada
    - Contexto de la consulta
    """

    def __init__(self, prompt_manager: Optional[PromptDesignManager] = None):
        """
        Inicializa el orquestador

        Args:
            prompt_manager: Instancia de PromptDesignManager (usa la global si no se proporciona)
        """
        self.prompt_manager = prompt_manager or prompt_design_manager
        self._cache = {}  # Cache de prompts por sector

    def get_prompts_for_query(
        self,
        query: str,
        intent_result: Optional[IntentResult] = None,
        context: Optional[str] = None,
        sector_id: Optional[str] = None
    ) -> DynamicPromptResult:
        """
        Obtiene los prompts apropiados para una consulta

        Args:
            query: Consulta del usuario
            intent_result: Resultado de detección de intención (opcional)
            context: Contexto adicional (opcional)
            sector_id: ID del sector específico (usa el activo si no se especifica)

        Returns:
            DynamicPromptResult con prompts configurados
        """
        # Determinar sector
        if not sector_id:
            sector_id, sector_config = self.prompt_manager.get_active_sector()
        else:
            sector_config = self.prompt_manager.get_sector_info(sector_id)

        # Determinar tipo de intención
        if intent_result:
            intent_type = self._map_intent_type(intent_result.intent_type)
        else:
            intent_type = "GENERAL"

        # Obtener prompts del sector
        system_prompt, user_prompt_template = self.prompt_manager.get_prompt_for_query(
            query, intent_type, sector_id
        )

        # Construir prompt de usuario con contexto
        user_prompt = self._build_user_prompt(
            user_prompt_template, query, context
        )

        # Crear resultado
        result = DynamicPromptResult(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            sector_id=sector_id,
            sector_name=sector_config.get("name", sector_id),
            intent_type=intent_type,
            context_template=user_prompt_template,
            guidelines=sector_config.get("response_guidelines", []),
            metadata={
                "sector_description": sector_config.get("description", ""),
                "sector_enabled": sector_config.get("enabled", False),
                "intent_confidence": intent_result.confidence if intent_result else 1.0,
                "has_custom_context": context is not None
            }
        )

        logger.debug(
            f"Dynamic prompts selected: sector={sector_id}, intent={intent_type}"
        )

        return result

    def _map_intent_type(self, intent_type: IntentType) -> str:
        """
        Mapea IntentType a string para búsqueda de prompts

        Args:
            intent_type: Tipo de intención detectada

        Returns:
            String del tipo de intención
        """
        mapping = {
            IntentType.DEFINITION: "DEFINITION",
            IntentType.COMPARISON: "COMPARISON",
            IntentType.STATE_OF_ART: "STATE_OF_ART",
            IntentType.GAP_ANALYSIS: "GAP_ANALYSIS",
            IntentType.UNKNOWN: "GENERAL"
        }
        return mapping.get(intent_type, "GENERAL")

    def _build_user_prompt(
        self,
        template: str,
        query: str,
        context: Optional[str] = None
    ) -> str:
        """
        Construye el prompt de usuario insertando contexto y query

        Args:
            template: Template del prompt
            query: Query del usuario
            context: Contexto recuperado

        Returns:
            Prompt completo
        """
        # Asegurar que el template tiene placeholder para contexto
        if "{context}" not in template:
            template += "\n\nCONTEXTO: {context}"

        # Insertar query si el template lo requiere
        if "{query}" in template:
            template = template.replace("{query}", query)

        # Insertar contexto
        actual_context = context if context else "No hay contexto disponible."
        user_prompt = template.replace("{context}", actual_context)

        return user_prompt

    def format_prompt_for_llm(
        self,
        result: DynamicPromptResult,
        include_metadata: bool = False
    ) -> Dict[str, str]:
        """
        Formatea el resultado para enviar al LLM

        Args:
            result: Resultado de prompts dinámicos
            include_metadata: Si incluir metadata en el prompt

        Returns:
            Diccionario con system y user prompts
        """
        system_prompt = result.system_prompt

        if include_metadata and result.guidelines:
            guidelines_text = "\n".join([f"- {g}" for g in result.guidelines])
            system_prompt += f"\n\n**DIRECTRICES:**\n{guidelines_text}"

        return {
            "system": system_prompt,
            "user": result.user_prompt
        }

    def get_prompt_preview(
        self,
        sector_id: Optional[str] = None,
        intent_type: str = "GENERAL"
    ) -> Dict[str, Any]:
        """
        Obtiene preview de prompts sin ejecutar query

        Args:
            sector_id: ID del sector (usa el activo si no se especifica)
            intent_type: Tipo de intención

        Returns:
            Diccionario con información de preview
        """
        if not sector_id:
            sector_id, sector_config = self.prompt_manager.get_active_sector()
        else:
            sector_config = self.prompt_manager.get_sector_info(sector_id)

        system_prompt, user_template = self.prompt_manager.get_prompt_for_query(
            "", intent_type, sector_id
        )

        return {
            "sector_id": sector_id,
            "sector_name": sector_config.get("name", sector_id),
            "intent_type": intent_type,
            "system_prompt": system_prompt,
            "user_template": user_template,
            "guidelines": sector_config.get("response_guidelines", []),
            "description": sector_config.get("description", "")
        }

    def refresh_cache(self):
        """Limpia el cache de prompts"""
        self._cache.clear()
        logger.info("Dynamic prompt cache cleared")

    def get_available_sectors(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene información de todos los sectores disponibles

        Returns:
            Diccionario con info de sectores
        """
        sectors = self.prompt_manager.get_all_sectors()
        active_id, _ = self.prompt_manager.get_active_sector()

        result = {}
        for sector_id, config in sectors.items():
            result[sector_id] = {
                "name": config.get("name", sector_id),
                "description": config.get("description", ""),
                "enabled": config.get("enabled", False),
                "is_active": sector_id == active_id,
                "intent_prompts_count": len(config.get("intent_prompts", {})),
                "guidelines_count": len(config.get("response_guidelines", []))
            }

        return result

    def validate_prompts(self, sector_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Valida que los prompts de un sector estén correctamente configurados

        Args:
            sector_id: ID del sector (usa el activo si no se especifica)

        Returns:
            Diccionario con resultado de validación
        """
        if not sector_id:
            sector_id, _ = self.prompt_manager.get_active_sector()

        try:
            sector_config = self.prompt_manager.get_sector_info(sector_id)

            issues = []
            warnings = []

            # Validar system prompt
            system_prompt = sector_config.get("system_prompt", "")
            if not system_prompt or len(system_prompt.strip()) < 10:
                issues.append("System prompt es muy corto o está vacío")

            # Validar intent prompts
            intent_prompts = sector_config.get("intent_prompts", {})
            if not intent_prompts:
                warnings.append("No hay intent prompts configurados")
            else:
                for intent_type, config in intent_prompts.items():
                    prompt = config.get("prompt", "")
                    if "{context}" not in prompt:
                        warnings.append(
                            f"Intent prompt '{intent_type}' no contiene placeholder {{context}}"
                        )

            # Validar guidelines
            guidelines = sector_config.get("response_guidelines", [])
            if not guidelines:
                warnings.append("No hay guidelines de respuesta configuradas")

            return {
                "valid": len(issues) == 0,
                "sector_id": sector_id,
                "sector_name": sector_config.get("name", sector_id),
                "issues": issues,
                "warnings": warnings,
                "score": max(0, 100 - (len(issues) * 30) - (len(warnings) * 10))
            }

        except Exception as e:
            return {
                "valid": False,
                "sector_id": sector_id,
                "issues": [f"Error de validación: {str(e)}"],
                "warnings": [],
                "score": 0
            }


# Instancia global
dynamic_prompt_orchestrator = DynamicPromptOrchestrator()
