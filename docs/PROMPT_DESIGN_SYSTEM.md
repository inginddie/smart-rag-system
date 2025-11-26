# 🎨 Sistema de Diseño de Prompts Dinámicos

## 📋 Tabla de Contenidos

- [Visión General](#visión-general)
- [Características Principales](#características-principales)
- [Arquitectura](#arquitectura)
- [Guía de Uso](#guía-de-uso)
- [Sectores Preconfigur ados](#sectores-preconfigurados)
- [Crear Sectores Personalizados](#crear-sectores-personalizados)
- [API de Programación](#api-de-programación)
- [Integración con RAG](#integración-con-rag)
- [Casos de Uso](#casos-de-uso)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Visión General

El **Sistema de Diseño de Prompts Dinámicos** permite configurar el comportamiento del RAG para diferentes dominios, sectores o necesidades **sin modificar código**. Transforma el sistema de un RAG académico especializado a un **RAG configurable para cualquier sector**.

### Problema que Resuelve

**Antes:** El sistema estaba hardcodeado para investigación académica. Cambiar el dominio requería modificar código fuente.

**Ahora:** Configura prompts desde la UI para cualquier sector: negocios, legal, médico, técnico, o personalizado.

### Beneficios

✅ **Sin Código**: Configura todo desde la interfaz Gradio
✅ **Multi-Sector**: Soporta múltiples dominios simultáneamente
✅ **Cambio Dinámico**: Cambia de sector sin reiniciar
✅ **Personalizable**: Crea sectores completamente personalizados
✅ **Persistente**: Configuraciones guardadas en JSON
✅ **Versionado**: Backups automáticos de configuraciones

---

## 🚀 Características Principales

### 1. Gestión de Sectores

- **6 Sectores Preconfigu rados**: Académico, Negocios, Legal, Médico, Técnico, Personalizado
- **Creación de Sectores**: Define tus propios sectores desde la UI
- **Activación Dinámica**: Cambia el sector activo en tiempo real
- **Habilitación/Deshabilitación**: Control fino de sectores disponibles

### 2. Configuración por Sector

Cada sector puede configurar:

- **System Prompt**: Define el comportamiento base del asistente
- **Intent Prompts**: Prompts especializados por tipo de consulta (DEFINITION, COMPARISON, etc.)
- **Guidelines**: Reglas que el asistente debe seguir
- **Metadata**: Descripción, habilitación, configuraciones adicionales

### 3. Interfaz de Usuario

Panel completo con 6 pestañas:

1. **⚙️ Configurar Sector**: Edita prompts y guidelines del sector activo
2. **🧪 Probar Prompts**: Prueba cómo responderá el sistema
3. **➕ Nuevo Sector**: Crea sectores personalizados
4. **📋 Gestionar Sectores**: Lista y elimina sectores
5. **💾 Import/Export**: Exporta/importa configuraciones completas

### 4. Integración Transparente

- **Detección de Intención**: Automática vía Intent Detector
- **Selección de Prompts**: Basada en sector activo + intención
- **Feedback en UI**: Muestra sector y tipo de intención usado
- **Backward Compatible**: Funciona con sistema legacy si se deshabilita

---

## 🏗️ Arquitectura

### Componentes Principales

```
┌─────────────────────────────────────────────────────────┐
│                     UI Layer                             │
│  prompt_design_panel.py - Interfaz Gradio               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Business Logic                          │
│  prompt_design_manager.py - Gestión de prompts          │
│  dynamic_prompt_orchestrator.py - Orquestación          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Persistence Layer                       │
│  prompt_storage.py - Almacenamiento JSON                │
│  config/custom_prompts.json - Configuración             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                   RAG Integration                        │
│  rag_chain.py - Uso de prompts dinámicos                │
└─────────────────────────────────────────────────────────┘
```

### Flujo de Ejecución

```
1. Usuario hace query → RAGService.query()
2. RAGChain detecta intención → IntentDetector
3. DynamicPromptOrchestrator obtiene prompts:
   - Lee sector activo de PromptStorage
   - Selecciona intent prompt apropiado
   - Construye system + user prompts
4. RAGChain ejecuta con prompts personalizados
5. UI muestra sector e intención usados
```

---

## 📖 Guía de Uso

### Inicio Rápido (5 minutos)

#### 1. Lanzar Aplicación

```bash
python launch_with_api.py
```

#### 2. Abrir UI

Navegar a: `http://localhost:7860`

#### 3. Ir al Tab de Diseño de Prompts

Click en: **🎨 Diseño de Prompts**

#### 4. Ver Sector Activo

En la sección "🎯 Sector Activo" verás el sector actual (por defecto: "Investigación Académica")

#### 5. Probar con el Sector Actual

1. Ve a "💬 Chat Académico"
2. Haz una pregunta: "¿Cuáles son las tendencias actuales?"
3. La respuesta mostrará: **🎯 Sector: Investigación Académica | Tipo: GENERAL**

#### 6. Cambiar de Sector

1. Vuelve a **🎨 Diseño de Prompts**
2. En dropdown "Sector Activo", selecciona: "Análisis de Negocios"
3. Click en **✅ Activar Sector Seleccionado**
4. Vuelve al chat y haz la misma pregunta
5. La respuesta ahora usará el enfoque de negocios

---

## 🏢 Sectores Preconfigurados

### 1. Investigación Académica (`academic_research`)

**Uso**: Análisis de papers, síntesis académica, estado del arte

**System Prompt**:
```
Eres un asistente de investigación académica especializado en análisis riguroso de literatura científica.
```

**Guidelines**:
- Cita fuentes específicas con autores y años
- Mantén rigor académico en terminología
- Identifica gaps y limitaciones en la investigación
- Proporciona análisis crítico basado en evidencia

**Cuándo Usar**: Investigación, tesis, papers académicos

---

### 2. Análisis de Negocios (`business_analysis`)

**Uso**: Estrategia empresarial, análisis de mercado, toma de decisiones

**System Prompt**:
```
Eres un analista de negocios experto que proporciona insights estratégicos basados en datos.
```

**Guidelines**:
- Enfócate en valor de negocio y ROI
- Identifica riesgos y oportunidades
- Proporciona recomendaciones accionables
- Usa métricas y KPIs relevantes

**Cuándo Usar**: Planes de negocio, análisis de mercado, estrategia

---

### 3. Revisión Legal (`legal_review`)

**Uso**: Análisis de contratos, regulaciones, compliance

**System Prompt**:
```
Eres un asistente legal que analiza documentos con precisión y rigor jurídico.
```

**Guidelines**:
- Mantén precisión en terminología legal
- Identifica cláusulas y obligaciones clave
- Señala riesgos y áreas de atención
- Referencia leyes y regulaciones aplicables

**Cuándo Usar**: Contratos, términos y condiciones, compliance

---

### 4. Análisis Médico (`medical_analysis`)

**Uso**: Literatura médica, casos clínicos, evidencia científica

**System Prompt**:
```
Eres un asistente médico especializado en análisis de literatura clínica y evidencia médica.
```

**Guidelines**:
- Prioriza evidencia basada en estudios clínicos
- Usa terminología médica precisa
- Identifica nivel de evidencia y calidad de estudios
- Señala contraindicaciones y consideraciones de seguridad

**Cuándo Usar**: Investigación médica, revisión de literatura clínica

---

### 5. Documentación Técnica (`technical_documentation`)

**Uso**: Arquitectura de software, documentación técnica, código

**System Prompt**:
```
Eres un arquitecto de software experto que analiza documentación técnica y proporciona soluciones.
```

**Guidelines**:
- Usa terminología técnica precisa
- Proporciona ejemplos de código cuando sea relevante
- Identifica patrones y mejores prácticas
- Señala trade-offs arquitectónicos

**Cuándo Usar**: Documentación de sistemas, arquitectura, código

---

### 6. Personalizado (`custom`)

**Uso**: Plantilla base para crear sectores personalizados

**System Prompt**:
```
Eres un asistente inteligente que proporciona respuestas precisas y útiles.
```

**Cuándo Usar**: Punto de partida para sectores personalizados

---

## ➕ Crear Sectores Personalizados

### Desde la UI

#### 1. Ir al Tab "➕ Nuevo Sector"

#### 2. Completar Formulario

- **ID del Sector**: `marketing_digital` (sin espacios, minúsculas)
- **Nombre**: `Marketing Digital`
- **Descripción**: `Análisis de estrategias de marketing digital y SEO`
- **System Prompt**:
  ```
  Eres un especialista en marketing digital con expertise en SEO, SEM, redes sociales y analytics.

  Proporcionas insights basados en métricas y mejores prácticas actuales.
  ```
- **Directrices** (una por línea):
  ```
  Enfócate en métricas digitales (CTR, CPC, ROAS, engagement)
  Menciona herramientas específicas (Google Analytics, SEMrush, etc.)
  Considera tendencias actuales en redes sociales
  Proporciona recomendaciones accionables y medibles
  ```

#### 3. Click en "✨ Crear Sector"

#### 4. Activar el Nuevo Sector

1. Volver a "🎯 Sector Activo"
2. Seleccionar "Marketing Digital" en dropdown
3. Click "✅ Activar Sector Seleccionado"

---

### Desde Código (Python)

```python
from src.admin.prompt_design_manager import PromptDesignManager

manager = PromptDesignManager()

# Crear sector personalizado
manager.create_custom_sector(
    sector_id="hr_management",
    name="Gestión de Recursos Humanos",
    description="Análisis de RRHH, cultura organizacional y talento",
    system_prompt="""Eres un experto en gestión de recursos humanos que proporciona insights sobre:
- Adquisición y retención de talento
- Cultura organizacional
- Performance management
- Employee engagement
- Compensación y beneficios""",
    guidelines=[
        "Enfócate en mejores prácticas de RRHH",
        "Considera aspectos legales y de compliance",
        "Usa datos de encuestas de clima y engagement",
        "Proporciona frameworks probados (OKRs, 360 feedback, etc.)"
    ]
)

# Activar el sector
manager.set_active_sector("hr_management")

print("✅ Sector de RRHH creado y activado")
```

---

## 🔧 API de Programación

### PromptDesignManager

Gestiona sectores y configuraciones.

```python
from src.admin.prompt_design_manager import PromptDesignManager

manager = PromptDesignManager()

# Obtener sector activo
sector_id, sector_config = manager.get_active_sector()

# Cambiar sector
manager.set_active_sector("business_analysis")

# Actualizar system prompt
manager.update_system_prompt(
    "business_analysis",
    "Nuevo system prompt..."
)

# Agregar guideline
manager.add_response_guideline(
    "business_analysis",
    "Considera impacto en stakeholders"
)

# Obtener estadísticas
stats = manager.get_statistics()
```

### DynamicPromptOrchestrator

Obtiene prompts dinámicamente.

```python
from src.utils.dynamic_prompt_orchestrator import DynamicPromptOrchestrator
from src.utils.intent_detector import intent_detector

orchestrator = DynamicPromptOrchestrator()

# Obtener prompts para query
query = "Analiza las tendencias del mercado"
intent_result = await intent_detector.detect_intent(query)

dynamic_result = orchestrator.get_prompts_for_query(
    query=query,
    intent_result=intent_result
)

# Usar prompts
print(f"Sector: {dynamic_result.sector_name}")
print(f"System Prompt: {dynamic_result.system_prompt}")
print(f"Guidelines: {dynamic_result.guidelines}")

# Validar configuración
validation = orchestrator.validate_prompts("business_analysis")
if validation['valid']:
    print("✅ Configuración válida")
else:
    print(f"❌ Problemas: {validation['issues']}")
```

### PromptStorage

Persistencia de configuraciones.

```python
from src.admin.prompt_storage import PromptStorage

storage = PromptStorage()

# Exportar configuración
config_json = storage.export_config()
with open("backup.json", "w") as f:
    f.write(config_json)

# Importar configuración
with open("backup.json", "r") as f:
    config_json = f.read()
storage.import_config(config_json)
```

---

## 🔗 Integración con RAG

### Cómo Funciona

1. **Usuario hace query** → `RAGService.query()`
2. **Intent Detection** → Detecta tipo de consulta
3. **Prompt Selection** → `DynamicPromptOrchestrator.get_prompts_for_query()`
   - Lee sector activo
   - Selecciona intent prompt apropiado
   - Combina system prompt + guidelines
4. **RAG Execution** → `RAGChain.invoke()` con prompts personalizados
5. **Response Enhancement** → Agrega info de sector e intención

### Habilitar/Deshabilitar

Por defecto, el sistema de prompts dinámicos está **habilitado**.

Para usar el sistema legacy:

```python
# En RAGChain
chain = RAGChain(use_dynamic_prompts=False)
```

### Información en Respuestas

Las respuestas incluyen metadata del sistema de prompts:

```python
result = rag_service.query("mi pregunta")

# Información de prompts dinámicos
if 'dynamic_prompt_info' in result:
    info = result['dynamic_prompt_info']
    print(f"Sector: {info['sector_name']}")
    print(f"Intent: {info['intent_type']}")
    print(f"Guidelines: {info['guidelines']}")
```

---

## 💼 Casos de Uso

### Caso 1: Startup Multi-Producto

**Necesidad**: RAG para analizar documentos de 3 áreas diferentes.

**Solución**:

1. Crear sector "product_development" para specs técnicas
2. Crear sector "sales_enablement" para materiales de ventas
3. Crear sector "customer_support" para documentación de soporte
4. Cambiar sector según el área que se esté consultando

**Beneficio**: Un solo sistema RAG con comportamientos especializados.

---

### Caso 2: Consultoría Multi-Cliente

**Necesidad**: Adaptar RAG para diferentes clientes con diferentes dominios.

**Solución**:

1. Crear sector por cliente: "client_healthcare", "client_finance", etc.
2. Configurar prompts con terminología del dominio del cliente
3. Exportar configuración de cada cliente
4. Importar según cliente activo

**Beneficio**: Configuraciones persistentes y versionadas por cliente.

---

### Caso 3: Universidad Multi-Departamento

**Necesidad**: Sistema RAG para diferentes facultades.

**Solución**:

1. Sector "engineering" con prompts técnicos
2. Sector "medicine" con prompts médicos
3. Sector "law" con prompts legales
4. Sector "business" con prompts empresariales

**Beneficio**: Un sistema institucional que se adapta a cada facultad.

---

### Caso 4: Evolución del Sistema

**Necesidad**: Empezar con académico, evolucionar a comercial.

**Solución**:

1. Fase 1: Usar "academic_research" (default)
2. Fase 2: Crear "commercial_analysis" cuando se necesite
3. Fase 3: Ambos sectores disponibles según contexto

**Beneficio**: Evolución gradual sin reescribir código.

---

## 🐛 Troubleshooting

### Problema: Sector no cambia

**Síntomas**: Cambio de sector pero respuestas usan sector anterior

**Solución**:
1. Verificar mensaje de confirmación: "✅ Sector activado exitosamente"
2. Refrescar página del navegador
3. Ver en respuestas que muestre: "🎯 Sector: [Nuevo Sector]"

---

### Problema: Prompts no se guardan

**Síntomas**: Cambios en prompts no persisten

**Solución**:
1. Verificar permisos de escritura en `config/custom_prompts.json`
2. Revisar logs en `logs/app.log`
3. Usar Export para respaldar configuración

---

### Problema: Error al crear sector

**Síntomas**: "Sector ya existe"

**Solución**:
1. Verificar que ID sea único
2. Usar "📋 Gestionar Sectores" para ver sectores existentes
3. Eliminar sector antiguo si es necesario

---

### Problema: Validación falla

**Síntomas**: Warnings o issues en validación

**Solución**:
1. Ir a "🧪 Probar Prompts"
2. Ejecutar validación
3. Corregir issues reportados:
   - System prompt muy corto → Agregar más contexto
   - Sin placeholder `{context}` → Agregar a intent prompts
   - Sin guidelines → Agregar al menos 2-3

---

## 📊 Archivos y Ubicaciones

### Configuración

```
config/
├── custom_prompts.json         # Configuración principal
└── backups/
    └── prompts/
        └── custom_prompts_*.json   # Backups automáticos
```

### Código Fuente

```
src/
├── admin/
│   ├── prompt_design_manager.py     # Gestión de prompts
│   └── prompt_storage.py            # Persistencia
├── utils/
│   └── dynamic_prompt_orchestrator.py  # Orquestación
└── chains/
    └── rag_chain.py                 # Integración RAG

ui/
└── components/
    └── prompt_design_panel.py        # Panel UI
```

---

## 🎓 Mejores Prácticas

### 1. Diseño de System Prompts

✅ **Hacer**:
- Ser específico sobre el rol del asistente
- Definir expertise y enfoque
- Mencionar formato de respuesta esperado

❌ **No Hacer**:
- Prompts genéricos ("Eres útil")
- Demasiado largo (>500 palabras)
- Sin dirección clara

### 2. Configuración de Guidelines

✅ **Hacer**:
- 3-7 guidelines por sector
- Específicas y accionables
- Relacionadas con el dominio

❌ **No Hacer**:
- Más de 10 guidelines (sobrecarga)
- Guidelines vagas ("Sé bueno")
- Guidelines contradictorias

### 3. Organización de Sectores

✅ **Hacer**:
- IDs descriptivos en snake_case
- Nombres claros y profesionales
- Descripciones concisas pero informativas

❌ **No Hacer**:
- IDs crípticos (sec1, sec2)
- Nombres ambiguos
- Sin descripciones

### 4. Mantenimiento

✅ **Hacer**:
- Exportar config regularmente
- Probar prompts antes de activar
- Mantener backups externos

❌ **No Hacer**:
- Modificar JSON directamente sin backup
- Borrar sectores sin probar impacto
- Ignorar validaciones

---

## 🚀 Roadmap Futuro

### En Consideración

- [ ] **Templates por Rol de Usuario**: Prompts diferentes para novatos vs expertos
- [ ] **A/B Testing**: Comparar efectividad de prompts
- [ ] **Analytics**: Métricas de uso por sector
- [ ] **Versionado de Prompts**: Git-like version control
- [ ] **Prompts Condicionales**: Basados en metadata del documento
- [ ] **Integración con Fine-tuning**: Exportar prompts para fine-tuning

---

## 📚 Referencias

- [Documentación Principal](../README.md)
- [Demo Script](../demo_prompt_design.py)
- [API Reference](./API_REFERENCE.md)
- [Guía de Contribución](../CONTRIBUTING.md)

---

**Versión**: 1.0.0
**Última Actualización**: 2025-11-26
**Mantenedor**: Smart RAG System Team
