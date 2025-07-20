# -*- coding: utf-8 -*-
import gradio as gr
from gradio.themes.soft import Soft
from typing import List, Tuple
from src.services.rag_service import RAGService
from src.utils.logger import setup_logger
from config.settings import settings

logger = setup_logger()

class GradioRAGApp:
    """
    Aplicación Gradio para el sistema RAG con funcionalidades avanzadas:
    - Detección inteligente de intención académica
    - Expansión automática de consultas
    - Selección dinámica de modelos
    - Feedback visual completo para transparencia del sistema
    """
    
    def __init__(self):
        """
        Inicializa la aplicación con el servicio RAG.
        
        Aquí establecemos la conexión con el motor principal del sistema RAG,
        pero mantenemos el estado de inicialización separado para permitir
        una configuración step-by-step del sistema desde la interfaz.
        """
        self.rag_service = RAGService()
        self.initialized = False
    
    def initialize_service(self) -> str:
        """
        Inicializa el servicio RAG y proporciona feedback detallado al usuario.
        
        Este método es crucial porque valida que todos los componentes del sistema
        estén funcionando correctamente antes de permitir consultas. Es como hacer
        un "health check" completo del sistema.
        """
        try:
            if self.rag_service.initialize():
                self.initialized = True
                return "✅ Sistema RAG inicializado correctamente con todas las funcionalidades avanzadas habilitadas:\n" + \
                       "🎯 Detección de intención académica\n" + \
                       "🔍 Expansión automática de consultas\n" + \
                       "🤖 Selección inteligente de modelos\n" + \
                       "📚 Base de documentos indexada y lista"
            else:
                return "⚠️ Sistema inicializado pero no se encontraron documentos para indexar"
        except Exception as e:
            logger.error(f"Error initializing service: {e}")
            return f"❌ Error al inicializar: {str(e)}"
    
    def _format_intent_info(self, intent_info: dict) -> str:
        """
        Formatea la información de detección de intención para presentación al usuario.
        
        Esta función es esencial para la transparencia del sistema. Cuando un investigador
        hace una pregunta, necesita entender cómo el sistema interpretó su consulta para
        poder evaluar la relevancia de la respuesta y, si es necesario, reformular
        su pregunta de manera más específica.
        """
        if not intent_info:
            return ""
        
        intent_type = intent_info.get('detected_intent', 'unknown')
        confidence = intent_info.get('confidence', 0)
        specialized_prompt = intent_info.get('specialized_prompt_used', False)
        processing_time = intent_info.get('processing_time_ms', 0)
        
        # Mapear tipos de intención a nombres comprensibles para el usuario
        # Estos nombres están diseñados para que investigadores sin conocimiento técnico
        # puedan entender inmediatamente qué tipo de respuesta pueden esperar
        intent_names = {
            'definition': '📖 Definición Conceptual',
            'comparison': '⚖️ Análisis Comparativo', 
            'state_of_art': '🌟 Estado del Arte',
            'gap_analysis': '🔍 Análisis de Gaps',
            'unknown': '❓ Consulta General',
            'error': '⚠️ Error de Clasificación'
        }
        
        intent_name = intent_names.get(intent_type, f'❓ {intent_type}')
        
        # Construir mensaje informativo con diferentes niveles de detalle
        info_parts = [f"**Tipo de consulta detectada:** {intent_name}"]
        
        if confidence > 0:
            # Los emojis ayudan a transmitir rápidamente el nivel de confianza
            confidence_emoji = "🎯" if confidence >= 0.8 else "🎲" if confidence >= 0.6 else "❓"
            info_parts.append(f"**Confianza:** {confidence_emoji} {confidence:.0%}")
        
        if specialized_prompt and intent_type not in ['unknown', 'error']:
            info_parts.append("**Respuesta optimizada:** ✨ Usando template académico especializado")
        
        if processing_time > 0:
            info_parts.append(f"**Tiempo de análisis:** ⚡ {processing_time:.1f}ms")
        
        return "\n".join(info_parts)
    
    def _format_expansion_info(self, expansion_info: dict) -> str:
        """
        Formatea la información de expansión de consulta para mostrar al usuario.
        
        La expansión de consultas puede ser un concepto abstracto para muchos usuarios.
        Esta función hace visible ese proceso, mostrando exactamente qué términos
        adicionales está usando el sistema para buscar información relevante.
        Esto ayuda a los investigadores a entender por qué ciertos documentos
        aparecieron en los resultados incluso si no contenían exactamente sus términos originales.
        """
        if not expansion_info or expansion_info.get('expansion_count', 0) == 0:
            return ""
        
        expanded_terms = expansion_info.get('expanded_terms', [])
        processing_time = expansion_info.get('processing_time_ms', 0)
        strategy_used = expansion_info.get('strategy_used', 'unknown')
        
        info_parts = [f"**Términos expandidos:** 🔍 {', '.join(expanded_terms[:5])}"]
        
        if len(expanded_terms) > 5:
            info_parts.append(f"*... y {len(expanded_terms) - 5} términos más*")
        
        if strategy_used != 'unknown':
            strategy_names = {
                'conservative': 'Conservadora',
                'moderate': 'Moderada', 
                'comprehensive': 'Comprehensiva'
            }
            strategy_display = strategy_names.get(strategy_used, strategy_used)
            info_parts.append(f"**Estrategia:** 📊 {strategy_display}")
        
        if processing_time > 0:
            info_parts.append(f"**Tiempo de expansión:** ⚡ {processing_time:.1f}ms")
        
        return "\n".join(info_parts)
    
    def _format_model_info(self, model_info: dict) -> str:
        """
        Formatea la información del modelo seleccionado para mostrar al usuario.
        
        La selección automática de modelos es una de las características más sofisticadas
        del sistema. Esta función hace transparente esa decisión, permitiendo que los
        usuarios entiendan por qué el sistema eligió un modelo particular para su consulta.
        Esto es especialmente importante en contextos académicos donde la reproducibilidad
        y la comprensión del proceso son fundamentales.
        """
        if not model_info:
            return ""
        
        model_name = model_info.get('selected_model', 'unknown')
        complexity_score = model_info.get('complexity_score', 0)
        reasoning = model_info.get('reasoning', '')
        
        # Mapear modelos técnicos a nombres que los usuarios puedan entender fácilmente
        # Incluimos información sobre las fortalezas de cada modelo
        model_names = {
            'gpt-4o': '🧠 GPT-4o (Análisis Académico Profundo)',
            'gpt-4o-mini': '⚡ GPT-4o-mini (Respuesta Rápida y Eficiente)',
            'gpt-3.5-turbo': '💨 GPT-3.5-turbo (Consultas Directas)'
        }
        
        model_display = model_names.get(model_name, f'🤖 {model_name}')
        
        info_parts = [f"**Modelo seleccionado:** {model_display}"]
        
        if complexity_score > 0:
            # Visual indicators para el nivel de complejidad detectado
            complexity_emoji = "🔥" if complexity_score >= 0.7 else "⚡" if complexity_score >= 0.4 else "💨"
            info_parts.append(f"**Complejidad detectada:** {complexity_emoji} {complexity_score:.0%}")
        
        # Agregar reasoning si está disponible y es informativo
        if reasoning and len(reasoning) < 100:  # Solo mostrar si es conciso
            info_parts.append(f"**Razón:** {reasoning}")
        
        return "\n".join(info_parts)
    
    def chat_response(self, message: str, history: List[Tuple[str, str]]) -> Tuple[str, str]:
        """
        Procesa las consultas del usuario y genera respuestas con información enriquecida.
        
        Esta es la función central que orquesta todo el pipeline RAG avanzado:
        1. Valida el estado del sistema
        2. Procesa la consulta a través del pipeline completo
        3. Extrae y formatea toda la metadata del proceso
        4. Presenta tanto la respuesta como la información del sistema
        
        El retorno de una tupla permite separar la respuesta principal (que es lo que
        el usuario busca) de la información del sistema (que proporciona transparencia
        sobre cómo se generó esa respuesta).
        """
        if not self.initialized:
            return "❌ El sistema no está inicializado. Por favor inicialízalo primero.", ""
        
        if not message.strip():
            return "Por favor, escribe una pregunta académica.", ""
        
        try:
            # Obtener respuesta completa con toda la metadata del pipeline
            result = self.rag_service.query(message, include_sources=True)
            
            # La respuesta principal es lo que el usuario realmente quiere leer
            main_response = result['answer']
            
            # Construir información del sistema de manera modular
            # Cada sección proporciona transparencia sobre una parte diferente del proceso
            system_info_parts = []
            
            # Sección 1: Análisis de la consulta (detección de intención)
            intent_info = result.get('intent_info', {})
            if intent_info:
                intent_details = self._format_intent_info(intent_info)
                if intent_details:
                    system_info_parts.append("### 🎯 Análisis de Consulta")
                    system_info_parts.append(intent_details)
            
            # Sección 2: Expansión de consulta (términos adicionales utilizados)
            expansion_info = result.get('expansion_info', {})
            if expansion_info and expansion_info.get('expansion_count', 0) > 0:
                expansion_details = self._format_expansion_info(expansion_info)
                if expansion_details:
                    system_info_parts.append("### 🔍 Expansión de Consulta")
                    system_info_parts.append(expansion_details)
            
            # Sección 3: Selección de modelo (por qué se eligió este modelo)
            model_info = result.get('model_info', {})
            if model_info:
                model_details = self._format_model_info(model_info)
                if model_details:
                    system_info_parts.append("### 🤖 Selección de Modelo")
                    system_info_parts.append(model_details)
            
            # Sección 4: Fuentes consultadas (transparencia sobre los documentos utilizados)
            sources = result.get('sources', [])
            if sources:
                system_info_parts.append("### 📚 Fuentes Consultadas")
                source_list = []
                for i, source in enumerate(sources[:3], 1):  # Mostrar máximo 3 fuentes principales
                    file_name = source.get('metadata', {}).get('file_name', 'Documento desconocido')
                    source_list.append(f"{i}. **{file_name}**")
                system_info_parts.append("\n".join(source_list))
                
                if len(sources) > 3:
                    system_info_parts.append(f"*... y {len(sources) - 3} fuentes adicionales*")
            
            # Combinar toda la información del sistema en un panel cohesivo
            system_info = "\n\n".join(system_info_parts) if system_info_parts else ""
            
            return main_response, system_info
            
        except Exception as e:
            logger.error(f"Error in chat response: {e}")
            error_msg = f"❌ Error al procesar la pregunta: {str(e)}"
            return error_msg, ""
    
    def reindex_documents(self) -> str:
        """
        Reindexar documentos cuando se agregan nuevos archivos o se quiere refrescar la base.
        
        Esta operación es costosa en términos de tiempo y recursos, por lo que incluimos
        advertencias claras y feedback detallado sobre el proceso.
        """
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
        """
        Genera contenido dinámico de preguntas frecuentes basado en el uso real del sistema.
        
        Esta función es un ejemplo de cómo el sistema aprende de sus usuarios.
        Las preguntas más frecuentes se pueden usar para mejorar la documentación,
        identificar patrones de uso, y optimizar las respuestas del sistema.
        """
        faqs = self.rag_service.get_frequent_questions()
        if not faqs:
            return "_No hay preguntas frecuentes registradas aún._"
        lines = "\n".join(f"- {q}" for q in faqs)
        return f"**Preguntas frecuentes:**\n{lines}"
    
    def create_interface(self) -> gr.Blocks:
        """
        Crea la interfaz de usuario completa con todas las funcionalidades integradas.
        
        Esta función construye la interfaz que expone todas las capacidades del sistema
        de manera intuitiva. El diseño está pensado para investigadores académicos
        que necesitan tanto poder como facilidad de uso.
        """
        with gr.Blocks(
            theme=Soft(),
            css="""
            /* Estilos personalizados para mejorar la experiencia visual */
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
            /* Asegurar legibilidad en el panel lateral */
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
            
            # Header principal con branding y descripción del sistema
            gr.HTML("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1>🤖 Sistema RAG Avanzado para Investigación Académica</h1>
                <p>Especializado en IA para Historias de Usuario - Con Inteligencia Artificial Multicapa</p>
                <p><small>
                    🎯 Detección automática de intención &nbsp;•&nbsp; 
                    🔍 Expansión inteligente de consultas &nbsp;•&nbsp; 
                    🤖 Selección dinámica de modelos &nbsp;•&nbsp; 
                    📊 Transparencia completa del proceso
                </small></p>
            </div>
            """)
            
            with gr.Tabs():
                # Tab principal - Chat Académico Inteligente
                with gr.TabItem("💬 Chat Académico Inteligente"):
                    gr.Markdown("### Asistente de Investigación con IA Multicapa")
                    gr.Markdown("""
                    Haz preguntas académicas y observa cómo el sistema combina múltiples técnicas de IA:
                    - 🎯 **Detecta automáticamente** el tipo de consulta (definición, comparación, estado del arte, gaps)
                    - 🔍 **Expande tu consulta** con sinónimos académicos y términos relacionados relevantes  
                    - 🤖 **Selecciona el modelo apropiado** (GPT-4o para análisis complejos, GPT-4o-mini para consultas simples)  
                    - ✨ **Optimiza la respuesta** usando templates académicos especializados por tipo de intención
                    - 📊 **Muestra todo el proceso** para transparencia y reproducibilidad académica
                    """)
                    
                    with gr.Row():
                        with gr.Column(scale=2):
                            # Área principal de conversación
                            chatbot = gr.Chatbot(
                                label="Conversación Académica Inteligente",
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
                            # Panel de información del sistema - la clave de la transparencia
                            system_info_display = gr.Markdown(
                                label="📊 Información del Sistema",
                                value="*Envía una consulta para ver cómo el sistema analiza tu pregunta con IA multicapa*",
                                elem_classes=["system-info"],
                                visible=True
                            )
                    
                    # Ejemplos académicos organizados por tipo para educar al usuario
                    with gr.Accordion("📋 Ejemplos por Tipo de Consulta", open=False):
                        gr.Markdown("""
                        **🔵 Definiciones Conceptuales (Activará template especializado en definiciones):**
                        - "¿Qué es Natural Language Processing en requirements engineering?"
                        - "Define machine learning aplicado a historias de usuario"
                        - "Explica el concepto de automated requirements generation"
                        
                        **🟣 Análisis Comparativos (Activará template de comparación sistemática):**
                        - "Compara supervised vs unsupervised learning para user stories"
                        - "Diferencias entre rule-based y ML approaches en requirements"
                        - "Ventajas y desventajas de BERT vs GPT para análisis de texto"
                        
                        **🟢 Estado del Arte (Activará template de síntesis temporal):**
                        - "Estado del arte en IA para automatización de requirements"
                        - "Enfoques actuales en NLP para historias de usuario"
                        - "Tendencias recientes en AI-assisted software development"
                        
                        **🟠 Análisis de Gaps (Activará template de identificación de oportunidades):**
                        - "¿Qué limitaciones tienen los métodos actuales de NLP para user stories?"
                        - "Gaps de investigación en automated requirements engineering"
                        - "¿Qué oportunidades existen para mejorar las técnicas actuales?"
                        """)

                    # FAQ dinámicas - aprendizaje del sistema
                    faq_display = gr.Markdown(value=self.get_faq_markdown())
                    
                    def respond(message, chat_history):
                        """
                        Handler principal para las respuestas del chat.
                        
                        Esta función coordina todo el proceso de respuesta y actualiza
                        tanto el historial de chat como la información del sistema.
                        """
                        if not message.strip():
                            return chat_history, "", self.get_faq_markdown(), ""
                        
                        # Procesar la consulta a través del pipeline completo
                        bot_response, system_info = self.chat_response(message, chat_history)
                        
                        # Actualizar historial en formato compatible con Gradio
                        chat_history.append({"role": "user", "content": message})
                        chat_history.append({"role": "assistant", "content": bot_response})

                        return chat_history, "", self.get_faq_markdown(), system_info
                    
                    # Event handlers para interacción del usuario
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
                        lambda: ([], "", self.get_faq_markdown(), "*Envía una consulta para ver el análisis multicapa del sistema*"),
                        outputs=[chatbot, msg, faq_display, system_info_display]
                    )
                
                # Tab de administración del sistema
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
                    
                    # Información detallada de configuración para transparency técnica
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
                
                # Tab de guía académica - educación del usuario
                with gr.TabItem("📚 Guía de Investigación Inteligente"):
                    gr.Markdown("""
                    ## 🎓 Sistema RAG Inteligente para Investigación Académica
                    
                    ### 🧠 Inteligencia Artificial Multicapa
                    
                    Este sistema combina **cuatro niveles de IA** para optimizar tu experiencia de investigación:
                    
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
                    
                    ### 🚀 Cómo Aprovechar al Máximo el Sistema
                    
                    #### **Para Investigación de Tesis sobre IA y User Stories:**
                    
                    **🔍 Exploración Inicial:**
                    1. "Estado del arte en IA para historias de usuario" (activará análisis cronológico con expansión temporal)
                    2. "¿Qué es automated requirements generation?" (activará definición estructurada con sinónimos técnicos)
                    
                    **📊 Análisis Comparativo:**
                    1. "Compara NLP vs Machine Learning para requirements analysis" (expandirá con variaciones metodológicas)
                    2. "Ventajas y desventajas de rule-based vs deep learning approaches" (incluirá términos contrastivos)
                    
                    **🎯 Identificación de Oportunidades:**
                    1. "¿Qué limitaciones tienen las técnicas actuales de NLP para user stories?" (expandirá con términos de gap analysis)
                    2. "Gaps de investigación en automated requirements engineering" (incluirá sinónimos de limitaciones)
                    
                    ### 💡 Indicadores Visuales del Sistema
                    
                    Observa el **panel lateral** durante tus consultas para ver:
                    
                    - **🎯 Tipo de consulta detectada** con nivel de confianza y reasoning
- **🔍 Términos expandidos** agregados automáticamente con estrategia utilizada
                   - **🤖 Modelo seleccionado** y razón de la selección basada en complejidad  
                   - **✨ Optimización aplicada** (si usa template especializado)
                   - **📚 Fuentes consultadas** para tu respuesta específica
                    
                   ### 🎓 Resultados de Investigación Optimizados
                    
                   **Para Definiciones:**
                   - Estructura académica formal con contexto histórico
                   - Referencias a autores principales y papers fundamentales
                   - Conexiones con conceptos relacionados
                   - Expansión automática con sinónimos técnicos y variaciones
                    
                   **Para Comparaciones:**
                   - Matrices comparativas sistemáticas
                   - Análisis de ventajas/desventajas equilibrado
                   - Recomendaciones basadas en contexto de uso
                   - Términos contrastivos agregados automáticamente
                    
                   **Para Estado del Arte:**
                   - Evolución temporal de enfoques
                   - Identificación de tendencias emergentes  
                   - Análisis de consenso vs controversias
                   - Expansión con indicadores temporales y de tendencia
                    
                   **Para Análisis de Gaps:**
                   - Categorización de limitaciones por tipo
                   - Oportunidades específicas de investigación
                   - Conexión con trabajos futuros sugeridos
                   - Términos de limitación y oportunidad expandidos
                    
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
                   - 🔍 *El sistema expandirá automáticamente con términos relacionados*
                    
                   **🔗 Conecta conceptos:**
                   - ❌ "NLP tools"
                   - ✅ "Compare herramientas de NLP para extracción automática de requirements"
                   - 🔍 *Activará template comparativo y expandirá con variaciones técnicas*
                    
                   **📊 Solicita análisis estructurado:**
                   - ❌ "research gaps"
                   - ✅ "¿Qué limitaciones identifican los estudios actuales en automated user story generation?"
                   - 🔍 *Detectará gap analysis y expandirá con sinónimos de limitaciones*
                    
                   ### 🚀 El Futuro de tu Investigación
                   
                   Con este sistema inteligente multicapa, puedes:
                   - **⚡ Acelerar** tu revisión de literatura 5-10x con expansión automática
                   - **🎯 Identificar** gaps de investigación automáticamente con detección de intención  
                   - **📊 Comparar** metodologías de manera sistemática con templates especializados
                   - **🔍 Descubrir** conexiones entre diferentes líneas de investigación mediante expansión semántica
                   - **📈 Optimizar** la calidad académica con selección inteligente de modelos
                   - **🔬 Reproducir** resultados con total transparencia del proceso
                   """)
           
           # Event handlers para funcionalidades administrativas
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
        """
        Lanza la aplicación con configuración optimizada para investigación académica.
        
        Esta función inicia el servidor web que expone toda la funcionalidad del sistema
        RAG inteligente. La configuración por defecto está optimizada para uso académico.
        """
        interface = self.create_interface()
        
        # Configuración por defecto optimizada
        launch_kwargs = {
            'server_port': settings.server_port,
            'share': settings.share_gradio,
            'show_error': True,
            'quiet': False,
            **kwargs
        }
        
        logger.info(f"Launching advanced RAG app with multicapa AI on port {launch_kwargs['server_port']}")
        logger.info("Features enabled: Intent Detection + Query Expansion + Smart Model Selection")
        interface.launch(**launch_kwargs)