#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Panel de Memoria para Gradio UI
Visualización y gestión del sistema de memoria conversacional
"""

import gradio as gr
from typing import Optional
from src.services.rag_service import RAGService


class MemoryPanel:
    """Panel de administración de memoria para la UI"""
    
    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service
    
    def get_memory_stats_markdown(self) -> str:
        """Genera markdown con estadísticas de memoria"""
        try:
            stats = self.rag_service.get_memory_stats()
            
            conv_stats = stats.get('conversation', {})
            sem_stats = stats.get('semantic', {})
            
            md = "### 🧠 Sistema de Memoria\n\n"
            
            # Estadísticas conversacionales
            md += "#### 💬 Memoria Conversacional\n"
            md += f"- **Sesiones activas:** {conv_stats.get('total_sessions', 0)}\n"
            md += f"- **Mensajes totales:** {conv_stats.get('total_messages', 0)}\n"
            md += f"- **Promedio mensajes/sesión:** {conv_stats.get('avg_messages_per_session', 0):.1f}\n"
            md += f"- **Límite por sesión:** {conv_stats.get('max_conversation_length', 50)}\n\n"
            
            # Estadísticas semánticas
            md += "#### 🔍 Memoria Semántica\n"
            md += f"- **Memorias almacenadas:** {sem_stats.get('total_memories', 0)}\n"
            md += f"- **Importancia promedio:** {sem_stats.get('avg_importance', 0):.2f}\n"
            md += f"- **Accesos promedio:** {sem_stats.get('avg_access_count', 0):.1f}\n"
            md += f"- **Capacidad máxima:** {sem_stats.get('max_memories', 100)}\n"
            
            return md
        except Exception as e:
            return f"_Error obteniendo estadísticas: {e}_"
    
    def get_sessions_list(self) -> str:
        """Lista todas las sesiones activas"""
        try:
            sessions = self.rag_service.get_all_conversations()
            
            if not sessions:
                return "_No hay sesiones activas_"
            
            md = "### 📋 Sesiones Activas\n\n"
            for session_id in sessions:
                summary = self.rag_service.get_conversation_summary(session_id)
                if summary.get('exists'):
                    md += f"**{session_id}**\n"
                    md += f"- Mensajes: {summary['total_messages']}\n"
                    md += f"- Usuario: {summary['user_messages']} | Asistente: {summary['assistant_messages']}\n"
                    
                    if summary.get('first_message'):
                        first_content = summary['first_message']['content'][:50]
                        md += f"- Primer mensaje: _{first_content}..._\n"
                    
                    md += "\n"
            
            return md
        except Exception as e:
            return f"_Error obteniendo sesiones: {e}_"
    
    def get_session_history(self, session_id: str, limit: int = 10) -> str:
        """Obtiene el historial de una sesión específica"""
        if not session_id or not session_id.strip():
            return "_Ingresa un ID de sesión_"
        
        try:
            history = self.rag_service.get_conversation_history(session_id, limit=limit)
            
            if not history:
                return f"_No se encontró la sesión '{session_id}'_"
            
            md = f"### 💬 Historial de Sesión: {session_id}\n\n"
            
            for i, msg in enumerate(history, 1):
                role = "👤 Usuario" if msg['role'] == 'user' else "🤖 Asistente"
                content = msg['content']
                timestamp = msg.get('timestamp', 'N/A')
                
                md += f"**{i}. {role}** _{timestamp}_\n"
                md += f"> {content}\n\n"
            
            return md
        except Exception as e:
            return f"_Error obteniendo historial: {e}_"
    
    def search_memories(self, query: str, top_k: int = 5) -> str:
        """Busca en las memorias semánticas"""
        if not query or not query.strip():
            return "_Ingresa una consulta de búsqueda_"
        
        try:
            results = self.rag_service.search_agent_memories(query, top_k=top_k)
            
            if not results:
                return f"_No se encontraron memorias para: '{query}'_"
            
            md = f"### 🔍 Resultados de Búsqueda: '{query}'\n\n"
            
            for i, result in enumerate(results, 1):
                score = result['score']
                content = result['content']
                agent_id = result['metadata'].get('agent_id', 'Unknown')
                access_count = result.get('access_count', 0)
                
                md += f"**{i}. Score: {score:.2f}** (Agente: {agent_id}, Accesos: {access_count})\n"
                md += f"> {content}\n\n"
            
            return md
        except Exception as e:
            return f"_Error en búsqueda: {e}_"
    
    def clear_session(self, session_id: str) -> str:
        """Limpia una sesión específica"""
        if not session_id or not session_id.strip():
            return "❌ Ingresa un ID de sesión"
        
        try:
            success = self.rag_service.clear_conversation(session_id)
            if success:
                return f"✅ Sesión '{session_id}' eliminada correctamente"
            else:
                return f"⚠️ No se encontró la sesión '{session_id}'"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def create_memory_interface(self):
        """Crea la interfaz de gestión de memoria"""
        with gr.TabItem("🧠 Sistema de Memoria"):
            gr.Markdown("""
            ## Sistema de Memoria Conversacional
            
            Gestiona y visualiza la memoria del sistema RAG Agentic.
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    # Estadísticas
                    stats_display = gr.Markdown(value=self.get_memory_stats_markdown())
                    refresh_stats_btn = gr.Button("🔄 Actualizar Estadísticas", variant="secondary")
                
                with gr.Column(scale=1):
                    # Lista de sesiones
                    sessions_display = gr.Markdown(value=self.get_sessions_list())
                    refresh_sessions_btn = gr.Button("🔄 Actualizar Sesiones", variant="secondary")
            
            gr.Markdown("---")
            
            # Visualización de historial
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📜 Ver Historial de Sesión")
                    session_id_input = gr.Textbox(
                        label="ID de Sesión",
                        placeholder="Ej: session_001"
                    )
                    limit_input = gr.Slider(
                        minimum=5,
                        maximum=50,
                        value=10,
                        step=5,
                        label="Número de mensajes"
                    )
                    view_history_btn = gr.Button("👁️ Ver Historial", variant="primary")
                    
                    history_display = gr.Markdown(value="_Selecciona una sesión_")
            
            gr.Markdown("---")
            
            # Búsqueda en memorias
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 🔍 Buscar en Memorias Semánticas")
                    search_query_input = gr.Textbox(
                        label="Consulta de Búsqueda",
                        placeholder="Ej: preferencias de usuario"
                    )
                    search_top_k = gr.Slider(
                        minimum=1,
                        maximum=20,
                        value=5,
                        step=1,
                        label="Número de resultados"
                    )
                    search_btn = gr.Button("🔍 Buscar", variant="primary")
                    
                    search_results_display = gr.Markdown(value="_Ingresa una consulta_")
            
            gr.Markdown("---")
            
            # Gestión de sesiones
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 🗑️ Gestión de Sesiones")
                    clear_session_input = gr.Textbox(
                        label="ID de Sesión a Eliminar",
                        placeholder="Ej: session_001"
                    )
                    clear_session_btn = gr.Button("🗑️ Eliminar Sesión", variant="stop")
                    clear_status = gr.Textbox(label="Estado", interactive=False)
            
            # Event handlers
            refresh_stats_btn.click(
                fn=self.get_memory_stats_markdown,
                outputs=stats_display
            )
            
            refresh_sessions_btn.click(
                fn=self.get_sessions_list,
                outputs=sessions_display
            )
            
            view_history_btn.click(
                fn=self.get_session_history,
                inputs=[session_id_input, limit_input],
                outputs=history_display
            )
            
            search_btn.click(
                fn=self.search_memories,
                inputs=[search_query_input, search_top_k],
                outputs=search_results_display
            )
            
            clear_session_btn.click(
                fn=self.clear_session,
                inputs=clear_session_input,
                outputs=clear_status
            )
