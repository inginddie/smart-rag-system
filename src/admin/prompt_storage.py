# -*- coding: utf-8 -*-
"""
PromptStorage - Gestión de persistencia de prompts personalizados
Permite almacenar y recuperar prompts especializados por sector/dominio
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from src.utils.logger import setup_logger

logger = setup_logger()


class PromptStorage:
    """Gestiona la persistencia de prompts personalizados"""

    DEFAULT_PROMPTS_FILE = "config/custom_prompts.json"
    BACKUP_DIR = "config/backups/prompts"
    MAX_BACKUPS = 10

    def __init__(self, prompts_file: Optional[str] = None):
        """
        Inicializa el almacenamiento de prompts

        Args:
            prompts_file: Ruta al archivo de prompts (opcional)
        """
        self.prompts_file = prompts_file or self.DEFAULT_PROMPTS_FILE
        self._ensure_directories()
        self._initialize_default_prompts()

    def _ensure_directories(self):
        """Asegura que existan los directorios necesarios"""
        config_dir = os.path.dirname(self.prompts_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        if not os.path.exists(self.BACKUP_DIR):
            os.makedirs(self.BACKUP_DIR, exist_ok=True)

    def _initialize_default_prompts(self):
        """Inicializa el archivo de prompts con configuración por defecto"""
        if not os.path.exists(self.prompts_file):
            default_config = self._get_default_prompt_configuration()
            self.save_prompts(default_config)
            logger.info(f"Initialized default prompts at {self.prompts_file}")

    def _get_default_prompt_configuration(self) -> Dict[str, Any]:
        """Retorna la configuración de prompts por defecto"""
        return {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "active_sector": "academic_research",
            "sectors": {
                "academic_research": {
                    "name": "Investigación Académica",
                    "description": "Análisis de papers académicos, síntesis de investigación",
                    "enabled": True,
                    "system_prompt": "Eres un asistente de investigación académica especializado en análisis riguroso de literatura científica.",
                    "response_guidelines": [
                        "Cita fuentes específicas con autores y años",
                        "Mantén rigor académico en terminología",
                        "Identifica gaps y limitaciones en la investigación",
                        "Proporciona análisis crítico basado en evidencia"
                    ],
                    "intent_prompts": {
                        "DEFINITION": {
                            "name": "Definición Académica",
                            "prompt": """Proporciona una definición académica rigurosa que incluya:
1. Definición formal con terminología estándar
2. Contexto histórico y evolución del concepto
3. Características técnicas fundamentales
4. Referencias a autores clave

CONTEXTO: {context}""",
                            "enabled": True
                        },
                        "COMPARISON": {
                            "name": "Análisis Comparativo",
                            "prompt": """Realiza un análisis comparativo sistemático:
1. Identifica elementos a comparar
2. Crea matriz comparativa con criterios relevantes
3. Analiza fortalezas y limitaciones de cada enfoque
4. Proporciona recomendaciones basadas en evidencia

CONTEXTO: {context}""",
                            "enabled": True
                        },
                        "GENERAL": {
                            "name": "Consulta General",
                            "prompt": """Analiza la información académica proporcionada:
1. Identifica hallazgos clave y metodologías
2. Extrae métricas y resultados experimentales
3. Relaciona diferentes estudios cuando sea relevante
4. Cita específicamente las fuentes

CONTEXTO: {context}""",
                            "enabled": True
                        }
                    }
                },
                "business_analysis": {
                    "name": "Análisis de Negocios",
                    "description": "Análisis empresarial, estrategia y toma de decisiones",
                    "enabled": False,
                    "system_prompt": "Eres un analista de negocios experto que proporciona insights estratégicos basados en datos.",
                    "response_guidelines": [
                        "Enfócate en valor de negocio y ROI",
                        "Identifica riesgos y oportunidades",
                        "Proporciona recomendaciones accionables",
                        "Usa métricas y KPIs relevantes"
                    ],
                    "intent_prompts": {
                        "GENERAL": {
                            "name": "Análisis General",
                            "prompt": """Analiza la información desde perspectiva de negocios:
1. Identifica oportunidades y riesgos clave
2. Evalúa impacto potencial en el negocio
3. Proporciona recomendaciones accionables
4. Considera factores de mercado y competencia

CONTEXTO: {context}""",
                            "enabled": True
                        }
                    }
                },
                "legal_review": {
                    "name": "Revisión Legal",
                    "description": "Análisis de documentos legales y regulaciones",
                    "enabled": False,
                    "system_prompt": "Eres un asistente legal que analiza documentos con precisión y rigor jurídico.",
                    "response_guidelines": [
                        "Mantén precisión en terminología legal",
                        "Identifica cláusulas y obligaciones clave",
                        "Señala riesgos y áreas de atención",
                        "Referencia leyes y regulaciones aplicables"
                    ],
                    "intent_prompts": {
                        "GENERAL": {
                            "name": "Análisis Legal",
                            "prompt": """Analiza el documento legal proporcionado:
1. Identifica términos y condiciones clave
2. Señala obligaciones y derechos de las partes
3. Identifica riesgos y cláusulas problemáticas
4. Referencia marco legal aplicable

CONTEXTO: {context}""",
                            "enabled": True
                        }
                    }
                },
                "medical_analysis": {
                    "name": "Análisis Médico",
                    "description": "Revisión de literatura médica y casos clínicos",
                    "enabled": False,
                    "system_prompt": "Eres un asistente médico especializado en análisis de literatura clínica y evidencia médica.",
                    "response_guidelines": [
                        "Prioriza evidencia basada en estudios clínicos",
                        "Usa terminología médica precisa",
                        "Identifica nivel de evidencia y calidad de estudios",
                        "Señala contraindicaciones y consideraciones de seguridad"
                    ],
                    "intent_prompts": {
                        "GENERAL": {
                            "name": "Análisis Médico",
                            "prompt": """Analiza la información médica con rigor clínico:
1. Evalúa nivel de evidencia de los estudios
2. Identifica hallazgos clínicos relevantes
3. Señala efectos adversos y contraindicaciones
4. Proporciona conclusiones basadas en evidencia

CONTEXTO: {context}""",
                            "enabled": True
                        }
                    }
                },
                "technical_documentation": {
                    "name": "Documentación Técnica",
                    "description": "Análisis de documentación técnica y arquitectura de software",
                    "enabled": False,
                    "system_prompt": "Eres un arquitecto de software experto que analiza documentación técnica y proporciona soluciones.",
                    "response_guidelines": [
                        "Usa terminología técnica precisa",
                        "Proporciona ejemplos de código cuando sea relevante",
                        "Identifica patrones y mejores prácticas",
                        "Señala trade-offs arquitectónicos"
                    ],
                    "intent_prompts": {
                        "GENERAL": {
                            "name": "Análisis Técnico",
                            "prompt": """Analiza la documentación técnica:
1. Identifica componentes y arquitectura del sistema
2. Evalúa patrones de diseño utilizados
3. Señala mejores prácticas y anti-patrones
4. Proporciona recomendaciones técnicas

CONTEXTO: {context}""",
                            "enabled": True
                        }
                    }
                },
                "custom": {
                    "name": "Personalizado",
                    "description": "Sector personalizado definido por el usuario",
                    "enabled": False,
                    "system_prompt": "Eres un asistente inteligente que proporciona respuestas precisas y útiles.",
                    "response_guidelines": [
                        "Sé claro y conciso",
                        "Proporciona información basada en el contexto",
                        "Estructura tus respuestas de manera lógica"
                    ],
                    "intent_prompts": {
                        "GENERAL": {
                            "name": "Consulta General",
                            "prompt": """Responde a la consulta basándote en el contexto:

CONTEXTO: {context}""",
                            "enabled": True
                        }
                    }
                }
            }
        }

    def load_prompts(self) -> Dict[str, Any]:
        """Carga la configuración de prompts desde el archivo"""
        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.debug(f"Loaded prompts from {self.prompts_file}")
            return config
        except FileNotFoundError:
            logger.warning(f"Prompts file not found: {self.prompts_file}")
            default_config = self._get_default_prompt_configuration()
            self.save_prompts(default_config)
            return default_config
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing prompts file: {e}")
            raise

    def save_prompts(self, config: Dict[str, Any], create_backup: bool = True):
        """
        Guarda la configuración de prompts

        Args:
            config: Configuración a guardar
            create_backup: Si crear backup del archivo anterior
        """
        try:
            if create_backup and os.path.exists(self.prompts_file):
                self._create_backup()

            config["last_updated"] = datetime.now().isoformat()

            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved prompts to {self.prompts_file}")

        except Exception as e:
            logger.error(f"Error saving prompts: {e}")
            raise

    def _create_backup(self):
        """Crea backup del archivo de prompts actual"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(
                self.BACKUP_DIR,
                f"custom_prompts_{timestamp}.json"
            )

            with open(self.prompts_file, 'r', encoding='utf-8') as src:
                with open(backup_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())

            logger.info(f"Created backup: {backup_file}")
            self._cleanup_old_backups()

        except Exception as e:
            logger.error(f"Error creating backup: {e}")

    def _cleanup_old_backups(self):
        """Elimina backups antiguos, manteniendo solo los últimos MAX_BACKUPS"""
        try:
            backups = sorted(
                Path(self.BACKUP_DIR).glob("custom_prompts_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            for backup in backups[self.MAX_BACKUPS:]:
                backup.unlink()
                logger.debug(f"Removed old backup: {backup}")

        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")

    def get_active_sector(self) -> str:
        """Obtiene el sector activo actual"""
        config = self.load_prompts()
        return config.get("active_sector", "academic_research")

    def set_active_sector(self, sector_id: str):
        """
        Establece el sector activo

        Args:
            sector_id: ID del sector a activar
        """
        config = self.load_prompts()

        if sector_id not in config["sectors"]:
            raise ValueError(f"Sector no encontrado: {sector_id}")

        config["active_sector"] = sector_id
        self.save_prompts(config)
        logger.info(f"Active sector changed to: {sector_id}")

    def get_sector_config(self, sector_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene la configuración de un sector específico

        Args:
            sector_id: ID del sector (usa el activo si no se especifica)

        Returns:
            Configuración del sector
        """
        config = self.load_prompts()
        target_sector = sector_id or config.get("active_sector", "academic_research")

        if target_sector not in config["sectors"]:
            logger.warning(f"Sector not found: {target_sector}, using default")
            target_sector = "academic_research"

        return config["sectors"][target_sector]

    def update_sector_config(self, sector_id: str, sector_config: Dict[str, Any]):
        """
        Actualiza la configuración de un sector

        Args:
            sector_id: ID del sector
            sector_config: Nueva configuración del sector
        """
        config = self.load_prompts()
        config["sectors"][sector_id] = sector_config
        self.save_prompts(config)
        logger.info(f"Updated sector config: {sector_id}")

    def add_custom_sector(self, sector_id: str, sector_config: Dict[str, Any]):
        """
        Agrega un nuevo sector personalizado

        Args:
            sector_id: ID del nuevo sector
            sector_config: Configuración del sector
        """
        config = self.load_prompts()

        if sector_id in config["sectors"]:
            raise ValueError(f"Sector ya existe: {sector_id}")

        config["sectors"][sector_id] = sector_config
        self.save_prompts(config)
        logger.info(f"Added custom sector: {sector_id}")

    def delete_sector(self, sector_id: str):
        """
        Elimina un sector personalizado

        Args:
            sector_id: ID del sector a eliminar
        """
        config = self.load_prompts()

        if sector_id not in config["sectors"]:
            raise ValueError(f"Sector no encontrado: {sector_id}")

        # No permitir eliminar sector activo
        if sector_id == config.get("active_sector"):
            raise ValueError("No se puede eliminar el sector activo")

        del config["sectors"][sector_id]
        self.save_prompts(config)
        logger.info(f"Deleted sector: {sector_id}")

    def export_config(self) -> str:
        """
        Exporta la configuración completa

        Returns:
            JSON string de la configuración
        """
        config = self.load_prompts()
        return json.dumps(config, indent=2, ensure_ascii=False)

    def import_config(self, config_json: str):
        """
        Importa configuración desde JSON

        Args:
            config_json: JSON string con la configuración
        """
        try:
            config = json.loads(config_json)
            self.save_prompts(config, create_backup=True)
            logger.info("Configuration imported successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing import config: {e}")
            raise ValueError("JSON inválido")


# Instancia global
prompt_storage = PromptStorage()
