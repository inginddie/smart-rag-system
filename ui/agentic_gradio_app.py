# -*- coding: utf-8 -*-
"""
Extensión de GradioRAGApp para mostrar capacidades agentic.
Mantiene compatibilidad completa con interfaz existente.
"""

import gradio as gr
from typing import List, Tuple
from src.services.agentic_rag_service import AgenticRAGService, create_rag_service
from src.utils.logger import setup_logger
from config.settings import settings

logger = setup_logger()

class AgenticGradioApp:
    """
    Aplicación Gradio extendida con capacidades agentic.
    Mantiene toda la funcionalidad existente.
    """
    
    def __init__(self, enable_agentic: bool = True):
        # Usar factory para crear servicio apropiado
        self.rag_service = create_rag_service(agentic=enable_agentic)
        self.is_agentic = isinstance(self.rag_service, AgenticRAGService)
        self.initialized = False
        
        logger.info(f"AgenticGradioApp created (agentic: {self.is_agentic})")
    
    def initialize_service(self) -> str:
        """Inicializa el servicio RAG con capacidades agentic"""
        try:
            if self.rag_service.initialize():
                self.initialized = True
                
                if self.is_agentic:
                    status = "✅ Sistema RAG Agentic inicializado correctamente"
                    
                    # Obtener estadísticas de agentes
                    agent_stats = self.rag_service.get_agent_stats()
                    if agent_stats["agentic_mode"]:
                        status += f"\n🤖 Agentes disponibles: {agent_stats['agents_count']}"
                        status += f"\n🧠 Memoria distribuida: {'Activa' if agent_stats.get('memory_stats', {}).get('redis_available') else 'Local'}"
                    else:
                        status += "\n⚠️ Modo clásico activo (agentes no disponibles)"
                else:
                    status = "✅ Sistema RAG clásico inicializado correctamente"
                    
                return status
            else:
                return "⚠️ Sistema inicializado pero no se encontraron documentos para indexar"
                
        except Exception as e:
            logger.error(f"Error initializing service: {e}")
            return f"❌ Error al inicializar: {str(e)}"
    
    def chat_response(self, message: str, history: List[Tuple[str, str]]) -> str:
        """Maneja respuestas con capacidades agentic"""
        if not self.initialized:
            return "❌ El sistema no está inicializado. Por favor inicialízalo primero."
        
        if not message.strip():
            return "Por favor, escribe una pregunta."
        
        try:
            # Usar método agentic si está disponible
            if self.is_agentic and hasattr(self.rag_service, 'query_agentic'):
                import asyncio
                try:
                    # Intentar consulta agentic async
                    result = asyncio.run(
                        self.rag_service.query_agentic(message, session_id="gradio_session")
                    )
                except:
                    # Fallback a método clásico
                    result = self.rag_service.query(message)
            else:
                # Método clásico
                result = self.rag_service.query(message)
            
            response = result['answer']
            
            # Agregar información de agente si está disponible
            if self.is_agentic and 'agent_info' in result:
                agent_info = result['agent_info']
                if settings.log_level == "DEBUG":
                    response += f"\n\n*[Procesado por {agent_info.get('agent_name', 'RAG clásico')}"
                    if 'confidence' in agent_info:
                        response += f", confianza: {agent_info['confidence']:.2f}"
                    response += "]*"
            
            # Información de modelo (preservada de versión original)
            model_info = result.get('model_info', {})
            if model_info and model_info.get('selected_model') and settings.log_level == "DEBUG":
                model_name = model_info.get('selected_model', 'unknown')
                complexity = model_info.get('complexity_score', 0)
                response += f"\n\n*[Modelo: {model_name}, complejidad: {complexity:.2f}]*"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat response: {e}")
            return f"❌ Error al procesar la pregunta: {str(e)}"
    
    def reindex_documents(self) -> str:
        """Reindexar documentos (método preservado)"""
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
        """Genera texto Markdown de preguntas frecuentes (preservado)"""
        if hasattr(self.rag_service, 'get_frequent_questions'):
            faqs = self.rag_service.get_frequent_questions()
            if not faqs:
                return "_No hay preguntas frecuentes registradas aún._"
            lines = "\n".join(f"- {q}" for q in faqs)
            return f"**Preguntas frecuentes:**\n{lines}"
        return "_Funcionalidad no disponible._"
    
    def get_system_status(self) -> str:
        """Obtiene estado detallado del sistema (nueva funcionalidad)"""
        try:
            status = self.rag_service.get_status()
            
            status_text = "### 📊 Estado del Sistema\n\n"
            
            # Estado básico
            if status.get('initialized'):
                status_text += "✅ **Sistema**: Inicializado\n"
            else:
                status_text += "❌ **Sistema**: No inicializado\n"
            
            status_text += f"📁 **Documentos**: {status.get('document_count', 0)} indexados\n"
            
            # Estado agentic si está disponible
            if self.is_agentic:
                agentic_mode = status.get('agentic_mode', False)
                status_text += f"🤖 **Modo Agentic**: {'Activo' if agentic_mode else 'Inactivo'}\n"
                
                agents = status.get('agents_available', [])
                if agents:
                    status_text += f"👥 **Agentes**: {', '.join(agents)}\n"
                
                # Métricas agentic
                metrics = status.get('agentic_metrics', {})
                if metrics:
                    status_text += "\n**📈 Métricas Agentic:**\n"
                    status_text += f"- Consultas procesadas por agentes: {metrics.get('agent_queries', 0)}\n"
                    status_text += f"- Fallbacks a RAG clásico: {metrics.get('fallback_to_classic', 0)}\n"
            
            # Configuración de modelos
            status_text += "\n**🔧 Configuración:**\n"
            status_text += f"- Modelo complejo: {settings.complex_model}\n"
            status_text += f"- Modelo simple: {settings.simple_model}\n"
            status_text += f"- Selección inteligente: {'Activa' if settings.enable_smart_selection else 'Inactiva'}\n"
            
            return status_text
            
        except Exception as e:
            return f"❌ Error obteniendo estado: {str(e)}"
    
    def toggle_agentic_mode(self) -> str:
        """Activa/desactiva modo agentic (nueva funcionalidad)"""
        if not self.is_agentic:
            return "⚠️ Servicio no soporta modo agentic"
        
        try:
            current_status = self.rag_service.get_status().get('agentic_mode', False)
            
            if current_status:
                self.rag_service.disable_agentic_mode()
                return "✅ Modo agentic desactivado - usando RAG clásico"
            else:
                self.rag_service.enable_agentic_mode()
                new_status = self.rag_service.get_status().get('agentic_mode', False)
                if new_status:
                    return "✅ Modo agentic activado"
                else:
                    return "❌ No se pudo activar modo agentic - verificar inicialización"
                    
        except Exception as e:
            return f"❌ Error cambiando modo: {str(e)}"
    
    def create_interface(self) -> gr.Blocks:
        """Crea la interfaz extendida con capacidades agentic"""
        with gr.Blocks(
            title="Sistema RAG Agentic - Investigación de Tesis",
            theme=gr.themes.Soft(),
        ) as interface:
            
            gr.HTML(f"""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1>🤖 Sistema RAG Agentic para Investigación</h1>
                <p>Especializado en IA para Historias de Usuario - {'Con Agentes Especializados' if self.is_agentic else 'Modo Clásico'}</p>
                <p><small>{'Usa agentes especializados para análisis académico avanzado' if self.is_agentic else 'Usa selección inteligente de modelos GPT-4o/4o-mini'}</small></p>
            </div>
            """)
            
            with gr.Tabs():
                # Tab principal - Chat (preservado y mejorado)
                with gr.TabItem("💬 Chat Académico"):
                    gr.Markdown("### Asistente de Investigación Agentic" if self.is_agentic else "### Asistente de Investigación")
                    if self.is_agentic:
                        gr.Markdown("El sistema seleccionará automáticamente el agente más apropiado para tu consulta académica.")
                    else:
                        gr.Markdown("Haz preguntas académicas sobre tus documentos. El sistema seleccionará automáticamente el modelo más apropiado.")
                    
                    # ChatInterface (preservado)
                    chatbot = gr.Chatbot(
                        label="Conversación Académica",
                        height=400,
                        type='messages'
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
                    
                    # Ejemplos académicos (preservados)
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
                    
                    # Event handlers para el chat (preservados)
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
                
                # Tab de administración (extendido)
                with gr.TabItem("⚙️ Administración"):
                    gr.Markdown("### Gestión del Sistema RAG Agentic" if self.is_agentic else "### Gestión del Sistema RAG")
                    
                    with gr.Row():
                        init_btn = gr.Button("🚀 Inicializar Sistema", variant="primary")
                        reindex_btn = gr.Button("📚 Reindexar Documentos", variant="secondary")
                        
                        # Controles agentic adicionales
                        if self.is_agentic:
                            toggle_btn = gr.Button("🔄 Cambiar Modo", variant="secondary")
                    
                    status_output = gr.Textbox(
                        label="Estado del Sistema",
                        interactive=False,
                        lines=3
                    )
                    
                    # Estado detallado del sistema (nuevo)
                    with gr.Row():
                        status_btn = gr.Button("📊 Ver Estado Detallado", variant="secondary")
                    
                    detailed_status = gr.Markdown(value="Presiona 'Ver Estado Detallado' para más información.")
                    
                    # Configuración del sistema (preservada y extendida)
                    gr.Markdown("### Configuración Actual")
                    
                    config_text = f"""
                    **Selección Inteligente de Modelos:**
                    - 🧠 **Modelo para consultas complejas**: `{settings.complex_model}`
                    - ⚡ **Modelo para consultas simples**: `{settings.simple_model}`
                    - 🎯 **Umbral de complejidad**: `{settings.complexity_threshold}`
                    - 🔄 **Selección automática**: `{'Activada' if settings.enable_smart_selection else 'Desactivada'}`
                    """
                    
                    if self.is_agentic:
                        config_text += """
                    
                    **Capacidades Agentic:**
                    - 🤖 **Agentes especializados**: DocumentSearchAgent
                    - 🧠 **Memoria distribuida**: Redis + ChromaDB
                    - 🔄 **Selección automática de agentes**: Activa
                    - 📊 **Métricas de agentes**: Disponibles
                        """
                    
                    config_text += f"""
                    
                    **Configuración RAG:**
                    - 📁 **Directorio de documentos**: `{settings.documents_path}`
                    - 🗃️ **Base de datos vectorial**: `{settings.vector_db_path}`
                    - 🔤 **Modelo de embeddings**: `{settings.embedding_model}`
                    - 📊 **Tamaño de chunk**: `{settings.chunk_size}`
                    - 🔗 **Overlap de chunk**: `{settings.chunk_overlap}`
                    - 📖 **Documentos por consulta**: `{settings.max_documents}`
                    """
                    
                    gr.Markdown(config_text)
                
                # Tab de ayuda académica (preservado y extendido)
                with gr.TabItem("📚 Guía de Investigación"):
                    if self.is_agentic:
                        gr.Markdown("""
                        ## 🎓 Sistema RAG Agentic para Investigación de Tesis
                        
                        ### 🤖 Agentes Especializados
                        
                        El sistema utiliza **agentes inteligentes especializados**:
                        
                        **DocumentSearchAgent** se activa automáticamente para:
                        - 🔬 **Análisis académico profundo**: "analiza metodología", "compara enfoques"
                        - 📊 **Búsqueda especializada**: "encuentra papers sobre", "literatura en"
                        - 🎯 **Extracción de información**: "qué técnicas", "cuáles son las métricas"
                        - 📝 **Síntesis académica**: "resume el estado del arte", "gaps de investigación"
                        
                        ### 🧠 Memoria Inteligente
                        
                        Los agentes mantienen **memoria de conversación**:
                        - 💭 **Contexto de sesión**: Recuerdan consultas anteriores
                        - 🔗 **Conexiones semánticas**: Relacionan preguntas con respuestas pasadas
                        - 📚 **Memoria académica**: Almacenan hallazgos importantes
                        
                        ### 🚀 Estrategias de Búsqueda Avanzadas
                        
                        El sistema selecciona automáticamente la mejor estrategia:
                        
                        #### **Búsqueda Académica** (para análisis profundo)
                        - "Analiza el estado del arte en IA para historias de usuario"
                        - "¿Cuáles son las metodologías principales en la literatura?"
                        - "Sintetiza los enfoques de NLP en requirements engineering"
                        
                        #### **Búsqueda por Metadatos** (para filtros específicos)
                        - "Papers del autor Smith en 2020"
                        - "Estudios publicados después de 2018"
                        - "Artículos de la conferencia ICSE"
                        
                        #### **Búsqueda por Palabras Clave** (para términos exactos)
                        - 'Buscar "machine learning" exacto'
                        - "Documentos que mencionen 'user story generation'"
                        - "Papers con 'natural language processing'"
                        
                        #### **Búsqueda Semántica** (por defecto)
                        - "Técnicas de automatización de requirements"
                        - "Mejoras en el desarrollo ágil"
                        - "Aplicaciones de IA en software engineering"
                        """)
                    else:
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
                        """)
                    
                    gr.Markdown("""
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
            
            # Event handlers (preservados y extendidos)
            init_btn.click(
                fn=self.initialize_service,
                outputs=status_output
            )
            
            reindex_btn.click(
                fn=self.reindex_documents,
                outputs=status_output
            )
            
            status_btn.click(
                fn=self.get_system_status,
                outputs=detailed_status
            )
            
            # Event handler adicional para modo agentic
            if self.is_agentic:
                toggle_btn.click(
                    fn=self.toggle_agentic_mode,
                    outputs=status_output
                )
        
        return interface
    
    def launch(self, **kwargs):
        """Lanza la aplicación (método preservado)"""
        interface = self.create_interface()
        
        # Configuración por defecto
        launch_kwargs = {
            'server_port': settings.server_port,
            'share': settings.share_gradio,
            'show_error': True,
            'quiet': False,
            **kwargs
        }
        
        mode_text = "agentic" if self.is_agentic else "classic"
        logger.info(f"Launching RAG app in {mode_text} mode on port {launch_kwargs['server_port']}")
        interface.launch(**launch_kwargs)

# Función de compatibilidad para migración gradual
class GradioRAGApp(AgenticGradioApp):
    """
    Alias para mantener compatibilidad con código existente.
    Automáticamente usa capacidades agentic si están disponibles.
    """
    
    def __init__(self):
        super().__init__(enable_agentic=True)
        logger.info("GradioRAGApp initialized with agentic capabilities")