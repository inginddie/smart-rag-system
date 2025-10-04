# -*- coding: utf-8 -*-
"""
Panel de administración para gestión de keywords
"""

import gradio as gr
from typing import Dict, List, Any, Tuple
import json
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger()

class AdminPanel:
    """Panel de administración para keywords de agentes"""
    
    def __init__(self, rag_service):
        self.rag_service = rag_service
        self.keyword_manager = rag_service.get_keyword_manager()
    
    def create_admin_interface(self) -> gr.Tab:
        """Crea la interfaz de administración"""
        
        with gr.Tab("🔧 Administración") as admin_tab:
            gr.Markdown("## 🔧 Gestión de Keywords para Agentes")
            gr.Markdown("_Configura dinámicamente las keywords que activan cada agente_")
            
            # Estado del sistema
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📊 Estado del Sistema")
                    system_stats = gr.Markdown(self._get_system_stats_markdown())
                    refresh_stats_btn = gr.Button("🔄 Actualizar Estadísticas", size="sm")
            
            # Prueba de activación
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 🧪 Prueba de Activación de Agentes")
                    gr.Markdown("_Prueba qué agentes se activarían con una query específica_")
                    test_query_input = gr.Textbox(
                        label="Query de prueba",
                        placeholder="Ej: Find research papers about deep learning",
                        value="Find research papers about deep learning"
                    )
                    test_btn = gr.Button("🔍 Probar Query", variant="primary")
                    test_results = gr.Markdown("_Ingresa una query y presiona 'Probar Query'_")
            
            gr.Markdown("---")
            
            # Gestión de keywords por capacidad
            gr.Markdown("### 🎯 Gestión de Keywords por Capacidad")
            
            with gr.Accordion("📄 DOCUMENT_SEARCH", open=True):
                doc_search_keywords, doc_search_result = self._create_capability_manager(
                    "DocumentSearchAgent", "DOCUMENT_SEARCH"
                )
            
            with gr.Accordion("🔄 SYNTHESIS", open=False):
                synthesis_keywords, synthesis_result = self._create_capability_manager(
                    "DocumentSearchAgent", "SYNTHESIS"
                )
            
            with gr.Accordion("🎓 ACADEMIC_ANALYSIS", open=False):
                academic_keywords, academic_result = self._create_capability_manager(
                    "DocumentSearchAgent", "ACADEMIC_ANALYSIS"
                )
            
            gr.Markdown("---")
            
            # Configuración del agente
            gr.Markdown("### ⚙️ Configuración del Agente")
            
            with gr.Row():
                with gr.Column():
                    threshold_slider = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        step=0.05,
                        label="Threshold de Activación",
                        value=self._get_agent_threshold("DocumentSearchAgent"),
                        info="Score mínimo para activar el agente (0.0 - 1.0)"
                    )
                    update_threshold_btn = gr.Button("💾 Actualizar Threshold")
                    threshold_result = gr.Markdown("")
            
            gr.Markdown("---")
            
            # Acciones globales
            gr.Markdown("### 🛠️ Acciones del Sistema")
            
            with gr.Row():
                reload_btn = gr.Button("🔄 Recargar Configuración")
                reset_btn = gr.Button("⚠️ Resetear a Defaults", variant="stop")
            
            with gr.Row():
                export_btn = gr.Button("📤 Exportar Config")
                export_output = gr.File(label="Configuración Exportada")
            
            global_result = gr.Markdown("")
            
            # Event handlers
            refresh_stats_btn.click(
                fn=self._refresh_system_stats,
                outputs=system_stats
            )
            
            test_btn.click(
                fn=self._test_query_activation,
                inputs=test_query_input,
                outputs=test_results
            )
            
            update_threshold_btn.click(
                fn=self._update_threshold,
                inputs=threshold_slider,
                outputs=threshold_result
            )
            
            reload_btn.click(
                fn=self._reload_config,
                outputs=[global_result, system_stats]
            )
            
            reset_btn.click(
                fn=self._reset_to_defaults,
                outputs=[global_result, system_stats]
            )
            
            export_btn.click(
                fn=self._export_config,
                outputs=[export_output, global_result]
            )
        
        return admin_tab
    
    def _create_capability_manager(self, agent_name: str, capability: str) -> Tuple[gr.Textbox, gr.Markdown]:
        """Crea interfaz de gestión para una capacidad"""
        
        current_keywords = self._get_capability_keywords(agent_name, capability)
        
        with gr.Row():
            with gr.Column(scale=3):
                keywords_display = gr.Textbox(
                    label="Keywords Actuales",
                    value=", ".join(current_keywords),
                    lines=2,
                    interactive=False
                )
            
            with gr.Column(scale=1):
                gr.Markdown(f"**Total:** {len(current_keywords)} keywords")
        
        with gr.Row():
            new_keyword = gr.Textbox(
                label="Nueva Keyword",
                placeholder="Ej: investigar, buscar, etc.",
                scale=3
            )
            add_btn = gr.Button("➕ Agregar", scale=1, variant="primary")
        
        with gr.Row():
            remove_keyword = gr.Textbox(
                label="Keyword a Eliminar",
                placeholder="Escribe la keyword exacta",
                scale=3
            )
            remove_btn = gr.Button("🗑️ Eliminar", scale=1, variant="stop")
        
        result_md = gr.Markdown("")
        
        # Event handlers
        add_btn.click(
            fn=lambda kw: self._add_keyword(agent_name, capability, kw),
            inputs=new_keyword,
            outputs=[result_md, keywords_display]
        )
        
        remove_btn.click(
            fn=lambda kw: self._remove_keyword(agent_name, capability, kw),
            inputs=remove_keyword,
            outputs=[result_md, keywords_display]
        )
        
        return keywords_display, result_md
    
    # ======= HELPER METHODS =======
    
    def _get_system_stats_markdown(self) -> str:
        """Genera markdown con estadísticas del sistema"""
        try:
            stats = self.keyword_manager.get_system_stats()
            
            return f"""
**Estadísticas del Sistema:**

- 🤖 **Agentes Totales:** {stats['total_agents']}
- ✅ **Agentes Activos:** {stats['active_agents']}
- 🎯 **Capacidades Totales:** {stats['total_capabilities']}
- 🔑 **Keywords Totales:** {stats['total_keywords']}
- 📅 **Última Actualización:** {stats.get('last_updated', 'N/A')}
- ✔️ **Configuración Válida:** {'Sí' if stats.get('config_valid', False) else 'No'}
"""
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return f"❌ **Error obteniendo estadísticas:** {str(e)}"
    
    def _refresh_system_stats(self) -> str:
        """Refresca las estadísticas del sistema"""
        self.keyword_manager.reload_config()
        return self._get_system_stats_markdown()
    
    def _test_query_activation(self, query: str) -> str:
        """Prueba qué agentes se activarían con una query"""
        if not query or not query.strip():
            return "⚠️ **Por favor ingresa una query válida**"
        
        try:
            results = self.keyword_manager.test_query_activation(query)
            
            if not results:
                return "❌ **No hay agentes configurados**"
            
            output = f"### Resultados para: \"{query}\"\n\n"
            
            for agent_name, result in results.items():
                score = result['score']
                threshold = result['threshold']
                would_activate = result['would_activate']
                matches = result['matches']
                
                status_icon = "✅" if would_activate else "❌"
                
                output += f"#### {status_icon} **{agent_name}**\n\n"
                output += f"- **Score:** {score:.2f} / {threshold:.2f} (threshold)\n"
                output += f"- **Estado:** {'🟢 SE ACTIVARÍA' if would_activate else '🔴 NO SE ACTIVARÍA'}\n"
                output += f"- **Capacidades Matched:** {result['matched_capabilities']} / {result['total_capabilities']}\n"
                
                if matches:
                    output += "\n**Keywords Detectadas:**\n"
                    for capability, keywords in matches.items():
                        output += f"- `{capability}`: {', '.join(keywords)}\n"
                else:
                    output += "\n_No se detectaron keywords_\n"
                
                output += "\n---\n\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error testing query: {e}")
            return f"❌ **Error:** {str(e)}"
    
    def _get_capability_keywords(self, agent_name: str, capability: str) -> List[str]:
        """Obtiene keywords de una capacidad"""
        try:
            return self.keyword_manager.get_capability_keywords(agent_name, capability)
        except Exception as e:
            logger.error(f"Error getting keywords: {e}")
            return []
    
    def _add_keyword(self, agent_name: str, capability: str, keyword: str) -> Tuple[str, str]:
        """Agrega una keyword"""
        if not keyword or not keyword.strip():
            return "⚠️ **La keyword no puede estar vacía**", self._get_keywords_display(agent_name, capability)
        
        keyword = keyword.strip().lower()
        
        try:
            success = self.keyword_manager.add_keyword(agent_name, capability, keyword)
            
            if success:
                new_display = self._get_keywords_display(agent_name, capability)
                return f"✅ **Keyword '{keyword}' agregada exitosamente**", new_display
            else:
                return f"❌ **Error agregando keyword '{keyword}'**", self._get_keywords_display(agent_name, capability)
                
        except Exception as e:
            logger.error(f"Error adding keyword: {e}")
            return f"❌ **Error:** {str(e)}", self._get_keywords_display(agent_name, capability)
    
    def _remove_keyword(self, agent_name: str, capability: str, keyword: str) -> Tuple[str, str]:
        """Elimina una keyword"""
        if not keyword or not keyword.strip():
            return "⚠️ **Especifica la keyword a eliminar**", self._get_keywords_display(agent_name, capability)
        
        keyword = keyword.strip().lower()
        
        try:
            success = self.keyword_manager.remove_keyword(agent_name, capability, keyword)
            
            if success:
                new_display = self._get_keywords_display(agent_name, capability)
                return f"✅ **Keyword '{keyword}' eliminada exitosamente**", new_display
            else:
                return f"❌ **Error eliminando keyword '{keyword}'**", self._get_keywords_display(agent_name, capability)
                
        except Exception as e:
            logger.error(f"Error removing keyword: {e}")
            return f"❌ **Error:** {str(e)}", self._get_keywords_display(agent_name, capability)
    
    def _get_keywords_display(self, agent_name: str, capability: str) -> str:
        """Obtiene display de keywords actuales"""
        keywords = self._get_capability_keywords(agent_name, capability)
        return ", ".join(keywords) if keywords else "(sin keywords)"
    
    def _get_agent_threshold(self, agent_name: str) -> float:
        """Obtiene el threshold de un agente"""
        try:
            config = self.keyword_manager.get_agent_config(agent_name)
            return config.get('threshold', 0.3)
        except Exception as e:
            logger.error(f"Error getting threshold: {e}")
            return 0.3
    
    def _update_threshold(self, threshold: float) -> str:
        """Actualiza el threshold del agente"""
        try:
            success = self.keyword_manager.update_threshold("DocumentSearchAgent", threshold)
            
            if success:
                return f"✅ **Threshold actualizado a {threshold:.2f}**"
            else:
                return "❌ **Error actualizando threshold**"
                
        except Exception as e:
            logger.error(f"Error updating threshold: {e}")
            return f"❌ **Error:** {str(e)}"
    
    def _reload_config(self) -> Tuple[str, str]:
        """Recarga la configuración desde disco"""
        try:
            self.keyword_manager.reload_config()
            stats = self._get_system_stats_markdown()
            return "✅ **Configuración recargada exitosamente**", stats
        except Exception as e:
            logger.error(f"Error reloading config: {e}")
            return f"❌ **Error:** {str(e)}", self._get_system_stats_markdown()
    
    def _reset_to_defaults(self) -> Tuple[str, str]:
        """Resetea la configuración a valores por defecto"""
        try:
            success = self.keyword_manager.reset_to_defaults()
            stats = self._get_system_stats_markdown()
            
            if success:
                return "✅ **Configuración reseteada a valores por defecto**", stats
            else:
                return "❌ **Error reseteando configuración**", stats
                
        except Exception as e:
            logger.error(f"Error resetting config: {e}")
            return f"❌ **Error:** {str(e)}", self._get_system_stats_markdown()
    
    def _export_config(self) -> Tuple[str, str]:
        """Exporta la configuración actual"""
        try:
            config = self.keyword_manager.export_config()
            
            # Guardar a archivo temporal
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"agent_keywords_export_{timestamp}.json"
            filepath = f"config/{filename}"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return filepath, f"✅ **Configuración exportada a {filename}**"
            
        except Exception as e:
            logger.error(f"Error exporting config: {e}")
            return None, f"❌ **Error:** {str(e)}"
