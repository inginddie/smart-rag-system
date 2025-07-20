# -*- coding: utf-8 -*-
import gradio as gr
from typing import List, Tuple
from src.services.rag_service import RAGService
from src.utils.logger import setup_logger
from config.settings import settings

logger = setup_logger()

class GradioRAGApp:
    """Aplicación Gradio para el sistema RAG con selección inteligente de modelos y detección de intención académica"""
    
    def __init__(self):
        self.rag_service = RAGService()
        self.initialized = False
    
    def initialize_service(self) -> str:
        """Inicializa el servicio RAG"""
        try:
            if self.rag_service.initialize():
                self.initialized = True
                return "✅ Sistema RAG inicializado correctamente con detección de intención académica habilitada"
            else:
                return "⚠️ Sistema inicializado pero no se encontraron documentos para indexar"
        except Exception as e:
            logger.error(f"Error initializing service: {e}")
            return f"❌ Error al inicializar: {str(e)}"
    
    def _format_intent_info(self, intent_info: dict) -> str:
        """Formatea la información de intención para mostrar al usuario"""
        if not intent_info:
            return ""
        
        intent_type = intent_info.get('detected_intent', 'unknown')
        confidence = intent_info.get('confidence', 0)
        specialized_prompt = intent_info.get('specialized_prompt_used', False)
        processing_time = intent_info.get('processing_time_ms', 0)
        
        # Mapear tipos de intención a nombres amigables
        intent_names = {
            'definition': '📖 Definición Conceptual',
            'comparison': '⚖️ Análisis Comparativo', 
            'state_of_art': '🌟 Estado del Arte',
            'gap_analysis': '🔍 Análisis de Gaps',
            'unknown': '❓ Consulta General',
            'error': '⚠️ Error de Clasificación'
        }
        
        intent_name = intent_names.get(intent_type, f'❓ {intent_type}')
        
        # Crear mensaje informativo
        info_parts = [f"**Tipo de consulta detectada:** {intent_name}"]
        
        if confidence > 0:
            confidence_emoji = "🎯" if confidence >= 0.8 else "🎲" if confidence >= 0.6 else "❓"
            info_parts.append(f"**Confianza:** {confidence_emoji} {confidence:.0%}")
        
        if specialized_prompt and intent_type not in ['unknown', 'error']:
            info_parts.append("**Respuesta optimizada:** ✨ Usando template académico especializado")
        
        if processing_time > 0:
            info_parts.append(f"**Tiempo de análisis:** ⚡ {processing_time:.1f}ms")
        
        return "\n".join(info_parts)
    
    def _format_expansion_info(self, expansion_info: dict) -> str:
        """Formatea la información de expansión de consulta para mostrar al usuario"""
        if not expansion_info or expansion_info.get('expansion_count', 0) == 0:
            return ""
        
        expanded_terms = expansion_info.get('expanded_terms', [])
        processing_time = expansion_info.get('processing_time_ms', 0)
        
        info_parts = [f"**Términos expandidos:** 🔍 {', '.join(expanded_terms[:5])}"]
        
        if len(expanded_terms) > 5:
            info_parts.append(f"*... y {len(expanded_terms) - 5} términos más*")
        
        if processing_time > 0:
            info_parts.append(f"**Tiempo de expansión:** ⚡ {processing_time:.1f}ms")
        
        return "\n".join(info_parts)
        """Formatea la información del modelo para mostrar al usuario"""
        if not model_info:
            return ""
        
        model_name = model_info.get('selected_model', 'unknown')
        complexity_score = model_info.get('complexity_score', 0)
        
        # Mapear modelos a nombres amigables
        model_names = {
            'gpt-4o': '🧠 GPT-4o (Análisis Complejo)',
            'gpt-4o-mini': '⚡ GPT-4o-mini (Respuesta Rápida)',
            'gpt-3.5-turbo': '💨 GPT-3.5-turbo (Eficiente)'
        }
        
        model_display = model_names.get(model_name, f'🤖 {model_name}')
        
        info_parts = [f"**Modelo seleccionado:** {model_display}"]
        
        if complexity_score > 0:
            complexity_emoji = "🔥" if complexity_score >= 0.7 else "⚡" if complexity_score >= 0.4 else "💨"
            info_parts.append(f"**Complejidad detectada:** {complexity_emoji} {complexity_score:.0%}")
        
        return "\n".join(info_parts)
    
    def chat_response(self, message: str, history: List[Tuple[str, str]]) -> Tuple[str, str]:
        """
        Maneja las respuestas del chat con información enriquecida de intención y modelo
        
        Returns:
            Tuple[respuesta_principal, información_del_sistema]
        """
        if not self.initialized:
            return "❌ El sistema no está inicializado. Por favor inicialízalo primero.", ""
        
        if not message.strip():
            return "Por favor, escribe una pregunta.", ""
        
        try:
            # Obtener respuesta completa con metadata
            result = self.rag_service.query(message, include_sources=True)
            
            # Respuesta principal
            main_response = result['answer']
            
            # Información del sistema (intent + model + expansion)
            system_info_parts = []
            
            # Agregar información de intención si está disponible
            intent_info = result.get('intent_info', {})
            if intent_info:
                intent_details = self._format_intent_info(intent_info)
                if intent_details:
                    system_info_parts.append("### 🎯 Análisis de Consulta")
                    system_info_parts.append(intent_details)
            
            # Agregar información de expansión si está disponible
            expansion_info = result.get('expansion_info', {})
            if expansion_info:
                expansion_details = self._format_expansion_info(expansion_info)
                if expansion_details:
                    system_info_parts.append("### 🔍 Expansión de Consulta")
                    system_info_parts.append(expansion_details)
            
            # Agregar información del modelo si está disponible
            model_info = result.get('model_info', {})
            if model_info:
                model_details = self._format_model_info(model_info)
                if model_details:
                    system_info_parts.append("### 🤖 Selección de Modelo")
                    system_info_parts.append(model_details)
            
            # Agregar información de fuentes si está disponible
            sources = result.get('sources', [])
            if sources:
                system_info_parts.append("### 📚 Fuentes Consultadas")
                source_list = []
                for i, source in enumerate(sources[:3], 1):  # Mostrar máximo 3 fuentes
                    file_name = source.get('metadata', {}).get('file_name', 'Documento desconocido')
                    source_list.append(f"{i}. **{file_name}**")
                system_info_parts.append("\n".join(source_list))
                
                if len(sources) > 3:
                    system_info_parts.append(f"*... y {len(sources) - 3} fuentes adicionales*")
            
            # Combinar información del sistema
            system_info = "\n\n".join(system_info_parts) if system_info_parts else ""
            
            return main_response, system_info
            
        except Exception as e:
            logger.error(f"Error in chat response: {e}")
            error_msg = f"❌ Error al procesar la pregunta: {str(e)}"
            return error_msg, ""
    
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
        """Crea la interfaz de Gradio actualizada con intent feedback"""
        with gr.Blocks(
            title="Sistema RAG Avanzado - Investigación de Tesis",
            theme=gr.themes.Soft(),
            css="""
            .system-info {
                background-color: #f8f9fa !important;
                border: 1px solid #e9ecef !important;
                border-radius: 8px !important;
                padding: 12px !important;
                margin-top: 8px !important;
                font-size: 0.9em !important;
                color: #2c3e50 !important;
            }
            .system-info h3 {
                color: #34495e !important;
                font-weight: bold !important;
                margin-bottom: 8px !important;
            }
            .system-info p {
                color: #2c3e50 !important;
                margin-bottom: 4px !important;
            }
            .system-info strong {
                color: #2c3e50 !important;
                font-weight: bold !important;
            }
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
            /* Asegurar que el texto en el panel lateral sea visible */
            .gr-column .gr-markdown {
                color: #2c3e50 !important;
            }
            .gr-column .gr-markdown h3 {
                color: #34495e !important;
                font-weight: bold !important;
            }
            .gr-column .gr-markdown strong {
                color: #2c3e50 !important;
                font-weight: bold !important;
            }
            """
        ) as interface:
            
            gr.HTML("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1>🤖 Sistema RAG Avanzado para Investigación Académica</h1>
                <p>Especializado en IA para Historias de Usuario - Con Detección Inteligente de Intención</p>
                <p><small>El sistema detecta automáticamente el tipo de consulta y optimiza la respuesta accordingly</small></p>
            </div>
            """)
            
            with gr.Tabs():
                # Tab principal - Chat Académico
                with gr.TabItem("💬 Chat Académico Inteligente"):
                    gr.Markdown("### Asistente de Investigación con IA")
                    gr.Markdown("""
                    Haz preguntas académicas y observa cómo el sistema:
                    - 🎯 **Detecta automáticamente** el tipo de consulta (definición, comparación, estado del arte, gaps)
                    - 🔍 **Expande tu consulta** con sinónimos académicos relevantes  
                    - 🤖 **Selecciona el modelo apropiado** (GPT-4o para análisis complejos, GPT-4o-mini para consultas simples)  
                    - ✨ **Optimiza la respuesta** usando templates académicos especializados
                    """)
                    
                    with gr.Row():
                        with gr.Column(scale=2):
                            # Área principal de chat
                            chatbot = gr.Chatbot(
                                label="Conversación Académica",
                                height=500,
                                type='messages',
                                show_label=True
                            )
                            
                            with gr.Row():
                                msg = gr.Textbox(
                                    label="Tu pregunta de investigación",
                                    placeholder="Ej: Compare las metodologías de IA para historias de usuario...",
                                    scale=4,
                                    lines=2
                                )
                                send_btn = gr.Button("Enviar", variant="primary", scale=1)
                            
                            with gr.Row():
                                clear_btn = gr.Button("🗑️ Limpiar Chat", variant="secondary")
                        
                        with gr.Column(scale=1):
                            # Panel de información del sistema
                            system_info_display = gr.Markdown(
                                label="📊 Información del Sistema",
                                value="*Envía una consulta para ver cómo el sistema analiza tu pregunta*",
                                elem_classes=["system-info"],
                                visible=True
                            )
                    
                    # Ejemplos académicos específicos organizados por tipo de intención
                    with gr.Accordion("📋 Ejemplos por Tipo de Consulta", open=False):
                        gr.Markdown("""
                        **🔵 Definiciones Conceptuales:**
                        - "¿Qué es Natural Language Processing en requirements engineering?"
                        - "Define machine learning aplicado a historias de usuario"
                        - "Explica el concepto de automated requirements generation"
                        
                        **🟣 Análisis Comparativos:**
                        - "Compara supervised vs unsupervised learning para user stories"
                        - "Diferencias entre rule-based y ML approaches en requirements"
                        - "Ventajas y desventajas de BERT vs GPT para análisis de texto"
                        
                        **🟢 Estado del Arte:**
                        - "Estado del arte en IA para automatización de requirements"
                        - "Enfoques actuales en NLP para historias de usuario"
                        - "Tendencias recientes en AI-assisted software development"
                        
                        **🟠 Análisis de Gaps:**
                        - "¿Qué limitaciones tienen los métodos actuales de NLP para user stories?"
                        - "Gaps de investigación en automated requirements engineering"
                        - "¿Qué oportunidades existen para mejorar las técnicas actuales?"
                        """)

                    # FAQ dinámicas
                    faq_display = gr.Markdown(value=self.get_faq_markdown())
                    
                    def respond(message, chat_history):
                        if not message.strip():
                            return chat_history, "", self.get_faq_markdown(), ""
                        
                        # Obtener respuesta y información del sistema
                        bot_response, system_info = self.chat_response(message, chat_history)
                        
                        # Agregar al historial en formato correcto para Gradio
                        chat_history.append({"role": "user", "content": message})
                        chat_history.append({"role": "assistant", "content": bot_response})

                        return chat_history, "", self.get_faq_markdown(), system_info
                    
                    # Event handlers para el chat
                    send_btn.click(
                        respond,
                        inputs=[msg, chatbot],
                        outputs=[chatbot, msg, faq_display, system_info_display]
                    )
                    
                    msg.submit(
                        respond,
                        inputs=[msg, chatbot],
                        outputs=[chatbot, msg, faq_display, system_info_display]
                    )
                    
                    clear_btn.click(
                        lambda: ([], "", self.get_faq_markdown(), "*Envía una consulta para ver el análisis del sistema*"),
                        outputs=[chatbot, msg, faq_display, system_info_display]
                    )
                
                # Tab de administración
                with gr.TabItem("⚙️ Administración del Sistema"):
                    gr.Markdown("### Gestión del Sistema RAG Inteligente")
                    
                    with gr.Row():
                        init_btn = gr.Button("🚀 Inicializar Sistema", variant="primary")
                        reindex_btn = gr.Button("📚 Reindexar Documentos", variant="secondary")
                    
                    status_output = gr.Textbox(
                        label="Estado del Sistema",
                        interactive=False,
                        lines=3
                    )
                    
                    # Información del sistema
                    gr.Markdown("### Configuración del Sistema RAG Inteligente")
                    gr.Markdown(f"""
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
                    """)
                
                # Tab de guía académica actualizada
                with gr.TabItem("📚 Guía de Investigación Inteligente"):
                    gr.Markdown("""
                    ## 🎓 Sistema RAG Inteligente para Investigación Académica
                    
                    ### 🧠 Inteligencia Artificial Integrada
                    
                    Este sistema combina **dos niveles de IA** para optimizar tu experiencia de investigación:
                    
                    #### 🎯 **Nivel 1: Detección Automática de Intención**
                    El sistema analiza tu consulta en **menos de 200ms** para determinar qué tipo de respuesta necesitas:
                    
                    - **📖 Definición Conceptual** → Estructura la respuesta con definición formal, contexto histórico y aplicaciones
                    - **⚖️ Análisis Comparativo** → Organiza la información en tablas comparativas y análisis sistemático  
                    - **🌟 Estado del Arte** → Presenta cronología, tendencias actuales y consenso académico
                    - **🔍 Análisis de Gaps** → Identifica limitaciones, oportunidades y direcciones futuras
                    
                    #### 🤖 **Nivel 2: Selección Inteligente de Modelo**
                    Basado en la complejidad de tu consulta, elige automáticamente:
                    
                    - **🧠 GPT-4o** para análisis académicos complejos, comparaciones metodológicas y síntesis profundas
                    - **⚡ GPT-4o-mini** para definiciones claras, consultas directas y respuestas rápidas
                    
                    ### 🚀 Cómo Aprovechar al Máximo el Sistema
                    
                    #### **Para Investigación de Tesis sobre IA y User Stories:**
                    
                    **🔍 Exploración Inicial:**
                    1. "Estado del arte en IA para historias de usuario" (activará análisis cronológico)
                    2. "¿Qué es automated requirements generation?" (activará definición estructurada)
                    
                    **📊 Análisis Comparativo:**
                    1. "Compara NLP vs Machine Learning para requirements analysis"
                    2. "Ventajas y desventajas de rule-based vs deep learning approaches"
                    
                    **🎯 Identificación de Oportunidades:**
                    1. "¿Qué limitaciones tienen las técnicas actuales de NLP para user stories?"
                    2. "Gaps de investigación en automated requirements engineering"
                    
                    ### 💡 Indicadores Visuales del Sistema
                    
                    Observa el **panel lateral** durante tus consultas para ver:
                    
                    - **🎯 Tipo de consulta detectada** con nivel de confianza
                    - **🤖 Modelo seleccionado** y razón de la selección  
                    - **✨ Optimización aplicada** (si usa template especializado)
                    - **📚 Fuentes consultadas** para tu respuesta específica
                    
                    ### 🎓 Resultados de Investigación Optimizados
                    
                    **Para Definiciones:**
                    - Estructura académica formal con contexto histórico
                    - Referencias a autores principales y papers fundamentales
                    - Conexiones con conceptos relacionados
                    
                    **Para Comparaciones:**
                    - Matrices comparativas sistemáticas
                    - Análisis de ventajas/desventajas equilibrado
                    - Recomendaciones basadas en contexto de uso
                    
                    **Para Estado del Arte:**
                    - Evolución temporal de enfoques
                    - Identificación de tendencias emergentes  
                    - Análisis de consenso vs controversias
                    
                    **Para Análisis de Gaps:**
                    - Categorización de limitaciones por tipo
                    - Oportunidades específicas de investigación
                    - Conexión con trabajos futuros sugeridos
                    
                    ### 🔬 Optimización para tu Dominio Específico
                    
                    El sistema está **pre-optimizado** para investigación en:
                    - ✅ Inteligencia Artificial aplicada a Software Engineering
                    - ✅ Natural Language Processing para Requirements  
                    - ✅ Machine Learning en User Story Analysis
                    - ✅ Automated Software Development Tools
                    - ✅ AI-Assisted Development Methodologies
                    
                    ### 📈 Consejos para Consultas de Alta Calidad
                    
                    **🎯 Sé específico en tu intención:**
                    - ❌ "machine learning" 
                    - ✅ "¿Qué técnicas de machine learning se usan para analizar historias de usuario?"
                    
                    **🔗 Conecta conceptos:**
                    - ❌ "NLP tools"
                    - ✅ "Compare herramientas de NLP para extracción automática de requirements"
                    
                    **📊 Solicita análisis estructurado:**
                    - ❌ "research gaps"
                    - ✅ "¿Qué limitaciones identifican los estudios actuales en automated user story generation?"
                    
                    ### 🚀 El Futuro de tu Investigación
                    
                    Con este sistema inteligente, puedes:
                    - **⚡ Acelerar** tu revisión de literatura 5-10x
                    - **🎯 Identificar** gaps de investigación automáticamente  
                    - **📊 Comparar** metodologías de manera sistemática
                    - **🔍 Descubrir** conexiones entre diferentes líneas de investigación
                    - **📈 Optimizar** la calidad académica de tu análisis
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
        
        logger.info(f"Launching RAG app with intelligent intent detection and model selection on port {launch_kwargs['server_port']}")
        interface.launch(**launch_kwargs)