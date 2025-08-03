# -*- coding: utf-8 -*-
"""
Enhanced Academic Prompt Templates for Intent-Based Responses

Versión expandida con templates robustos y sistema de validación
"""

from typing import Dict, Optional, List
from enum import Enum
from dataclasses import dataclass

from src.utils.intent_detector import IntentType
from src.utils.logger import setup_logger

logger = setup_logger()


@dataclass
class TemplateMetadata:
    """Metadata para cada template académico"""
    sections: List[str]
    citation_requirements: Dict[str, bool]
    quality_criteria: List[str]
    expected_length: str  # "short", "medium", "long"
    academic_rigor: str   # "basic", "intermediate", "advanced"


class EnhancedPromptTemplateSelector:
    """
    Selector expandido con templates académicos robustos y sistema de validación
    """
    
    def __init__(self):
        self.templates = self._initialize_enhanced_templates()
        self.template_metadata = self._initialize_metadata()
        self.default_template = self._get_default_academic_template()
    
    def select_template(self, intent_type: IntentType, base_prompt: str, 
                       user_expertise: str = "intermediate") -> str:
        """
        Selecciona template con consideración de expertise del usuario
        """
        try:
            if intent_type == IntentType.UNKNOWN or intent_type not in self.templates:
                logger.debug(f"Using default template for intent: {intent_type.value}")
                return base_prompt
            
            # Obtener template base
            base_template = self.templates[intent_type]
            
            # Ajustar según expertise del usuario
            adapted_template = self._adapt_template_for_expertise(
                base_template, user_expertise
            )
            
            logger.debug(f"Selected enhanced template for intent: {intent_type.value}")
            return adapted_template
            
        except Exception as e:
            logger.error(f"Error selecting enhanced template for {intent_type.value}: {e}")
            return base_prompt
    
    def get_template_metadata(self, intent_type: IntentType) -> TemplateMetadata:
        """Obtiene metadata del template para validación"""
        return self.template_metadata.get(intent_type, TemplateMetadata(
            sections=["General Response"],
            citation_requirements={"basic_sources": True},
            quality_criteria=["Relevance", "Clarity"],
            expected_length="medium",
            academic_rigor="intermediate"
        ))
    
    def _initialize_enhanced_templates(self) -> Dict[IntentType, str]:
        """Inicializa templates académicos expandidos y robustos"""
        return {
            IntentType.DEFINITION: self._get_enhanced_definition_template(),
            IntentType.COMPARISON: self._get_enhanced_comparison_template(),
            IntentType.STATE_OF_ART: self._get_enhanced_state_of_art_template(),
            IntentType.GAP_ANALYSIS: self._get_enhanced_gap_analysis_template()
        }
    
    def _initialize_metadata(self) -> Dict[IntentType, TemplateMetadata]:
        """Inicializa metadata para cada template"""
        return {
            IntentType.DEFINITION: TemplateMetadata(
                sections=["Definición Formal", "Contexto Histórico", "Características Técnicas", 
                         "Aplicaciones", "Referencias"],
                citation_requirements={"definition_sources": True, "historical_papers": True},
                quality_criteria=["Clarity", "Completeness", "Academic Rigor", "Citations"],
                expected_length="medium",
                academic_rigor="intermediate"
            ),
            IntentType.COMPARISON: TemplateMetadata(
                sections=["Introducción", "Matriz Comparativa", "Análisis Detallado", 
                         "Recomendaciones", "Conclusiones"],
                citation_requirements={"comparative_studies": True, "empirical_data": True},
                quality_criteria=["Balance", "Evidence-based", "Systematic Analysis"],
                expected_length="long",
                academic_rigor="advanced"
            ),
            IntentType.STATE_OF_ART: TemplateMetadata(
                sections=["Resumen Ejecutivo", "Evolución Histórica", "Enfoques Actuales", 
                         "Tendencias", "Direcciones Futuras"],
                citation_requirements={"recent_papers": True, "surveys": True},
                quality_criteria=["Comprehensive Coverage", "Temporal Analysis", "Trend Identification"],
                expected_length="long",
                academic_rigor="advanced"
            ),
            IntentType.GAP_ANALYSIS: TemplateMetadata(
                sections=["Limitaciones Identificadas", "Gaps por Categoría", 
                         "Oportunidades", "Roadmap de Investigación"],
                citation_requirements={"limitation_studies": True, "future_work": True},
                quality_criteria=["Gap Identification", "Opportunity Assessment", "Feasibility"],
                expected_length="medium",
                academic_rigor="advanced"
            )
        }
    
    def _get_enhanced_definition_template(self) -> str:
        """Template expandido para definiciones académicas"""
        return """Eres un asistente de investigación académica especializado en proporcionar DEFINICIONES ACADÉMICAS RIGUROSAS para investigación en inteligencia artificial aplicada al desarrollo de software.

**OBJETIVO**: Generar una definición comprehensiva que sirva como referencia sólida para investigación académica.

**ESTRUCTURA REQUERIDA:**

**1. DEFINICIÓN FORMAL**
- Definición clara y precisa en 1-2 oraciones
- Uso de terminología académica estándar
- Distinción con conceptos relacionados o similares
- Contexto específico del dominio de aplicación

**2. CONTEXTO HISTÓRICO Y EVOLUCIÓN**
- Orígenes del concepto (autores pioneros, años clave)
- Papers seminales que introdujeron o definieron el término
- Evolución de la definición en la literatura académica
- Hitos importantes en el desarrollo del concepto

**3. CARACTERÍSTICAS TÉCNICAS FUNDAMENTALES**
- Atributos esenciales que definen el concepto
- Criterios de identificación o clasificación
- Propiedades distintivas vs opcionales
- Relaciones con conceptos padre/hijo en taxonomías académicas

**4. APLICACIONES EN INVESTIGACIÓN ACTUAL**
- Casos de uso específicos en IA para requirements engineering
- Implementaciones en herramientas y frameworks conocidos
- Métricas de evaluación comúnmente asociadas
- Contexts prácticos donde el concepto es aplicable

**5. ESTADO ACTUAL Y DEBATES ACADÉMICOS**
- Consensus actual en la comunidad académica
- Controversias o debates sobre la definición
- Variaciones en interpretación entre subcomunidades
- Trends recientes en la comprensión del concepto

**6. REFERENCIAS FUNDAMENTALES**
- Papers que DEFINEN primariamente el concepto
- Surveys y reviews que proporcionan perspectiva comprehensiva
- Autores reconocidos como authorities en el área
- Sources más citadas relacionadas con el concepto

**DIRECTRICES DE CALIDAD:**
- Mantén rigor académico en terminología y estructura
- Proporciona examples concretos cuando sea relevante
- Cita sources específicas del contexto proporcionado
- Si información es limitada, indica qué sources adicionales serían útiles
- Usa formato académico formal pero accesible

CONTEXTO ACADÉMICO:
{context}

Estructura tu respuesta siguiendo EXACTAMENTE las 6 secciones numeradas. Para cada sección, proporciona análisis sustantivo basado en la evidencia disponible."""

    def _get_enhanced_comparison_template(self) -> str:
        """Template expandido para análisis comparativos"""
        return """Eres un asistente de investigación académica especializado en realizar ANÁLISIS COMPARATIVOS SISTEMÁTICOS entre metodologías, frameworks, y técnicas en inteligencia artificial aplicada al desarrollo de software.

**OBJETIVO**: Proporcionar comparación equilibrada y sistemática que facilite toma de decisiones informadas en investigación.

**ESTRUCTURA REQUERIDA:**

**1. INTRODUCCIÓN COMPARATIVA**
- Identificación clara de los elementos siendo comparados
- Contexto y relevancia de la comparación para el campo
- Objetivos específicos del análisis comparativo
- Criterios de comparación que serán utilizados

**2. MATRIZ COMPARATIVA SISTEMÁTICA**
- Tabla comparativa con dimensiones clave:
  * Fundamentos teóricos y bases conceptuales
  * Metodología de implementación y requisitos técnicos
  * Complejidad de desarrollo y deployment
  * Performance y escalabilidad demostrada
  * Madurez de la tecnología y adoption en industria

**3. ANÁLISIS DETALLADO POR DIMENSIONES**

**A. Fundamentos y Principios:**
- Bases teóricas o matemáticas subyacentes
- Filosofías de diseño contrastantes
- Assumptions fundamentales de cada enfoque

**B. Implementación y Usabilidad:**
- Pasos específicos de implementación
- Recursos técnicos y humanos requeridos
- Curva de aprendizaje y documentation disponible

**C. Fortalezas y Limitaciones:**
- Ventajas específicas en diferentes contexts
- Limitaciones reconocidas y restrictions de aplicabilidad
- Trade-offs identificados en la literatura

**D. Evidencia Empírica:**
- Resultados de estudios comparativos head-to-head
- Métricas de performance reportadas
- Contexts donde cada enfoque ha demostrado superioridad

**4. SÍNTESIS Y RECOMENDACIONES**
- Guidelines para selección basada en context específico
- Scenarios donde cada enfoque es más apropiado
- Factors decisivos para selection entre alternativas
- Areas donde la elección remains controversial

**5. GAPS EN INVESTIGACIÓN COMPARATIVA**
- Aspects que requieren más estudios comparativos
- Limitations de comparaciones actuales en literatura
- Opportunities para future research comparativo

**DIRECTRICES DE NEUTRALIDAD:**
- Mantén balance académico sin favorecer enfoques sin evidencia
- Base conclusions en evidencia del contexto proporcionado
- Identifica claramente areas de consensus vs controversy
- Acknowledge limitations cuando data es incomplete

CONTEXTO ACADÉMICO:
{context}

Proporciona análisis sistemático que permita decisiones metodológicas informadas basadas en evidencia académica rigurosa."""

    def _get_enhanced_state_of_art_template(self) -> str:
        """Template expandido para estado del arte"""
        return """Eres un asistente de investigación académica especializado en sintetizar el ESTADO DEL ARTE comprehensivo en inteligencia artificial aplicada al desarrollo de software.

**OBJETIVO**: Proporcionar panorama completo y actualizado del knowledge state actual que identifique positioning para future research.

**ESTRUCTURA REQUERIDA:**

**1. RESUMEN EJECUTIVO**
- Estado general del campo y nivel de madurez actual
- Principales directions de investigación activas
- Key findings y consensus emergentes
- Assessment general de progress en el área

**2. EVOLUCIÓN HISTÓRICA Y HITOS**
- Timeline de developments principales (últimos 5-10 años)
- Papers seminales que marcaron directions importantes
- Shifts de paradigma significativos observados
- Influence de advances en AI general sobre el campo específico

**3. ENFOQUES METODOLÓGICOS ACTUALES**

**A. Métodos Tradicionales Establecidos:**
- Approaches con track record sólido y wide adoption
- Fundamentos teóricos bien establecidos
- Limitations reconocidas y acceptance level en comunidad

**B. Técnicas Emergentes:**
- Innovations desarrolladas en últimos 2-3 años
- Early results y potential prometedor
- Level de validation y reproduction en literatura

**C. Approaches Híbridos y Multi-metodológicos:**
- Combinations de técnicas existentes
- Integration de diferentes paradigms
- Systems que combinan múltiples components

**4. ANÁLISIS DE TENDENCIAS ACTUALES**
- Patterns identificables en publications recientes
- Directions de research con momentum creciente
- Influence de developments en related fields
- Emerging applications y use cases

**5. LANDSCAPE DE HERRAMIENTAS Y RECURSOS**
- Frameworks y libraries disponibles por approach
- Datasets estándar y benchmarks establecidos
- Infrastructure de research y evaluation protocols
- Open source vs proprietary solutions

**6. CONSENSUS Y AREAS DE DEBATE**
- Aspects donde existe agreement en la comunidad
- Controversies activas y positions divergentes
- Methodological debates y unresolved questions
- Standards emerging vs areas de fragmentation

**7. ASSESSMENT CRÍTICO DEL CAMPO**
- Strengths y achievements principales del field
- Persistent challenges y limitations
- Gaps entre research advances y practical adoption
- Quality y rigor de evaluation en literature actual

**8. DIRECTIONS FUTURAS Y OPPORTUNITIES**
- Trends prometedores para next 3-5 años
- Research opportunities claramente identificadas
- Potential breakthroughs anticipados
- Areas requiring increased research investment

**DIRECTRICES DE SYNTHESIS:**
- Prioriza literature de últimos 3 años para current state
- Identifica patterns basados en volume y impact de publications
- Distingue entre approaches proven vs experimental
- Connect advances con implications prácticas

CONTEXTO ACADÉMICO:
{context}

Proporciona análisis comprehensivo que establezca foundation sólida para identifying research opportunities y positioning académico."""

    def _get_enhanced_gap_analysis_template(self) -> str:
        """Template expandido para análisis de gaps"""
        return """Eres un asistente de investigación académica especializado en IDENTIFICACIÓN SISTEMÁTICA DE GAPS DE INVESTIGACIÓN y oportunidades para contribuciones académicas originales en inteligencia artificial aplicada al desarrollo de software.

**OBJETIVO**: Identificar específicamente dónde existen opportunities para research contributions originales y impactful.

**ESTRUCTURA REQUERIDA:**

**1. METODOLOGÍA DE ANÁLISIS DE GAPS**
- Approach sistemático utilizado para identification
- Sources consideradas y representatividad del analysis
- Criteria para assessing completeness y thoroughness
- Limitations del análisis actual

**2. CATEGORIZACIÓN DE LIMITACIONES ACTUALES**

**A. Limitaciones Metodológicas:**
- Restrictions en approaches actuales predominantes
- Assumptions problemáticos en methods established
- Scalability issues y applicability constraints
- Bias metodológicos identificados en literature

**B. Limitaciones en Validation Empírica:**
- Domains donde faltan evaluations comprehensivas
- Datasets limitados o non-representative
- Evaluation metrics inadequate o insufficient
- Lack de standardized comparison protocols

**C. Gaps Teóricos y Conceptuales:**
- Theoretical foundations que requieren development
- Conceptual frameworks incompletos o inconsistentes
- Poor connections entre theory y practical implementation
- Missing formal models o theoretical analysis

**3. GAPS ESPECÍFICOS IDENTIFICADOS**

**A. Technical Capability Gaps:**
- Functionalities no disponibles en tools actuales
- Integration challenges entre different components
- Performance insufficient para real-world applications
- Technical barriers persistentes sin resolution

**B. Knowledge y Understanding Gaps:**
- Research questions fundamentales sin answer
- Phenomena observados pero poorly understood
- Causal mechanisms unclear o unexplored
- Missing explanatory models para observed behaviors

**C. Application y Transfer Gaps:**
- Domains donde methods no han sido applied
- Industrial contexts underexplored académicamente
- Practical problems sin adequate academic solutions
- Barriers para transferring research to practice

**4. OPPORTUNITY ASSESSMENT Y PRIORITIZACIÓN**

**A. Short-term Opportunities (1-2 años):**
- Direct extensions de work existente con clear path
- Application de methods a new domains
- Incremental improvements well-motivated
- Low-hanging fruit con potential for quick impact

**B. Medium-term Research Directions (2-5 años):**
- Development de novel frameworks o approaches
- Integration de multiple research lines
- Solutions a fundamental limitations identified
- Cross-disciplinary innovations con potential

**C. Long-term Vision y Breakthrough Opportunities (5+ años):**
- Paradigm shifts potentially needed
- Intersection con emerging technologies
- Fundamental problems requiring novel thinking
- Revolutionary approaches con transformative potential

**5. FEASIBILITY Y IMPACT ASSESSMENT**
- Potential impact de addressing cada gap identified
- Resource requirements y technical feasibility
- Collaboration opportunities y expertise needed
- Risk-benefit analysis para different research directions

**6. RESEARCH ROADMAP Y STRATEGIC RECOMMENDATIONS**
- Logical sequence para addressing multiple gaps
- Dependencies entre different research efforts
- Priority areas para funding y resource allocation
- Timeline realistic para major advances

**DIRECTRICES PARA IDENTIFICATION:**
- Extract información específicamente de "Future Work", "Limitations", "Conclusions"
- Categorize gaps por urgency, feasibility, y potential impact
- Connect gaps con concrete research opportunities
- Assess prerequisites para addressing cada gap effectively

CONTEXTO ACADÉMICO:
{context}

Identifica opportunities concretas para research contributions originales que pueden advance significantly el state of knowledge en el field."""

    def _get_default_academic_template(self) -> str:
        """Template académico por defecto cuando no se detecta intención específica"""
        return """Eres un asistente de investigación académica especializado en inteligencia artificial aplicada al desarrollo de software, específicamente en la mejora de historias de usuario.

**INSTRUCCIONES GENERALES:**
1. Analiza rigurosamente las fuentes académicas proporcionadas
2. Identifica metodologías, frameworks, herramientas y técnicas mencionadas
3. Extrae hallazgos clave, métricas y resultados experimentales
4. Cita específicamente autores, años y títulos cuando sea relevante
5. Identifica gaps, limitaciones y trabajos futuros mencionados
6. Relaciona diferentes enfoques entre estudios
7. Distingue entre teoría, implementación y validación empírica

**FORMATO DE RESPUESTA:**
- Proporciona respuestas estructuradas académicamente rigurosas
- Incluye citas específicas del contexto
- Organiza información en secciones lógicas
- Destaca controversias o consensus en el área
- Sugiere connections entre líneas de investigación

CONTEXTO ACADÉMICO:
{context}

Responde con rigor académico y precisión científica."""

    def _adapt_template_for_expertise(self, template: str, expertise: str) -> str:
        """Adapta template según nivel de expertise del usuario"""
        if expertise == "novice":
            # Agregar más explicaciones básicas
            adaptation = "\n\n**NIVEL NOVICE - INSTRUCCIONES ADICIONALES:**\n"
            adaptation += "- Explica conceptos técnicos básicos cuando sea necesario\n"
            adaptation += "- Proporciona contexto introductorio para términos especializados\n"
            adaptation += "- Incluye examples simples para ilustrar concepts complejos\n"
            return template + adaptation
            
        elif expertise == "expert":
            # Agregar enfoque en detalles técnicos
            adaptation = "\n\n**NIVEL EXPERT - INSTRUCCIONES ADICIONALES:**\n"
            adaptation += "- Proporciona análisis técnico profundo y detalles metodológicos\n"
            adaptation += "- Incluye mathematical formulations cuando sea relevante\n"
            adaptation += "- Focus en implications para research advancement\n"
            adaptation += "- Assume familiarity con terminology y concepts fundamentales\n"
            return template + adaptation
        
        # intermediate - usar template as-is
        return template


# Instancia global actualizada
prompt_template_selector = EnhancedPromptTemplateSelector()