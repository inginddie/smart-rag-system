# -*- coding: utf-8 -*-
"""
Panel de diseño de prompts para configuración dinámica del RAG por sector
"""

import gradio as gr
from typing import Dict, List, Any, Tuple, Optional
import json
from datetime import datetime
from src.utils.logger import setup_logger
from src.admin.prompt_design_manager import prompt_design_manager, PromptDesignManager

logger = setup_logger()


class PromptDesignPanel:
    """Panel UI para configuración de prompts especializados"""

    def __init__(self, prompt_manager: Optional[PromptDesignManager] = None):
        """
        Inicializa el panel

        Args:
            prompt_manager: Instancia de PromptDesignManager (usa la global si no se proporciona)
        """
        self.prompt_manager = prompt_manager or prompt_design_manager

    def create_interface(self) -> gr.Tab:
        """Crea la interfaz completa del panel de diseño de prompts"""

        with gr.Tab("🎨 Diseño de Prompts") as prompt_tab:
            gr.Markdown("# 🎨 Configurador de Prompts por Sector")
            gr.Markdown(
                "_Personaliza el comportamiento del RAG para diferentes dominios y necesidades_"
            )

            # Estadísticas generales
            with gr.Row():
                with gr.Column():
                    stats_display = gr.Markdown(self._get_stats_markdown())
                    refresh_stats_btn = gr.Button("🔄 Actualizar Stats", size="sm")

            gr.Markdown("---")

            # Selector de sector activo
            with gr.Row():
                with gr.Column(scale=3):
                    gr.Markdown("### 🎯 Sector Activo")
                    gr.Markdown(
                        "_Selecciona el sector que determinará cómo responde el RAG_"
                    )

                    sector_dropdown = gr.Dropdown(
                        choices=self._get_sector_choices(),
                        value=self._get_active_sector_id(),
                        label="Sector Activo",
                        interactive=True
                    )

                    active_sector_info = gr.Markdown(self._get_active_sector_info())

                with gr.Column(scale=1):
                    change_sector_btn = gr.Button(
                        "✅ Activar Sector Seleccionado",
                        variant="primary",
                        size="lg"
                    )
                    sector_result = gr.Markdown("")

            gr.Markdown("---")

            # Tabs para diferentes configuraciones
            with gr.Tabs():
                # Tab 1: Configuración del sector actual
                with gr.Tab("⚙️ Configurar Sector"):
                    self._create_sector_config_tab()

                # Tab 2: Probar prompts
                with gr.Tab("🧪 Probar Prompts"):
                    test_result_display = self._create_test_prompts_tab()

                # Tab 3: Crear nuevo sector
                with gr.Tab("➕ Nuevo Sector"):
                    create_result_display = self._create_new_sector_tab()

                # Tab 4: Gestionar sectores
                with gr.Tab("📋 Gestionar Sectores"):
                    manage_result_display = self._create_manage_sectors_tab()

                # Tab 5: Import/Export
                with gr.Tab("💾 Import/Export"):
                    import_export_result = self._create_import_export_tab()

            # Event handlers
            refresh_stats_btn.click(
                fn=self._get_stats_markdown,
                outputs=[stats_display]
            )

            change_sector_btn.click(
                fn=self._change_active_sector,
                inputs=[sector_dropdown],
                outputs=[sector_result, active_sector_info, stats_display]
            )

            sector_dropdown.change(
                fn=self._preview_sector_info,
                inputs=[sector_dropdown],
                outputs=[active_sector_info]
            )

        return prompt_tab

    def _create_sector_config_tab(self):
        """Crea el tab de configuración del sector"""
        gr.Markdown("### ⚙️ Configuración del Sector Actual")
        gr.Markdown("_Personaliza el comportamiento del sector activo_")

        # System Prompt
        with gr.Accordion("🤖 System Prompt", open=True):
            gr.Markdown("_Define el comportamiento base del asistente_")

            current_sector_id = self._get_active_sector_id()
            current_config = self.prompt_manager.get_sector_info(current_sector_id)

            system_prompt_text = gr.Textbox(
                label="System Prompt",
                value=current_config.get("system_prompt", ""),
                lines=5,
                placeholder="Eres un asistente especializado en..."
            )

            update_system_btn = gr.Button("💾 Actualizar System Prompt")
            system_result = gr.Markdown("")

            update_system_btn.click(
                fn=self._update_system_prompt,
                inputs=[system_prompt_text],
                outputs=[system_result]
            )

        # Intent Prompts
        with gr.Accordion("🎯 Prompts por Tipo de Consulta", open=True):
            gr.Markdown("_Personaliza cómo responde según el tipo de consulta_")

            intent_type_dropdown = gr.Dropdown(
                choices=["GENERAL", "DEFINITION", "COMPARISON", "STATE_OF_ART", "GAP_ANALYSIS"],
                value="GENERAL",
                label="Tipo de Consulta"
            )

            intent_prompt_name = gr.Textbox(
                label="Nombre del Prompt",
                placeholder="Ej: Análisis de Mercado"
            )

            intent_prompt_text = gr.Textbox(
                label="Prompt Template",
                lines=10,
                placeholder="Analiza la información...\n\nCONTEXTO: {context}",
                info="Usa {context} donde se insertará la información recuperada"
            )

            update_intent_btn = gr.Button("💾 Actualizar Intent Prompt")
            intent_result = gr.Markdown("")

            update_intent_btn.click(
                fn=self._update_intent_prompt,
                inputs=[intent_type_dropdown, intent_prompt_name, intent_prompt_text],
                outputs=[intent_result]
            )

        # Response Guidelines
        with gr.Accordion("📋 Directrices de Respuesta", open=False):
            gr.Markdown("_Define reglas que el asistente debe seguir_")

            guidelines_list = gr.Markdown(self._get_guidelines_markdown())

            new_guideline = gr.Textbox(
                label="Nueva Directriz",
                placeholder="Ej: Cita siempre las fuentes con formato APA"
            )

            with gr.Row():
                add_guideline_btn = gr.Button("➕ Agregar Directriz", variant="primary")
                remove_guideline_text = gr.Textbox(
                    label="Directriz a Eliminar",
                    placeholder="Copia la directriz exacta a eliminar"
                )
                remove_guideline_btn = gr.Button("➖ Eliminar Directriz", variant="stop")

            guideline_result = gr.Markdown("")

            add_guideline_btn.click(
                fn=self._add_guideline,
                inputs=[new_guideline],
                outputs=[guideline_result, guidelines_list]
            )

            remove_guideline_btn.click(
                fn=self._remove_guideline,
                inputs=[remove_guideline_text],
                outputs=[guideline_result, guidelines_list]
            )

    def _create_test_prompts_tab(self) -> gr.Markdown:
        """Crea el tab de prueba de prompts"""
        gr.Markdown("### 🧪 Probar Configuración de Prompts")
        gr.Markdown("_Verifica cómo responderá el sistema con la configuración actual_")

        test_sector_dropdown = gr.Dropdown(
            choices=self._get_sector_choices(),
            value=self._get_active_sector_id(),
            label="Sector a Probar"
        )

        test_intent_dropdown = gr.Dropdown(
            choices=["GENERAL", "DEFINITION", "COMPARISON", "STATE_OF_ART", "GAP_ANALYSIS"],
            value="GENERAL",
            label="Tipo de Intención"
        )

        test_query_input = gr.Textbox(
            label="Query de Prueba",
            placeholder="Ej: ¿Cuáles son las tendencias del mercado en 2024?",
            lines=2
        )

        test_btn = gr.Button("🔍 Probar Configuración", variant="primary")

        test_result = gr.Markdown("_Ingresa una query y presiona 'Probar Configuración'_")

        test_btn.click(
            fn=self._test_prompt_config,
            inputs=[test_sector_dropdown, test_intent_dropdown, test_query_input],
            outputs=[test_result]
        )

        return test_result

    def _create_new_sector_tab(self) -> gr.Markdown:
        """Crea el tab de creación de nuevo sector"""
        gr.Markdown("### ➕ Crear Nuevo Sector Personalizado")
        gr.Markdown("_Define un nuevo dominio con configuración específica_")

        with gr.Column():
            new_sector_id = gr.Textbox(
                label="ID del Sector",
                placeholder="Ej: financial_analysis (sin espacios, minúsculas)",
                info="Identificador único para el sector"
            )

            new_sector_name = gr.Textbox(
                label="Nombre del Sector",
                placeholder="Ej: Análisis Financiero"
            )

            new_sector_desc = gr.Textbox(
                label="Descripción",
                placeholder="Ej: Análisis de estados financieros, valoración de empresas",
                lines=2
            )

            new_sector_system_prompt = gr.Textbox(
                label="System Prompt",
                placeholder="Eres un analista financiero experto...",
                lines=5
            )

            new_sector_guidelines = gr.Textbox(
                label="Directrices (una por línea)",
                placeholder="Usa métricas financieras estándar\nCita fuentes de datos\nEvita recomendaciones de inversión",
                lines=4,
                info="Ingresa cada directriz en una nueva línea"
            )

            create_sector_btn = gr.Button("✨ Crear Sector", variant="primary", size="lg")

            create_result = gr.Markdown("")

            create_sector_btn.click(
                fn=self._create_new_sector,
                inputs=[
                    new_sector_id,
                    new_sector_name,
                    new_sector_desc,
                    new_sector_system_prompt,
                    new_sector_guidelines
                ],
                outputs=[create_result]
            )

        return create_result

    def _create_manage_sectors_tab(self) -> gr.Markdown:
        """Crea el tab de gestión de sectores"""
        gr.Markdown("### 📋 Gestionar Sectores Existentes")

        sectors_info = gr.Markdown(self._get_all_sectors_markdown())

        with gr.Row():
            refresh_sectors_btn = gr.Button("🔄 Actualizar Lista")
            delete_sector_id = gr.Textbox(
                label="ID del Sector a Eliminar",
                placeholder="Ej: custom_sector"
            )
            delete_sector_btn = gr.Button("🗑️ Eliminar Sector", variant="stop")

        manage_result = gr.Markdown("")

        refresh_sectors_btn.click(
            fn=self._get_all_sectors_markdown,
            outputs=[sectors_info]
        )

        delete_sector_btn.click(
            fn=self._delete_sector,
            inputs=[delete_sector_id],
            outputs=[manage_result, sectors_info]
        )

        return manage_result

    def _create_import_export_tab(self) -> gr.Markdown:
        """Crea el tab de import/export"""
        gr.Markdown("### 💾 Importar/Exportar Configuración")

        with gr.Row():
            with gr.Column():
                gr.Markdown("#### 📤 Exportar")
                export_btn = gr.Button("📥 Exportar Configuración Completa")
                export_file = gr.File(label="Configuración Exportada")

            with gr.Column():
                gr.Markdown("#### 📥 Importar")
                import_file = gr.File(label="Archivo de Configuración JSON")
                import_btn = gr.Button("📤 Importar Configuración", variant="primary")

        import_export_result = gr.Markdown("")

        export_btn.click(
            fn=self._export_config,
            outputs=[export_file, import_export_result]
        )

        import_btn.click(
            fn=self._import_config,
            inputs=[import_file],
            outputs=[import_export_result]
        )

        return import_export_result

    # Helper methods
    def _get_stats_markdown(self) -> str:
        """Genera markdown con estadísticas"""
        stats = self.prompt_manager.get_statistics()

        return f"""
### 📊 Estadísticas del Sistema

| Métrica | Valor |
|---------|-------|
| **Sectores Totales** | {stats['total_sectors']} |
| **Sectores Habilitados** | {stats['enabled_sectors']} |
| **Sector Activo** | {stats['active_sector_name']} ({stats['active_sector_id']}) |
| **Intent Prompts Totales** | {stats['total_intent_prompts']} |
| **Directrices Totales** | {stats['total_guidelines']} |
| **Versión** | {stats['version']} |
| **Última Actualización** | {stats['last_updated'][:19] if stats['last_updated'] != 'N/A' else 'N/A'} |
"""

    def _get_sector_choices(self) -> List[Tuple[str, str]]:
        """Obtiene lista de sectores para dropdown"""
        sectors = self.prompt_manager.get_all_sectors()
        return [(f"{v['name']} ({k})", k) for k, v in sectors.items()]

    def _get_active_sector_id(self) -> str:
        """Obtiene ID del sector activo"""
        active_id, _ = self.prompt_manager.get_active_sector()
        return active_id

    def _get_active_sector_info(self) -> str:
        """Obtiene info del sector activo"""
        active_id, active_config = self.prompt_manager.get_active_sector()
        return self._format_sector_info(active_id, active_config)

    def _preview_sector_info(self, sector_id: str) -> str:
        """Preview de info del sector"""
        config = self.prompt_manager.get_sector_info(sector_id)
        return self._format_sector_info(sector_id, config)

    def _format_sector_info(self, sector_id: str, config: Dict[str, Any]) -> str:
        """Formatea información del sector"""
        enabled = "✅ Habilitado" if config.get("enabled", False) else "❌ Deshabilitado"
        guidelines_count = len(config.get("response_guidelines", []))
        intents_count = len(config.get("intent_prompts", {}))

        return f"""
**{config.get('name', sector_id)}** ({sector_id})

_{config.get('description', 'Sin descripción')}_

- **Estado**: {enabled}
- **Directrices**: {guidelines_count}
- **Intent Prompts**: {intents_count}
"""

    def _get_guidelines_markdown(self) -> str:
        """Genera markdown con lista de directrices"""
        active_id = self._get_active_sector_id()
        config = self.prompt_manager.get_sector_info(active_id)
        guidelines = config.get("response_guidelines", [])

        if not guidelines:
            return "_No hay directrices configuradas_"

        md = "**Directrices Actuales:**\n\n"
        for i, guideline in enumerate(guidelines, 1):
            md += f"{i}. {guideline}\n"

        return md

    def _get_all_sectors_markdown(self) -> str:
        """Genera markdown con todos los sectores"""
        sectors = self.prompt_manager.get_all_sectors()
        active_id, _ = self.prompt_manager.get_active_sector()

        md = "### 📚 Sectores Configurados\n\n"

        for sector_id, config in sectors.items():
            is_active = "🎯 **ACTIVO**" if sector_id == active_id else ""
            enabled = "✅" if config.get("enabled", False) else "❌"

            md += f"#### {enabled} {config.get('name', sector_id)} {is_active}\n"
            md += f"**ID**: `{sector_id}`  \n"
            md += f"**Descripción**: {config.get('description', 'N/A')}  \n"
            md += f"**Directrices**: {len(config.get('response_guidelines', []))}  \n"
            md += f"**Intent Prompts**: {len(config.get('intent_prompts', {}))}  \n"
            md += "\n---\n\n"

        return md

    # Action methods
    def _change_active_sector(self, sector_id: str) -> Tuple[str, str, str]:
        """Cambia el sector activo"""
        success = self.prompt_manager.set_active_sector(sector_id)

        if success:
            config = self.prompt_manager.get_sector_info(sector_id)
            result = f"✅ **Sector activado exitosamente**\n\nAhora el RAG usará: **{config.get('name', sector_id)}**"
        else:
            result = "❌ **Error al cambiar sector**\n\nVerifica que el sector exista."

        return result, self._get_active_sector_info(), self._get_stats_markdown()

    def _update_system_prompt(self, new_prompt: str) -> str:
        """Actualiza el system prompt"""
        if not new_prompt.strip():
            return "❌ El system prompt no puede estar vacío"

        active_id = self._get_active_sector_id()
        success = self.prompt_manager.update_system_prompt(active_id, new_prompt)

        if success:
            return f"✅ **System prompt actualizado** para el sector: {active_id}"
        else:
            return "❌ **Error** al actualizar system prompt"

    def _update_intent_prompt(
        self, intent_type: str, prompt_name: str, prompt_text: str
    ) -> str:
        """Actualiza un intent prompt"""
        if not prompt_text.strip():
            return "❌ El prompt no puede estar vacío"

        active_id = self._get_active_sector_id()
        success = self.prompt_manager.update_intent_prompt(
            active_id, intent_type, prompt_text, prompt_name
        )

        if success:
            return f"✅ **Intent prompt actualizado**: {intent_type} ({prompt_name})"
        else:
            return "❌ **Error** al actualizar intent prompt"

    def _add_guideline(self, guideline: str) -> Tuple[str, str]:
        """Agrega una directriz"""
        if not guideline.strip():
            return "❌ La directriz no puede estar vacía", self._get_guidelines_markdown()

        active_id = self._get_active_sector_id()
        success = self.prompt_manager.add_response_guideline(active_id, guideline)

        if success:
            result = f"✅ **Directriz agregada**: {guideline}"
        else:
            result = "❌ **Error** o directriz duplicada"

        return result, self._get_guidelines_markdown()

    def _remove_guideline(self, guideline: str) -> Tuple[str, str]:
        """Elimina una directriz"""
        if not guideline.strip():
            return "❌ Especifica la directriz a eliminar", self._get_guidelines_markdown()

        active_id = self._get_active_sector_id()
        success = self.prompt_manager.remove_response_guideline(active_id, guideline)

        if success:
            result = f"✅ **Directriz eliminada**: {guideline}"
        else:
            result = "❌ **No se encontró** la directriz"

        return result, self._get_guidelines_markdown()

    def _test_prompt_config(
        self, sector_id: str, intent_type: str, test_query: str
    ) -> str:
        """Prueba la configuración de prompts"""
        if not test_query.strip():
            return "❌ Ingresa una query de prueba"

        try:
            test_result = self.prompt_manager.test_prompt_configuration(
                sector_id, test_query, intent_type
            )

            md = f"""
### 🧪 Resultado de Prueba

**Sector**: {test_result.sector_name} (`{test_result.sector_id}`)
**Intención**: {intent_type}
**Query**: _{test_result.test_query}_

---

#### 🤖 System Prompt que se usará:
```
{test_result.system_prompt[:500]}{'...' if len(test_result.system_prompt) > 500 else ''}
```

---

#### 🎯 Intent Prompt que se usará:
```
{test_result.intent_prompt[:500]}{'...' if len(test_result.intent_prompt) > 500 else ''}
```

---

#### 📋 Comportamiento Esperado:
{test_result.expected_behavior}
"""
            return md

        except Exception as e:
            return f"❌ **Error en prueba**: {str(e)}"

    def _create_new_sector(
        self,
        sector_id: str,
        name: str,
        description: str,
        system_prompt: str,
        guidelines_text: str
    ) -> str:
        """Crea un nuevo sector"""
        if not all([sector_id, name, system_prompt]):
            return "❌ **Campos requeridos**: ID, Nombre y System Prompt"

        # Parsear guidelines
        guidelines = [
            g.strip() for g in guidelines_text.split('\n')
            if g.strip()
        ]

        try:
            success = self.prompt_manager.create_custom_sector(
                sector_id, name, description, system_prompt, guidelines
            )

            if success:
                return f"""
✅ **Sector creado exitosamente**

**ID**: `{sector_id}`
**Nombre**: {name}
**Directrices**: {len(guidelines)}

Ahora puedes activarlo desde el selector de sector.
"""
            else:
                return "❌ **Error** al crear sector (puede que ya exista)"

        except Exception as e:
            return f"❌ **Error**: {str(e)}"

    def _delete_sector(self, sector_id: str) -> Tuple[str, str]:
        """Elimina un sector"""
        if not sector_id.strip():
            return "❌ Especifica el ID del sector", self._get_all_sectors_markdown()

        try:
            success = self.prompt_manager.delete_sector(sector_id)

            if success:
                result = f"✅ **Sector eliminado**: {sector_id}"
            else:
                result = "❌ **Error** al eliminar (¿es el sector activo?)"

        except Exception as e:
            result = f"❌ **Error**: {str(e)}"

        return result, self._get_all_sectors_markdown()

    def _export_config(self) -> Tuple[str, str]:
        """Exporta la configuración"""
        try:
            config_json = self.prompt_manager.export_configuration()

            # Guardar en archivo temporal
            filename = f"prompt_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = f"/tmp/{filename}"

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(config_json)

            return filepath, "✅ **Configuración exportada** exitosamente"

        except Exception as e:
            return None, f"❌ **Error** al exportar: {str(e)}"

    def _import_config(self, file_obj) -> str:
        """Importa configuración"""
        if file_obj is None:
            return "❌ Selecciona un archivo JSON"

        try:
            with open(file_obj.name, 'r', encoding='utf-8') as f:
                config_json = f.read()

            success = self.prompt_manager.import_configuration(config_json)

            if success:
                return "✅ **Configuración importada** exitosamente\n\n⚠️ Recarga la página para ver cambios"
            else:
                return "❌ **Error** al importar configuración"

        except Exception as e:
            return f"❌ **Error**: {str(e)}"


# Instancia global
prompt_design_panel = PromptDesignPanel()
