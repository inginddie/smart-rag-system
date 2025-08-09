# -*- coding: utf-8 -*-
"""
Enhanced Gradio App with Query Advisor Integration
MODIFICATION of existing ui/gradio_app.py
"""

from typing import List, Tuple

import gradio as gr
from gradio.themes.soft import Soft

from config.settings import settings
from src.services.rag_service import RAGService
from src.utils.logger import setup_logger

logger = setup_logger()


class GradioRAGApp:
    """
    Aplicación Gradio para el sistema RAG con Query Advisor integrado:
    - Detección inteligente de intención académica
    - Expansión automática de consultas
    - Selección dinámica de modelos
    - **NUEVO: Query Advisor con sugerencias y analytics**
    - Feedback visual completo para transparencia del sistema
    """

    def __init__(self):
        """
        Inicializa la aplicación con el servicio RAG enhanced.
        """
        self.rag_service = RAGService()
        self.initialized = False

    def initialize_service(self) -> str:
        """
        Inicializa el servicio RAG y proporciona feedback detallado al usuario.
        """
        try:
            if self.rag_service.initialize():
                self.initialized = True
                return (
                    "✅ Sistema RAG inicializado correctamente con todas las funcionalidades avanzadas habilitadas:\n"
                    + "🎯 Detección de intención académica\n"
                    + "🔍 Expansión automática de consultas\n"
                    + "🤖 Selección inteligente de modelos\n"
                    + "💡 Query Advisor con sugerencias inteligentes\n"
                    + "📊 Analytics de uso y aprendizaje\n"
                    + "📚 Base de documentos indexada y lista"
                )
            else:
                return "⚠️ Sistema inicializado pero no se encontraron documentos para indexar"
        except Exception as e:
            logger.error(f"Error initializing service: {e}")
            return f"❌ Error al inicializar: {str(e)}"

    def _format_intent_info(self, intent_info: dict) -> str:
        """Formatea la información de detección de intención para presentación al usuario."""
        if not intent_info:
            return ""

        intent_type = intent_info.get("detected_intent", "unknown")
        confidence = intent_info.get("confidence", 0)
        specialized_prompt = intent_info.get("specialized_prompt_used", False)
        processing_time = intent_info.get("processing_time_ms", 0)

        intent_names = {
            "definition": "📖 Definición Conceptual",
            "comparison": "⚖️ Análisis Comparativo",
            "state_of_art": "🌟 Estado del Arte",
            "gap_analysis": "🔍 Análisis de Gaps",
            "unknown": "❓ Consulta General",
            "error": "⚠️ Error de Clasificación",
        }

        intent_name = intent_names.get(intent_type, f"❓ {intent_type}")

        info_parts = [f"**Tipo de consulta detectada:** {intent_name}"]

        if confidence > 0:
            confidence_emoji = (
                "🎯" if confidence >= 0.8 else "🎲" if confidence >= 0.6 else "❓"
            )
            info_parts.append(f"**Confianza:** {confidence_emoji} {confidence:.0%}")

        if specialized_prompt and intent_type not in ["unknown", "error"]:
            info_parts.append(
                "**Respuesta optimizada:** ✨ Usando template académico especializado"
            )

        if processing_time > 0:
            info_parts.append(f"**Tiempo de análisis:** ⚡ {processing_time:.1f}ms")

        return "\n".join(info_parts)

    def _format_expansion_info(self, expansion_info: dict) -> str:
        """Formatea la información de expansión de consulta para mostrar al usuario."""
        if not expansion_info or expansion_info.get("expansion_count", 0) == 0:
            return ""

        expanded_terms = expansion_info.get("expanded_terms", [])
        processing_time = expansion_info.get("processing_time_ms", 0)
        strategy_used = expansion_info.get("strategy_used", "unknown")

        info_parts = [f"**Términos expandidos:** 🔍 {', '.join(expanded_terms[:5])}"]

        if len(expanded_terms) > 5:
            info_parts.append(f"*... y {len(expanded_terms) - 5} términos más*")

        if strategy_used != "unknown":
            strategy_names = {
                "conservative": "Conservadora",
                "moderate": "Moderada",
                "comprehensive": "Comprehensiva",
            }
            strategy_display = strategy_names.get(strategy_used, strategy_used)
            info_parts.append(f"**Estrategia:** 📊 {strategy_display}")

        if processing_time > 0:
            info_parts.append(f"**Tiempo de expansión:** ⚡ {processing_time:.1f}ms")

        return "\n".join(info_parts)

    def _format_model_info(self, model_info: dict) -> str:
        """Formatea la información del modelo seleccionado para mostrar al usuario."""
        if not model_info:
            return ""

        model_name = model_info.get("selected_model", "unknown")
        complexity_score = model_info.get("complexity_score", 0)
        reasoning = model_info.get("reasoning", "")

        model_names = {
            "gpt-4o": "🧠 GPT-4o (Análisis Académico Profundo)",
            "gpt-4o-mini": "⚡ GPT-4o-mini (Respuesta Rápida y Eficiente)",
            "gpt-3.5-turbo": "💨 GPT-3.5-turbo (Consultas Directas)",
        }

        model_display = model_names.get(model_name, f"🤖 {model_name}")

        info_parts = [f"**Modelo seleccionado:** {model_display}"]

        if complexity_score > 0:
            complexity_emoji = (
                "🔥"
                if complexity_score >= 0.7
                else "⚡" if complexity_score >= 0.4 else "💨"
            )
            info_parts.append(
                f"**Complejidad detectada:** {complexity_emoji} {complexity_score:.0%}"
            )

        if reasoning and len(reasoning) < 100:
            info_parts.append(f"**Razón:** {reasoning}")

        return "\n".join(info_parts)

    def _format_advisor_info(self, advisor_info: dict) -> str:
        """
        NUEVO: Formatea información del Query Advisor
        """
        if not advisor_info or advisor_info.get("error"):
            return ""

        effectiveness_score = advisor_info.get("effectiveness_score", 0)
        suggestions = advisor_info.get("suggestions", [])
        tips = advisor_info.get("contextual_tips", [])
        suggestion_shown = advisor_info.get("suggestion_shown", False)

        info_parts = []

        # Effectiveness score con visual indicator
        if effectiveness_score > 0:
            score_emoji = (
                "🎯"
                if effectiveness_score >= 0.8
                else "⚡" if effectiveness_score >= 0.6 else "🔧"
            )
            score_text = (
                "Excelente"
                if effectiveness_score >= 0.8
                else "Buena" if effectiveness_score >= 0.6 else "Mejorable"
            )
            info_parts.append(
                f"**Efectividad de consulta:** {score_emoji} {score_text} ({effectiveness_score:.1%})"
            )

        # Suggestions si las hay
        if suggestions:
            info_parts.append("**💡 Sugerencias de mejora:**")
            for i, suggestion in enumerate(suggestions[:2], 1):  # Max 2 suggestions
                priority_emoji = "🔥" if suggestion.get("priority", 3) == 1 else "⚡"
                info_parts.append(
                    f"   {priority_emoji} *{suggestion.get('reason', 'Mejora sugerida')}*"
                )

                # Show reformulated query if not too long
                reformulated = suggestion.get("reformulated_query", "")
                if len(reformulated) < 100:
                    info_parts.append(f'      → "{reformulated}"')

        # Contextual tips
        if tips:
            info_parts.append("**💭 Tips contextuales:**")
            for tip in tips[:1]:  # Show only first tip
                info_parts.append(f"   📝 {tip.get('tip_text', '')}")
                example = tip.get("example", "")
                if example and len(example) < 80:
                    info_parts.append(f"      *Ejemplo: {example}*")

        return "\n".join(info_parts)

    def _format_analytics_summary(self) -> str:
        """
        NUEVO: Genera resumen de analytics para mostrar en UI
        """
        try:
            summary = self.rag_service.get_analytics_summary()

            if summary.get("status") in ["no_data", "error"]:
                return "_No hay datos de analytics disponibles aún._"

            total_queries = summary.get("total_queries", 0)
            avg_effectiveness = summary.get("avg_effectiveness", 0)
            adoption_rate = summary.get("suggestion_adoption_rate", 0)

            info_parts = [
                f"**📊 Analytics del Sistema:**",
                f"• Total consultas procesadas: **{total_queries}**",
                f"• Efectividad promedio: **{avg_effectiveness:.1%}**",
                f"• Tasa adopción sugerencias: **{adoption_rate:.1%}**",
            ]

            # Intent-specific stats
            intent_stats = summary.get("intent_stats", {})
            if intent_stats:
                info_parts.append("**Por tipo de consulta:**")
                for intent, stats in list(intent_stats.items())[:3]:  # Top 3
                    success_rate = stats.get("success_rate", 0)
                    query_count = stats.get("query_count", 0)
                    info_parts.append(
                        f"• {intent}: {success_rate:.1%} éxito ({query_count} consultas)"
                    )

            return "\n".join(info_parts)

        except Exception as e:
            logger.error(f"Error generating analytics summary: {e}")
            return "_Error al generar resumen de analytics._"

    def chat_response(
        self, message: str, history: List[Tuple[str, str]]
    ) -> Tuple[str, str]:
        """
        Procesa las consultas del usuario con Query Advisor integrado.

        ENHANCED: Ahora incluye information del Query Advisor en el panel lateral
        """
        if not self.initialized:
            return (
                "❌ El sistema no está inicializado. Por favor inicialízalo primero.",
                "",
            )

        if not message.strip():
            return "Por favor, escribe una pregunta académica.", ""

        try:
            # Obtener respuesta completa con Query Advisor habilitado
            result = self.rag_service.query(
                message, include_sources=True, include_advisor=True
            )

            # La respuesta principal es lo que el usuario realmente quiere leer
            main_response = result["answer"]

            # Construir información del sistema de manera modular
            system_info_parts = []

            # Sección 1: Query Advisor (NUEVO - PRIORITARIO)
            advisor_info = result.get("advisor_info", {})
            if advisor_info and not advisor_info.get("error"):
                advisor_details = self._format_advisor_info(advisor_info)
                if advisor_details:
                    system_info_parts.append("### 💡 Query Advisor")
                    system_info_parts.append(advisor_details)

            # Sección 2: Análisis de la consulta (detección de intención)
            intent_info = result.get("intent_info", {})
            if intent_info:
                intent_details = self._format_intent_info(intent_info)
                if intent_details:
                    system_info_parts.append("### 🎯 Análisis de Consulta")
                    system_info_parts.append(intent_details)

            # Sección 3: Expansión de consulta (términos adicionales utilizados)
            expansion_info = result.get("expansion_info", {})
            if expansion_info and expansion_info.get("expansion_count", 0) > 0:
                expansion_details = self._format_expansion_info(expansion_info)
                if expansion_details:
                    system_info_parts.append("### 🔍 Expansión de Consulta")
                    system_info_parts.append(expansion_details)

            # Sección 4: Selección de modelo (por qué se eligió este modelo)
            model_info = result.get("model_info", {})
            if model_info:
                model_details = self._format_model_info(model_info)
                if model_details:
                    system_info_parts.append("### 🤖 Selección de Modelo")
                    system_info_parts.append(model_details)

            # Sección 5: Fuentes consultadas (transparencia sobre los documentos utilizados)
            sources = result.get("sources", [])
            if sources:
                system_info_parts.append("### 📚 Fuentes Consultadas")
                source_list = []
                for i, source in enumerate(
                    sources[:3], 1
                ):  # Mostrar máximo 3 fuentes principales
                    file_name = source.get("metadata", {}).get(
                        "file_name", "Documento desconocido"
                    )
                    source_list.append(f"{i}. **{file_name}**")
                system_info_parts.append("\n".join(source_list))

                if len(sources) > 3:
                    system_info_parts.append(
                        f"*... y {len(sources) - 3} fuentes adicionales*"
                    )

            # Combinar toda la información del sistema en un panel cohesivo
            system_info = "\n\n".join(system_info_parts) if system_info_parts else ""

            return main_response, system_info

        except Exception as e:
            logger.error(f"Error in chat response: {e}")
            error_msg = f"❌ Error al procesar la pregunta: {str(e)}"
            return error_msg, ""

    def track_suggestion_adoption(self, query: str, adopted: bool) -> str:
        """
        NUEVO: Track cuando el usuario adopta una sugerencia
        """
        try:
            self.rag_service.track_suggestion_adoption(query, adopted)
            return f"✅ Feedback registrado: sugerencia {'adoptada' if adopted else 'rechazada'}"
        except Exception as e:
            return f"❌ Error registrando feedback: {str(e)}"

    def reindex_documents(self) -> str:
        """Reindexar documentos cuando se agregan nuevos archivos."""
        try:
            count = self.rag_service.reindex_documents()
            if count > 0:
                return f"✅ Reindexados {count} documentos correctamente"
            else:
                return "⚠️ No se encontraron documentos para reindexar"
        except Exception as e:
            logger.error(f"Error reindexing: {e}")
            return f"❌ Error al reindexar: {str(e)}"

    def get_faq_markdown(self) -> str:
        """Genera contenido dinámico de preguntas frecuentes."""
        faqs = self.rag_service.get_frequent_questions()
        if not faqs:
            return "_No hay preguntas frecuentes registradas aún._"
        lines = "\n".join(f"- {q}" for q in faqs)
        return f"**Preguntas frecuentes:**\n{lines}"

    def get_improvement_recommendations(self) -> str:
        """
        NUEVO: Obtiene recomendaciones de mejora del sistema
        """
        try:
            recommendations = self.rag_service.get_improvement_recommendations()

            if not recommendations:
                return "✅ **El sistema está funcionando óptimamente.** No hay recomendaciones de mejora en este momento."

            lines = ["**🔧 Recomendaciones de Mejora:**"]
            for rec in recommendations[:3]:  # Max 3 recommendations
                priority_emoji = (
                    "🔥"
                    if rec.get("priority") == "high"
                    else "⚡" if rec.get("priority") == "medium" else "💡"
                )
                lines.append(
                    f"{priority_emoji} **{rec.get('category', 'General')}:** {rec.get('message', '')}"
                )

                if "metric" in rec:
                    lines.append(f"   *Métrica actual: {rec['metric']:.1%}*")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return "_Error al obtener recomendaciones._"

    def create_interface(self) -> gr.Blocks:
        """
        Crea la interfaz de usuario completa con Query Advisor integrado.

        ENHANCED: Incluye nuevo panel de Query Advisor y analytics
        """
        with gr.Blocks(
            theme=Soft(),
            css="""
            /* Estilos existentes + nuevos para Query Advisor */
            .system-info {
                background-color: #f8f9fa !important;
                border: 1px solid #e9ecef !important;
                border-radius: 8px !important;
                padding: 16px !important;
                margin: 8px 0 !important;
                font-size: 0.9em !important;
                color: #2c3e50 !important;
                min-height: 100px !important;
                overflow-y: auto !important;
                max-height: 600px !important;
                word-wrap: break-word !important;
            }

/* Asegurar que el markdown sea visible */
            .system-info .gr-markdown {
                color: #2c3e50 !important;
                background: transparent !important;
                padding: 0 !important;
                margin: 0 !important;
            }

            .system-info h3 {
                color: #34495e !important;
                font-weight: bold !important;
                margin: 12px 0 8px 0 !important;
                border-bottom: 2px solid #3498db !important;
                padding-bottom: 4px !important;
            }

            .system-info h4 {
                color: #2c3e50 !important;
                font-weight: 600 !important;
                margin: 8px 0 4px 0 !important;
            }

            .system-info p {
                color: #2c3e50 !important;
                margin: 4px 0 !important;
                line-height: 1.4 !important;
            }

            .system-info strong {
                color: #2c3e50 !important;
                font-weight: bold !important;
            }

            .system-info em {
                color: #555 !important;
                font-style: italic !important;
            }

            /* Fix específico para Query Advisor */
            .advisor-panel {
                background-color: #e8f4fd !important;
                border: 2px solid #3498db !important;
                border-radius: 10px !important;
                padding: 12px !important;
                margin: 8px 0 !important;
            }

            .effectiveness-high { 
                color: #27ae60 !important; 
                font-weight: bold !important; 
            }

            .effectiveness-medium { 
                color: #f39c12 !important; 
                font-weight: bold !important; 
            }

            .effectiveness-low { 
                color: #e74c3c !important; 
                font-weight: bold !important; 
            }

            /* Fix para el contenedor principal */
            .gr-column {
                min-width: 0 !important;
                flex-shrink: 0 !important;
            }

            /* Asegurar que el texto no se corte */
            .gr-markdown {
                overflow: visible !important;
                word-wrap: break-word !important;
                white-space: pre-wrap !important;
            }

            /* Fix para evitar overflow */
            .gradio-container {
                max-width: 100% !important;
                overflow-x: hidden !important;
            }

            /* Indicadores visuales para diferentes tipos de intención */
            .intent-indicator {
                display: inline-block !important;
                padding: 4px 8px !important;
                border-radius: 12px !important;
                font-size: 0.8em !important;
                font-weight: bold !important;
                margin-right: 8px !important;
            }

            .definition { 
                background-color: #e3f2fd !important; 
                color: #1565c0 !important; 
            }

            .comparison { 
                background-color: #f3e5f5 !important; 
                color: #7b1fa2 !important; 
            }

            .state_of_art { 
                background-color: #e8f5e8 !important; 
                color: #2e7d32 !important; 
            }

            .gap_analysis { 
                background-color: #fff3e0 !important; 
                color: #ef6c00 !important; 
            }

            /* Fix para scroll suave */
            .system-info::-webkit-scrollbar {
                width: 8px;
            }

            .system-info::-webkit-scrollbar-track {
                background: #f1f1f1;
            }

            .system-info::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 4px;
            }

            .system-info::-webkit-scrollbar-thumb:hover {
                background: #555;
            }
            """,
        ) as interface:

            # Header principal con branding actualizado
            gr.HTML(
                """
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1>🤖 Sistema RAG Avanzado + Query Advisor</h1>
                <p>Especializado en IA para Historias de Usuario - Con Inteligencia Artificial Multicapa + Sugerencias Inteligentes</p>
                <p><small>
                    🎯 Detección automática de intención &nbsp;•&nbsp; 
                    🔍 Expansión inteligente de consultas &nbsp;•&nbsp; 
                    🤖 Selección dinámica de modelos &nbsp;•&nbsp;
                    💡 <strong>Query Advisor con sugerencias</strong> &nbsp;•&nbsp;
                    📊 Analytics y aprendizaje automático
                </small></p>
            </div>
            """
            )

            with gr.Tabs():
                # Tab principal - Chat Académico Inteligente + Advisor
                with gr.TabItem("💬 Chat + Query Advisor"):
                    gr.Markdown(
                        "### Asistente de Investigación con IA Multicapa + Advisor"
                    )
                    gr.Markdown(
                        """
                    Haz preguntas académicas y observa cómo el sistema combina múltiples técnicas de IA + **Query Advisor**:
                    - 🎯 **Detecta automáticamente** el tipo de consulta (definición, comparación, estado del arte, gaps)
                    - 🔍 **Expande tu consulta** con sinónimos académicos y términos relacionados relevantes  
                    - 🤖 **Selecciona el modelo apropiado** (GPT-4o para análisis complejos, GPT-4o-mini para consultas simples)  
                    - ✨ **Optimiza la respuesta** usando templates académicos especializados por tipo de intención
                    - 💡 **NUEVO: Analiza efectividad** y sugiere mejoras automáticamente para consultas subóptimas
                    - 📊 **Aprende de tu uso** para mejorar sugerencias futuras
                    - 📊 **Muestra todo el proceso** para transparencia y reproducibilidad académica
                    """
                    )

                    with gr.Row():
                        with gr.Column(scale=2):
                            # Área principal de conversación
                            chatbot = gr.Chatbot(
                                label="Conversación Académica Inteligente + Advisor",
                                height=500,
                                type="messages",
                                show_label=True,
                            )

                            with gr.Row():
                                msg = gr.Textbox(
                                    label="Tu pregunta de investigación",
                                    placeholder="Ej: Compare las metodologías de IA para historias de usuario...",
                                    scale=4,
                                    lines=2,
                                )
                                send_btn = gr.Button(
                                    "Enviar", variant="primary", scale=1
                                )

                            with gr.Row():
                                clear_btn = gr.Button(
                                    "🗑️ Limpiar Chat", variant="secondary"
                                )

                        with gr.Column(scale=1):
                            # Panel de información del sistema - ENHANCED con Query Advisor
                            system_info_display = gr.Markdown(
                                label="📊 Información del Sistema + Query Advisor",
                                value="*Envía una consulta para ver cómo el sistema analiza tu pregunta con IA multicapa + sugerencias inteligentes*",
                                elem_classes=["system-info"],
                                visible=True,
                            )

                    # Ejemplos académicos organizados por tipo + nuevos ejemplos de advisor
                    with gr.Accordion(
                        "📋 Ejemplos por Tipo de Consulta + Query Advisor", open=False
                    ):
                        gr.Markdown(
                            """
                        **🔵 Definiciones Conceptuales (Activará template + advisor para definiciones):**
                        - "¿Qué es Natural Language Processing en requirements engineering?"
                        - "Define machine learning aplicado a historias de usuario"
                        - "ML" *(consulta vaga que activará sugerencias del advisor)*
                        
                        **🟣 Análisis Comparativos (Activará template comparativo + sugerencias específicas):**
                        - "Compara supervised vs unsupervised learning para user stories"
                        - "Diferencias entre rule-based y ML approaches en requirements"
                        - "compara métodos" *(consulta imprecisa que activará advisor)*
                        
                        **🟢 Estado del Arte (Activará template temporal + tips contextuales):**
                        - "Estado del arte en IA para automatización de requirements"
                        - "Enfoques actuales en NLP para historias de usuario"
                        - "IA últimos años" *(consulta mejorable que activará sugerencias)*
                        
                        **🟠 Análisis de Gaps (Activará template de gaps + advisor para precisión):**
                        - "¿Qué limitaciones tienen los métodos actuales de NLP para user stories?"
                        - "Gaps de investigación en automated requirements engineering"
                        - "problemas actuales" *(consulta vaga que activará advisor con mejoras)*
                        
                        **💡 Casos especiales que activan Query Advisor:**
                        - Consultas muy cortas: "IA", "ML", "NLP"
                        - Consultas vagas: "métodos", "técnicas", "approaches"
                        - Consultas sin contexto: "compare algorithms"
                        """
                        )

                    # FAQ dinámicas - aprendizaje del sistema
                    faq_display = gr.Markdown(value=self.get_faq_markdown())

                    def respond(message, chat_history):
                        """Handler principal para las respuestas del chat con Query Advisor."""
                        if not message.strip():
                            return chat_history, "", self.get_faq_markdown(), ""

                        # Procesar la consulta a través del pipeline completo + Query Advisor
                        bot_response, system_info = self.chat_response(
                            message, chat_history
                        )

                        # Actualizar historial en formato compatible con Gradio
                        chat_history.append({"role": "user", "content": message})
                        chat_history.append(
                            {"role": "assistant", "content": bot_response}
                        )

                        return chat_history, "", self.get_faq_markdown(), system_info

                    # Event handlers para interacción del usuario
                    send_btn.click(
                        respond,
                        inputs=[msg, chatbot],
                        outputs=[chatbot, msg, faq_display, system_info_display],
                    )

                    msg.submit(
                        respond,
                        inputs=[msg, chatbot],
                        outputs=[chatbot, msg, faq_display, system_info_display],
                    )

                    clear_btn.click(
                        lambda: (
                            [],
                            "",
                            self.get_faq_markdown(),
                            "*Envía una consulta para ver el análisis multicapa + Query Advisor del sistema*",
                        ),
                        outputs=[chatbot, msg, faq_display, system_info_display],
                    )

                # Tab de administración del sistema - ENHANCED con analytics
                with gr.TabItem("⚙️ Administración + Analytics"):
                    gr.Markdown(
                        "### Gestión del Sistema RAG Inteligente + Query Advisor"
                    )

                    with gr.Row():
                        init_btn = gr.Button(
                            "🚀 Inicializar Sistema", variant="primary"
                        )
                        reindex_btn = gr.Button(
                            "📚 Reindexar Documentos", variant="secondary"
                        )

                    status_output = gr.Textbox(
                        label="Estado del Sistema", interactive=False, lines=3
                    )

                    # NUEVO: Panel de Analytics y Recomendaciones
                    with gr.Row():
                        with gr.Column():
                            analytics_display = gr.Markdown(
                                label="📊 Analytics del Sistema",
                                value=self._format_analytics_summary(),
                            )

                        with gr.Column():
                            recommendations_display = gr.Markdown(
                                label="🔧 Recomendaciones de Mejora",
                                value=self.get_improvement_recommendations(),
                            )

                    refresh_analytics_btn = gr.Button(
                        "🔄 Actualizar Analytics", variant="secondary"
                    )

                    # Información detallada de configuración
                    gr.Markdown(
                        "### Configuración del Sistema RAG Inteligente + Query Advisor"
                    )
                    gr.Markdown(
                        f"""
                    **💡 Query Advisor (NUEVO):**
                    - 🎯 **Estado**: `Habilitado y operativo`
                    - 📊 **Umbral efectividad**: `{getattr(self.rag_service.query_advisor, 'effectiveness_threshold', 0.7)}`
                    - 🔧 **Sugerencias automáticas**: `Activas para consultas <70% efectividad`
                    - 📈 **Analytics**: `Tracking de patrones y mejoras`
                    
                    **🧠 Detección de Intención Académica:**
                    - 🎯 **Estado**: `{'Habilitada' if settings.enable_intent_detection else 'Deshabilitada'}`
                    - 📊 **Umbral de confianza**: `{settings.intent_confidence_threshold}`
                    - ⚡ **Tiempo máximo de procesamiento**: `{settings.intent_max_processing_time_ms}ms`
                    
                    **🔍 Expansión Inteligente de Consultas:**
                    - 🎯 **Estado**: `{'Habilitada' if settings.enable_query_expansion else 'Deshabilitada'}`
                    - 📊 **Máximo términos expandidos**: `{settings.max_expansion_terms}`
                    - 🎨 **Estrategia de expansión**: `{settings.expansion_strategy}`
                    - ⚡ **Tiempo máximo de procesamiento**: `{settings.expansion_max_processing_time_ms}ms`
                    
                    **🤖 Selección Inteligente de Modelos:**
                    - 🧠 **Modelo para consultas complejas**: `{settings.complex_model}`
                    - ⚡ **Modelo para consultas simples**: `{settings.simple_model}`
                    - 🎯 **Umbral de complejidad**: `{settings.complexity_threshold}`
                    - 🔄 **Selección automática**: `{'Activada' if settings.enable_smart_selection else 'Desactivada'}`
                    
                    **📚 Configuración RAG Base:**
                    - 📁 **Directorio de documentos**: `{settings.documents_path}`
                    - 🗃️ **Base de datos vectorial**: `{settings.vector_db_path}`
                    - 🔤 **Modelo de embeddings**: `{settings.embedding_model}`
                    - 📊 **Tamaño de chunk**: `{settings.chunk_size}`
                    - 🔗 **Overlap de chunk**: `{settings.chunk_overlap}`
                    - 📖 **Documentos por consulta**: `{settings.max_documents}`
                    """
                    )

                # Tab de guía académica - ENHANCED con Query Advisor
                with gr.TabItem("📚 Guía de Investigación + Query Advisor"):
                    gr.Markdown(
                        """
                    ## 🎓 Sistema RAG Inteligente + Query Advisor para Investigación Académica
                    
                    ### 🧠 Inteligencia Artificial Multicapa + Sugerencias Inteligentes
                    
                    Este sistema combina **cinco niveles de IA** para optimizar tu experiencia de investigación:
                    
                    #### 🎯 **Nivel 1: Detección Automática de Intención**
                    El sistema analiza tu consulta en **menos de 200ms** para determinar qué tipo de respuesta necesitas:
                    
                    - **📖 Definición Conceptual** → Estructura la respuesta con definición formal, contexto histórico y aplicaciones
                    - **⚖️ Análisis Comparativo** → Organiza la información en análisis sistemático y tablas comparativas  
                    - **🌟 Estado del Arte** → Presenta cronología, tendencias actuales y consenso académico
                    - **🔍 Análisis de Gaps** → Identifica limitaciones, oportunidades y direcciones futuras
                    
                    #### 🔍 **Nivel 2: Expansión Inteligente de Consulta**
                    Basado en tu intención detectada, expande automáticamente tu consulta:
                    
                    - **Sinónimos académicos** → "machine learning" se expande a "ML", "AI", "predictive modeling"
                    - **Términos relacionados** → "user stories" incluye "acceptance criteria", "requirements"
                    - **Variaciones contextuales** → Adaptadas al tipo de consulta específica
                    
                    #### 🤖 **Nivel 3: Selección Inteligente de Modelo**
                    Basado en la complejidad de tu consulta expandida, elige automáticamente:
                    
                    - **🧠 GPT-4o** para análisis académicos complejos, comparaciones metodológicas y síntesis profundas
                    - **⚡ GPT-4o-mini** para definiciones claras, consultas directas y respuestas rápidas
                    
                    #### ✨ **Nivel 4: Optimización de Template**
                    Usando tu intención detectada, aplica templates académicos especializados:
                    
                    - **Estructura académica apropiada** para cada tipo de consulta
                    - **Enfoque metodológico específico** (cronológico, comparativo, analítico)
                    - **Formato optimizado** para tu contexto de investigación
                    
                    #### 💡 **Nivel 5: Query Advisor (NUEVO)**
                    Sistema inteligente de sugerencias y mejora continua:
                    
                    - **Análisis de efectividad** en tiempo real (score 0-100%)
                    - **Sugerencias automáticas** para consultas subóptimas (<70% efectividad)
                    - **Tips contextuales** específicos por tipo de intención detectada
                    - **Aprendizaje de patrones** para mejorar sugerencias futuras
                    - **Analytics de uso** para optimización continua del sistema
                    
                    ### 🚀 Cómo Aprovechar al Máximo el Sistema + Query Advisor
                    
                    #### **Para Investigación de Tesis sobre IA y User Stories:**
                    
                    **🔍 Exploración Inicial con Advisor:**
                    1. "Estado del arte en IA para historias de usuario" → *Activará análisis cronológico + tips temporales*
                    2. "IA" → *Query Advisor detectará baja efectividad y sugerirá: "¿Qué aplicaciones de IA existen para historias de usuario?"*
                    
                    **📊 Análisis Comparativo con Sugerencias:**
                    1. "Compara NLP vs ML" → *Advisor sugerirá contexto: "Compara NLP vs ML para análisis de requirements"*
                    2. "diferencias métodos" → *Advisor reformulará: "¿Cuáles son las diferencias entre métodos rule-based y ML para historias de usuario?"*
                    
                    **🎯 Identificación de Oportunidades con Precision:**
                    1. "problemas actuales" → *Advisor especificará: "¿Qué limitaciones técnicas tienen los métodos actuales de NLP para user stories?"*
                    2. "gaps investigación" → *Advisor contextualizará: "¿Qué gaps de investigación existen en automated requirements engineering?"*
                    
                    ### 💡 Query Advisor en Acción - Ejemplos Prácticos
                    
                    **Consulta Vaga → Sugerencia Inteligente:**
                    - ❌ "ML" → 💡 Advisor: "Sé más específico: 'Machine learning aplicado a historias de usuario'"
                    - ❌ "compara métodos" → 💡 Advisor: "Agrega contexto: 'Compara métodos de NLP vs rule-based para requirements'"
                    - ❌ "técnicas actuales" → 💡 Advisor: "Estructura como pregunta: '¿Cuáles son las técnicas actuales de IA para user stories?'"
                    
                    **Efectividad Alta (>80%) → Tips de Optimización:**
                    - ✅ "¿Qué técnicas de deep learning se usan para análisis semántico de historias de usuario?" 
                    - 💭 Tip: "Para consultas complejas, considera dividirla en sub-preguntas específicas"
                    
                    **Efectividad Media (60-80%) → Mejoras Específicas:**
                    - ⚡ "Compare supervised learning vs unsupervised para requirements"
                    - 💡 Advisor: "Especifica criterios: 'Compare supervised vs unsupervised learning en términos de accuracy y interpretabilidad'"
                    
                    ### 📊 Indicadores Visuales del Sistema + Query Advisor
                    
                    Observa el **panel lateral enhanced** durante tus consultas para ver:
                    
                    - **💡 Query Advisor (NUEVO)** con score de efectividad y reasoning
                    - **🔧 Sugerencias automáticas** para consultas mejorables con ejemplos
                    - **💭 Tips contextuales** específicos por tipo de intención detectada
                    - **🎯 Tipo de consulta detectada** con nivel de confianza y reasoning
                    - **🔍 Términos expandidos** agregados automáticamente con estrategia utilizada
                    - **🤖 Modelo seleccionado** y razón de la selección basada en complejidad  
                    - **✨ Optimización aplicada** (si usa template especializado)
                    - **📚 Fuentes consultadas** para tu respuesta específica
                    
                    ### 🎓 Resultados de Investigación Optimizados + Aprendizaje Continuo
                    
                    **Para Definiciones (con Query Advisor):**
                    - Estructura académica formal con contexto histórico
                    - Referencias a autores principales y papers fundamentales
                    - Conexiones con conceptos relacionados
                    - Expansión automática con sinónimos técnicos y variaciones
                    - **NUEVO:** Sugerencias si la definición solicitada es muy general
                    
                    **Para Comparaciones (con Mejoras Inteligentes):**
                    - Matrices comparativas sistemáticas
                    - Análisis de ventajas/desventajas equilibrado
                    - Recomendaciones basadas en contexto de uso
                    - Términos contrastivos agregados automáticamente
                    - **NUEVO:** Advisor sugiere criterios específicos si faltan
                    
                    **Para Estado del Arte (con Optimización Temporal):**
                    - Evolución temporal de enfoques
                    - Identificación de tendencias emergentes  
                    - Análisis de consenso vs controversias
                    - Expansión con indicadores temporales y de tendencia
                    - **NUEVO:** Tips para enfocar en marcos temporales específicos
                    
                    **Para Análisis de Gaps (con Precisión Enhanced):**
                    - Categorización de limitaciones por tipo
                    - Oportunidades específicas de investigación
                    - Conexión con trabajos futuros sugeridos
                    - Términos de limitación y oportunidad expandidos
                    - **NUEVO:** Advisor reformula consultas vagas sobre limitaciones
                    
                    ### 🔬 Optimización Continua con Analytics
                    
                    El **Query Advisor aprende** de tus patrones de uso:
                    - 📈 **Tracking de efectividad** por tipo de consulta y usuario
                    - 🎯 **Mejora de sugerencias** basada en adopción de recomendaciones
                    - 📊 **Analytics de patrones** para identificar consultas exitosas
                    - 🔧 **Recomendaciones de sistema** para optimizar rendimiento general
                    
                    ### 📈 Consejos para Consultas de Alta Calidad + Query Advisor
                    
                    **🎯 Trabaja con el Advisor para mejorar:**
                    - ❌ "machine learning" → 💡 Advisor te sugerirá contexto específico
                    - ✅ Adopta sugerencias: "¿Qué técnicas de machine learning se usan para analizar historias de usuario?"
                    - 🔍 *El sistema recordará tu preferencia y mejorará futuras sugerencias*
                    
                    **🔗 Permite que el Advisor detecte imprecisiones:**
                    - ❌ "compare algorithms" → 💡 Advisor: "Especifica dominio: 'Compare algoritmos de NLP para extracción de requirements'"
                    - ✅ La sugerencia incluirá context académico apropiado
                    - 🔍 *Sistema aprende qué tipos de comparación prefieres*
                    
                    **📊 Usa feedback del Advisor para iterar:**
                    - ⚡ Consulta inicial con efectividad 65% → Sugerencias del Advisor
                    - ✅ Adopta reformulación sugerida → Efectividad sube a 85%
                    - 🔍 *Patrón se registra para mejorar sugerencias futuras*
                    
                    ### 🚀 El Futuro de tu Investigación con Query Advisor
                    
                    Con este sistema inteligente multicapa + Advisor, puedes:
                    - **⚡ Acelerar** tu revisión de literatura 5-10x con expansión automática + sugerencias
                    - **🎯 Identificar** gaps de investigación automáticamente con detección de intención + precision advisor
                    - **📊 Comparar** metodologías de manera sistemática con templates especializados + criteria suggestions
                    - **🔍 Descubrir** conexiones entre diferentes líneas de investigación mediante expansión semántica + contextual tips
                    - **📈 Optimizar** la calidad académica con selección inteligente de modelos + effectiveness tracking
                    - **🔬 Reproducir** resultados con total transparencia del proceso + analytics de mejora
                    - **💡 Mejorar continuamente** tus skills de consulta académica con feedback inteligente personalizado
                    - **📚 Aprender** de patrones exitosos para formular mejores preguntas automáticamente
                    """
                    )

            # Event handlers para funcionalidades administrativas + analytics
            init_btn.click(fn=self.initialize_service, outputs=status_output)

            reindex_btn.click(fn=self.reindex_documents, outputs=status_output)

            refresh_analytics_btn.click(
                fn=lambda: (
                    self._format_analytics_summary(),
                    self.get_improvement_recommendations(),
                ),
                outputs=[analytics_display, recommendations_display],
            )

        return interface

    def launch(self, **kwargs):
        """
        Lanza la aplicación con configuración optimizada para investigación académica + Query Advisor.
        """
        interface = self.create_interface()

        # Configuración por defecto optimizada
        launch_kwargs = {
            "server_port": settings.server_port,
            "share": settings.share_gradio,
            "show_error": True,
            "quiet": False,
            **kwargs,
        }

        logger.info(
            f"Launching advanced RAG app with Query Advisor on port {launch_kwargs['server_port']}"
        )
        logger.info(
            "Features enabled: Intent Detection + Query Expansion + Smart Model Selection + Query Advisor + Analytics"
        )
        interface.launch(**launch_kwargs)
