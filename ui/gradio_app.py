# -*- coding: utf-8 -*-
import gradio as gr
from typing import List, Tuple
from src.services.rag_service import RAGService
from src.utils.logger import setup_logger
from config.settings import settings
from ui.components.admin_panel import AdminPanel

logger = setup_logger()

class GradioRAGApp:
    """Aplicación Gradio para el sistema RAG con selección inteligente de modelos"""
    
    def __init__(self):
        self.rag_service = RAGService()
        self.initialized = False
        # Inicializar admin panel desde el inicio (no requiere que el servicio esté inicializado)
        self.admin_panel = AdminPanel(self.rag_service)
    
    def initialize_service(self) -> str:
        """Inicializa el servicio RAG"""
        try:
            if self.rag_service.initialize():
                self.initialized = True
                return "✅ Sistema RAG inicializado correctamente con selección inteligente de modelos"
            else:
                return "⚠️ Sistema inicializado pero no se encontraron documentos para indexar"
        except Exception as e:
            logger.error(f"Error initializing service: {e}")
            return f"❌ Error al inicializar: {str(e)}"
    
    def chat_response(self, message: str, history: List[Tuple[str, str]], show_technical_info: bool = False) -> str:
        """Maneja las respuestas del chat con control de información técnica"""
        if not self.initialized:
            return "❌ El sistema no está inicializado. Por favor inicialízalo primero."
        
        if not message.strip():
            return "Por favor, escribe una pregunta."
        
        try:
            # Obtener respuesta con información del modelo
            result = self.rag_service.query(message)
            response = result['answer']
            
            # Información del agente (si se usó)
            agent_info = result.get('agent_info')
            if agent_info and agent_info.get('agent_used'):
                response += f"\n\n🤖 *Procesado por: {agent_info['agent_used']}*"
            
            # Solo mostrar información técnica si se solicita explícitamente o en modo DEBUG
            model_info = result.get('model_info', {})
            should_show_technical = (
                show_technical_info or 
                (settings.log_level == "DEBUG" and hasattr(settings, 'show_model_info_in_ui') and settings.show_model_info_in_ui)
            )
            
            if model_info and should_show_technical:
                model_name = model_info.get('selected_model', 'unknown')
                complexity = model_info.get('complexity_score', 0)
                response += f"\n\n📋 *Información técnica: Procesado con {model_name} (complejidad: {complexity:.2f})*"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat response: {e}")
            # Solo mostrar detalles técnicos si está habilitado
            if settings.show_technical_errors:
                return f"❌ Error al procesar la pregunta: {str(e)}"
            else:
                return "❌ Error al procesar la pregunta. Por favor, inténtalo de nuevo o contacta al administrador."
    
    def reindex_documents(self) -> str:
        """Reindexar documentos"""
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
        """Genera el texto Markdown de las preguntas frecuentes."""
        faqs = self.rag_service.get_frequent_questions()
        if not faqs:
            return "_No hay preguntas frecuentes registradas aún._"
        lines = "\n".join(f"- {q}" for q in faqs)
        return f"**Preguntas frecuentes:**\n{lines}"
    
    def create_interface(self) -> gr.Blocks:
        """Crea la interfaz de Gradio actualizada"""
        with gr.Blocks(
            title="Sistema RAG Avanzado - Investigación de Tesis",
            theme=gr.themes.Soft(),
        ) as interface:
            
            gr.HTML("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1>🤖 Sistema RAG Avanzado para Investigación</h1>
                <p>Especializado en IA para Historias de Usuario - Selección Inteligente de Modelos</p>
                <p><small>Usa automáticamente GPT-4o para análisis complejos y GPT-4o-mini para consultas simples</small></p>
            </div>
            """)
            
            with gr.Tabs():
                # Tab principal - Chat
                with gr.TabItem("💬 Chat Académico"):
                    gr.Markdown("### Asistente de Investigación")
                    gr.Markdown("Haz preguntas académicas sobre tus documentos. El sistema seleccionará automáticamente el modelo más apropiado.")
                    
                    # ChatInterface actualizado para nueva versión de Gradio
                    chatbot = gr.Chatbot(
                        label="Conversación Académica",
                        height=400,
                        type='messages'  # Corregir warning de Gradio
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            label="Tu pregunta de investigación",
                            placeholder="Ej: Compara las metodologías de IA para historias de usuario...",
                            scale=4
                        )
                        send_btn = gr.Button("Enviar", variant="primary", scale=1)
                    
                    with gr.Row():
                        clear_btn = gr.Button("🗑️ Limpiar Chat", variant="secondary")
                    
                    # Ejemplos académicos específicos para tu investigación
                    gr.Examples(
                        examples=[
                            "¿Cuáles son las principales metodologías de IA para mejorar historias de usuario?",
                            "Compara los enfoques de NLP vs Machine Learning en requirements engineering",
                            "¿Qué gaps de investigación existen en la automatización de historias de usuario?",
                            "Analiza las métricas de evaluación utilizadas en la literatura",
                            "¿Qué técnicas de deep learning se han aplicado a requirements?",
                            "Resume el estado del arte en IA para desarrollo ágil",
                        ],
                        inputs=msg
                    )

                    faq_display = gr.Markdown(value=self.get_faq_markdown())
                    
                    def respond(message, chat_history):
                        if not message.strip():
                            return chat_history, "", self.get_faq_markdown()
                        
                        # Obtener respuesta del RAG
                        bot_response = self.chat_response(message, chat_history)
                        
                        # Agregar al historial en formato correcto para Gradio
                        chat_history.append({"role": "user", "content": message})
                        chat_history.append({"role": "assistant", "content": bot_response})

                        return chat_history, "", self.get_faq_markdown()
                    
                    # Event handlers para el chat
                    send_btn.click(
                        respond,
                        inputs=[msg, chatbot],
                        outputs=[chatbot, msg, faq_display]
                    )
                    
                    msg.submit(
                        respond,
                        inputs=[msg, chatbot],
                        outputs=[chatbot, msg, faq_display]
                    )
                    
                    clear_btn.click(
                        lambda: ([], "", self.get_faq_markdown()),
                        outputs=[chatbot, msg, faq_display]
                    )
                
                # Tab de administración
                with gr.TabItem("⚙️ Administración"):
                    gr.Markdown("### Gestión del Sistema RAG")
                    
                    with gr.Row():
                        init_btn = gr.Button("🚀 Inicializar Sistema", variant="primary")
                        reindex_btn = gr.Button("📚 Reindexar Documentos", variant="secondary")
                    
                    status_output = gr.Textbox(
                        label="Estado del Sistema",
                        interactive=False,
                        lines=3
                    )
                    
                    # Información del sistema
                    gr.Markdown("### Configuración Actual")
                    gr.Markdown(f"""
                    **Selección Inteligente de Modelos:**
                    - 🧠 **Modelo para consultas complejas**: `{settings.complex_model}`
                    - ⚡ **Modelo para consultas simples**: `{settings.simple_model}`
                    - 🎯 **Umbral de complejidad**: `{settings.complexity_threshold}`
                    - 🔄 **Selección automática**: `{'Activada' if settings.enable_smart_selection else 'Desactivada'}`
                    
                    **Configuración RAG:**
                    - 📁 **Directorio de documentos**: `{settings.documents_path}`
                    - 🗃️ **Base de datos vectorial**: `{settings.vector_db_path}`
                    - 🔤 **Modelo de embeddings**: `{settings.embedding_model}`
                    - 📊 **Tamaño de chunk**: `{settings.chunk_size}`
                    - 🔗 **Overlap de chunk**: `{settings.chunk_overlap}`
                    - 📖 **Documentos por consulta**: `{settings.max_documents}`
                    """)
                
                # Tab de administración de keywords (HU2)
                # El admin panel ya está inicializado en __init__
                self.admin_panel.create_admin_interface()
                
                # Tab de ayuda académica
                with gr.TabItem("📚 Guía de Investigación"):
                    gr.Markdown("""
                    ## 🎓 Sistema RAG para Investigación de Tesis
                    
                    ### 🧠 Selección Inteligente de Modelos
                    
                    El sistema **selecciona automáticamente** el modelo más apropiado:
                    
                    **GPT-4o (Análisis Complejo)** se activa con:
                    - 🔬 **Palabras académicas**: "analiza", "compara", "evalúa", "metodología"
                    - 📊 **Análisis crítico**: "ventajas y desventajas", "limitaciones", "gaps"
                    - 🎯 **Estado del arte**: "literatura", "síntesis", "framework"
                    - 📝 **Investigación**: "paper", "estudio", "hallazgos"
                    
                    **GPT-4o-mini (Consultas Simples)** para:
                    - ❓ **Definiciones**: "¿Qué es...?", "Define..."
                    - 📋 **Listas**: "Lista las técnicas...", "Enumera..."
                    - 🔍 **Búsquedas básicas**: "Encuentra...", "Busca..."
                    
                    ### 🚀 Tipos de Consultas para tu Tesis
                    
                    #### **Estado del Arte** (→ GPT-4o)
                    - "Analiza el estado del arte en IA para historias de usuario"
                    - "¿Cuáles son las metodologías principales en la literatura?"
                    - "Sintetiza los enfoques de NLP en requirements engineering"
                    
                    #### **Comparaciones Metodológicas** (→ GPT-4o)
                    - "Compara los frameworks de Chen et al. vs Smith et al."
                    - "¿Cuáles son las ventajas y desventajas de cada enfoque?"
                    - "Evalúa críticamente las técnicas de machine learning aplicadas"
                    
                    #### **Gaps de Investigación** (→ GPT-4o)
                    - "¿Qué limitaciones identifican los estudios actuales?"
                    - "¿Dónde están los gaps en la automatización de requirements?"
                    - "¿Qué direcciones futuras sugiere la literatura?"
                    
                    #### **Consultas Específicas** (→ GPT-4o-mini)
                    - "¿Qué es una historia de usuario?"
                    - "Lista las técnicas de NLP mencionadas"
                    - "Define requirements engineering"
                    
                    ### 💡 Consejos para Mejores Resultados
                    
                    1. **Sé específico** en tus preguntas académicas
                    2. **Usa terminología técnica** para activar análisis profundo
                    3. **Pregunta por comparaciones** para obtener síntesis complejas
                    4. **Solicita gaps** para identificar oportunidades de investigación
                    5. **Pide citas específicas** mencionando autores cuando sea posible
                    
                    ### 📖 Preparación de Documentos
                    
                    1. **Organiza tus 159 PDFs** por categorías temáticas
                    2. **Procesa por lotes** (20-30 papers a la vez)
                    3. **Verifica nombres** descriptivos de archivos
                    4. **Inicia con papers fundamentales** antes de casos específicos
                    """)
            
            # Event handlers
            init_btn.click(
                fn=self.initialize_service,
                outputs=status_output
            )
            
            reindex_btn.click(
                fn=self.reindex_documents,
                outputs=status_output
            )
        
        return interface
    
    def launch(self, **kwargs):
        """Lanza la aplicación"""
        interface = self.create_interface()
        
        # Configuración por defecto
        launch_kwargs = {
            'server_port': settings.server_port,
            'share': settings.share_gradio,
            'show_error': True,
            'quiet': False,
            **kwargs
        }
        
        logger.info(f"Launching RAG app with smart model selection on port {launch_kwargs['server_port']}")
        interface.launch(**launch_kwargs)
   
 # ======= AGENT SYSTEM UI METHODS =======
    
    def get_agent_stats_markdown(self) -> str:
        """Genera markdown con estadísticas de agentes"""
        if not self.initialized:
            return "_Sistema no inicializado_"
        
        try:
            stats = self.rag_service.get_agent_stats()
            
            if not stats.get('agents_enabled'):
                return "_Sistema de agentes no habilitado_"
            
            md = "### 🤖 Sistema de Agentes\n\n"
            md += f"**Total de agentes:** {stats['total_agents']}\n"
            md += f"**Agentes activos:** {stats['active_agents']}\n"
            md += f"**Queries procesadas:** {stats['total_queries']}\n\n"
            
            md += "**Agentes disponibles:**\n"
            agents = self.rag_service.get_available_agents()
            for agent in agents:
                md += f"- **{agent['name']}**\n"
                md += f"  - Capacidades: {', '.join(agent['capabilities'])}\n"
                md += f"  - Queries: {agent['stats']['total_queries']}\n"
                md += f"  - Success rate: {agent['stats']['success_rate']:.1%}\n"
            
            return md
        except Exception as e:
            return f"_Error obteniendo estadísticas: {e}_"
    
    def toggle_agents_ui(self, enabled: bool) -> str:
        """Toggle del sistema de agentes desde la UI"""
        try:
            self.rag_service.toggle_agents(enabled)
            status = "habilitado" if enabled else "deshabilitado"
            return f"✅ Sistema de agentes {status}"
        except Exception as e:
            return f"❌ Error: {e}"


if __name__ == "__main__":
    app = GradioRAGApp()
    app.launch()
