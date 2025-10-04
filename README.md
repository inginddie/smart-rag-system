# Sistema RAG Avanzado con Agentes Inteligentes
![image](https://github.com/user-attachments/assets/18a05e72-63bc-4ba0-8940-d4012af75a8e)

Un sistema completo de Retrieval-Augmented Generation (RAG) con arquitectura de agentes especializados, construido con Python, LangChain y Gradio.

## 🚀 Características Principales

### Sistema RAG Base
- **Múltiples formatos de documentos**: PDF, TXT, DOCX, XLS/XLSX
- **Soporte para datos en PostgreSQL**
- **Interfaz web intuitiva** con Gradio
- **Modo CLI** para consultas por línea de comandos
- **Sistema de logging avanzado**
- **Configuración centralizada** con variables de entorno
- **Manejo robusto de errores**
- **Arquitectura modular y escalable**
- **Tests unitarios incluidos**

### 🤖 Sistema de Agentes Especializados
- **DocumentSearchAgent**: Búsqueda semántica avanzada y síntesis académica
- **Registro de Agentes**: Descubrimiento automático por capacidades
- **Sistema de Fallback**: Recuperación automática ante errores
- **Métricas y Observabilidad**: Estadísticas detalladas por agente
- **Activación Inteligente**: Selección automática del mejor agente

### 🔧 Administración de Keywords (NUEVO)
- **Gestión Dinámica**: Agregar/eliminar keywords sin código
- **Pruebas en Tiempo Real**: Verificar activación de agentes con queries
- **Configuración de Threshold**: Ajustar sensibilidad de activación
- **Soporte Multiidioma**: Keywords en español e inglés
- **Persistencia Segura**: Backups automáticos de configuración
- **Panel de Administración**: Interfaz intuitiva en Gradio

## 📦 Instalación Rápida

### 1. Generar el proyecto
```bash
python generate_rag_project.py
```
Las funciones reutilizables para crear directorios y archivos se
encuentran en `src/utils/project_setup.py` por si deseas utilizarlas
desde tu propio código.

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
# Copia el template de configuración
cp config.template .env

# Edita .env y configura tu API key de OpenAI
# OPENAI_API_KEY=tu_api_key_aqui
```

### 5. Lanzar la aplicación
```bash
python main.py --mode ui
```

## 🎯 Uso Rápido

### Inicio Básico
1. **Coloca documentos** en `data/documents/`
2. **Lanza la aplicación**: `python launch_app.py`
3. **Abre** el navegador (se abre automáticamente)
4. **Inicializa** el sistema en la pestaña "⚙️ Administración"
5. **Haz preguntas** en la pestaña "💬 Chat Académico"

### 🔧 Gestión de Keywords (Nuevo)
1. **Ve al tab** "🔧 Administración"
2. **Prueba queries** en tiempo real
3. **Agrega keywords** por capacidad
4. **Ajusta threshold** según necesites
5. **Exporta/importa** configuraciones

**Ejemplo**: Agregar soporte para portugués
```
1. Expandir "DOCUMENT_SEARCH"
2. Agregar: "pesquisar"
3. Agregar: "procurar"
4. Probar: "Pesquisar documentos sobre IA"
```

## 📁 Estructura del Proyecto

```
rag_system/
├── config/                      # Configuración
│   ├── agent_keywords.json      # Keywords de agentes (NUEVO)
│   └── backups/                 # Backups automáticos (NUEVO)
├── src/
│   ├── admin/                   # Administración de keywords (NUEVO)
│   │   ├── keyword_manager.py   # Gestor de keywords
│   │   └── keyword_storage.py   # Persistencia
│   ├── agents/                  # Sistema de agentes (NUEVO)
│   │   ├── base/                # Arquitectura base
│   │   │   ├── agent.py         # BaseAgent
│   │   │   ├── registry.py      # Registro de agentes
│   │   │   └── fallback.py      # Sistema de fallback
│   │   └── specialized/         # Agentes especializados
│   │       └── document_search.py
│   ├── models/                  # Modelos de embedding
│   ├── storage/                 # Base vectorial y procesamiento
│   ├── chains/                  # Cadenas RAG
│   ├── services/                # Lógica de negocio
│   └── utils/                   # Utilidades
├── ui/                          # Interfaz Gradio
│   └── components/              # Componentes UI (NUEVO)
│       └── admin_panel.py       # Panel de administración
├── data/                        # Datos y documentos
├── tests/                       # Tests unitarios
│   └── agents/                  # Tests de agentes (NUEVO)
├── logs/                        # Archivos de log
└── launch_app.py                # Launcher principal (NUEVO)
```

## 🛠️ Comandos Útiles

### Interfaces
```bash
python launch_app.py            # Launcher principal (RECOMENDADO)
python main.py --mode ui        # Interfaz web
python main.py --mode cli --query "tu pregunta"  # CLI
python main.py --mode setup     # Configurar proyecto
```

### Testing
```bash
# Tests generales
pytest tests/ -v

# Tests de agentes
pytest tests/agents/ -v

# Test de administración de keywords
python test_keyword_admin.py
```

### Administración de Keywords
```bash
# Ver configuración actual
cat config/agent_keywords.json

# Exportar configuración
# (Usar el botón "📤 Exportar Config" en la UI)

# Restaurar desde backup
cp config/backups/agent_keywords_YYYYMMDD_HHMMSS.json config/agent_keywords.json
```

### Formato de código
```bash
black src/ ui/ tests/
isort src/ ui/ tests/
```

### Base de datos de trazas
Cada llamada al LLM se registra en `data/traces.db`. Puedes cambiar la ruta con la variable `TRACE_DB_PATH`. El costo se calcula usando los precios definidos en `model_prices`.

Para consultar los registros:
```bash
sqlite3 data/traces.db "SELECT * FROM llm_traces LIMIT 5;"
```

Para exportar el costo diario a CSV:
```bash
python scripts/export_daily_cost.py
```

## 🤖 Sistema de Agentes y Keywords

### ¿Qué son los Agentes?

Los agentes son componentes especializados que procesan tipos específicos de consultas. El sistema selecciona automáticamente el mejor agente según las keywords detectadas en tu query.

### Agentes Disponibles

#### DocumentSearchAgent
- **Capacidades**: 
  - `DOCUMENT_SEARCH`: Búsqueda de documentos y papers
  - `SYNTHESIS`: Síntesis de múltiples fuentes
  - `ACADEMIC_ANALYSIS`: Análisis académico y de investigación

- **Keywords por defecto**:
  - Inglés: search, find, document, paper, synthesize, academic, research
  - Español: buscar, encontrar, documento, articulo, sintetizar, academico, investigacion

### Cómo Funciona la Activación

1. **Usuario hace una query**: "Find research papers about AI"
2. **Sistema detecta keywords**: "find", "paper", "research"
3. **Calcula score**: 2 de 3 capacidades matched = 0.67
4. **Compara con threshold**: 0.67 >= 0.3 → ✅ Agente se activa
5. **Procesa con agente especializado**

### Gestión de Keywords

#### Desde la UI (Recomendado)

1. **Abrir panel**: Tab "🔧 Administración"
2. **Ver estadísticas**: Agentes, capacidades, keywords totales
3. **Probar query**: Sección "🧪 Prueba de Activación"
4. **Agregar keyword**: 
   - Expandir capacidad (ej: DOCUMENT_SEARCH)
   - Escribir keyword en "Nueva Keyword"
   - Presionar "➕ Agregar"
5. **Ajustar threshold**: Mover slider y presionar "💾 Actualizar"

#### Desde Código

```python
from src.services.rag_service import RAGService

rag = RAGService()
rag.initialize()

# Agregar keyword
rag.add_agent_keyword("DocumentSearchAgent", "DOCUMENT_SEARCH", "investigar")

# Probar activación
results = rag.test_query_activation("Quiero investigar sobre IA")
print(results)

# Actualizar threshold
rag.update_agent_threshold("DocumentSearchAgent", 0.5)
```

### Casos de Uso

#### Agregar Soporte para Nuevo Idioma

**Objetivo**: Agregar keywords en portugués

```
1. Expandir "DOCUMENT_SEARCH"
2. Agregar: "pesquisar"
3. Agregar: "procurar"
4. Agregar: "documento"
5. Probar: "Pesquisar documentos sobre IA"
```

#### Hacer el Agente Más Selectivo

**Objetivo**: Reducir falsos positivos

```
1. Ajustar threshold de 0.3 a 0.5
2. Probar queries ambiguas
3. Verificar que solo queries claras activan el agente
```

#### Agregar Términos Específicos del Dominio

**Objetivo**: Mejorar detección en tu área de investigación

```
1. Expandir "ACADEMIC_ANALYSIS"
2. Agregar: "metodologia"
3. Agregar: "framework"
4. Agregar: "hipotesis"
5. Probar con queries de tu dominio
```

### Backups y Seguridad

- **Backups automáticos**: Antes de cada cambio
- **Ubicación**: `config/backups/agent_keywords_*.json`
- **Retención**: Últimos 10 backups
- **Restauración**: Copiar backup a `config/agent_keywords.json`

### Métricas y Observabilidad

El sistema registra:
- Queries procesadas por agente
- Tasa de éxito/error
- Tiempo de respuesta
- Keywords detectadas
- Scores de activación

Ver estadísticas en el tab "🔧 Administración".

## 🔧 Configuración Avanzada

### Variables de Entorno (.env)

```env
# Modelos
SIMPLE_MODEL=gpt-4o-mini
COMPLEX_MODEL=gpt-4o
DEFAULT_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-large

# Precios por modelo (opcional)
MODEL_PRICES={"gpt-4o":0.02,"gpt-4o-mini":0.01}

# RAG
CHUNK_SIZE=1500
CHUNK_OVERLAP=300
MAX_DOCUMENTS=10

# UI
SERVER_PORT=8080
SHARE_GRADIO=true
```

### Configuración de Keywords (config/agent_keywords.json)

```json
{
  "agents": {
    "DocumentSearchAgent": {
      "capabilities": {
        "DOCUMENT_SEARCH": {
          "keywords": ["search", "find", "buscar", "encontrar"],
          "enabled": true,
          "weight": 1.0
        }
      },
      "threshold": 0.3,
      "enabled": true
    }
  }
}
```

**Parámetros clave:**
- `threshold`: Score mínimo para activar el agente (0.0 - 1.0)
- `keywords`: Lista de palabras que activan la capacidad
- `enabled`: Habilitar/deshabilitar capacidad o agente
- `weight`: Peso de la capacidad (para futuras mejoras)

## 🐛 Troubleshooting

### Error de API Key
- Verifica que `OPENAI_API_KEY` esté configurada
- Asegúrate de tener créditos en OpenAI

### No encuentra documentos
- Coloca archivos en `data/documents/`
- Formatos soportados: PDF, TXT, DOCX, XLS/XLSX

### Error de inicialización
- Revisa logs en `logs/app.log`
- Verifica permisos de escritura

### Panel de Keywords no aparece
1. Ve a "⚙️ Administración"
2. Presiona "🚀 Inicializar Sistema"
3. El tab "🔧 Administración" aparecerá automáticamente

### Los cambios de keywords no se aplican
1. Presiona "🔄 Recargar Configuración"
2. Verifica que veas el mensaje de confirmación
3. Prueba nuevamente con una query

### Puerto ocupado
- El launcher usa un puerto libre automáticamente
- Si usas `main.py`, cambia `SERVER_PORT` en `.env`

### Agente no se activa
1. Ve al tab "🔧 Administración"
2. Prueba tu query en "🧪 Prueba de Activación"
3. Verifica el score vs threshold
4. Agrega keywords relevantes o ajusta threshold

## 📚 Documentación Adicional

### Módulo de Administración de Keywords
- **Documentación Técnica**: `docs/technical/HU2_KEYWORD_ADMIN_COMPLETADO.md`
- **Guía Rápida**: `docs/guides/QUICKSTART_KEYWORD_ADMIN.md`
- **Resumen Visual**: `docs/technical/KEYWORD_ADMIN_VISUAL_SUMMARY.md`

### Sistema de Agentes
- **Ejemplos de Queries**: `docs/guides/EJEMPLOS_QUERIES_AGENTES.md`
- **Demo de Resultados**: `docs/technical/DEMO_AGENTES_RESULTADO.md`
- **Progreso de Desarrollo**: `docs/development/AGENT_DEVELOPMENT_PROGRESS.md`

### Guías de Uso
- **Cómo Ejecutar**: `docs/guides/COMO_EJECUTAR_LA_APP.md`
- **Índice de Documentación**: `DOCUMENTACION_FINAL.md`

### Tests
```bash
# Test completo del sistema de keywords
python tests/test_keyword_admin.py

# Test de activación de agentes
python tests/test_agent_activation.py

# Test de estadísticas de agentes
python tests/test_agentstats.py
```

## 🎯 Roadmap

### Completado ✅
- [x] Sistema RAG base
- [x] Arquitectura de agentes
- [x] DocumentSearchAgent
- [x] Sistema de fallback
- [x] Registro de agentes
- [x] Administración de keywords
- [x] Panel de administración UI
- [x] Soporte multiidioma
- [x] Backups automáticos

### En Desarrollo 🚧
- [ ] ComparisonAgent (análisis comparativo)
- [ ] StateOfArtAgent (síntesis de estado del arte)
- [ ] Sistema de memoria conversacional
- [ ] Orquestador multi-agente
- [ ] Optimización de performance

### Futuro 🔮
- [ ] API REST para gestión remota
- [ ] Machine learning para optimización automática
- [ ] A/B testing de configuraciones
- [ ] Analytics avanzados
- [ ] Más agentes especializados

## 🤝 Contribuciones

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

MIT License - ver LICENSE para detalles.

## 🙏 Agradecimientos

- LangChain por el framework RAG
- OpenAI por los modelos de lenguaje
- Gradio por la interfaz web
- La comunidad open source

---

**Versión**: 2.0.0 (con Sistema de Agentes y Administración de Keywords)  
**Última Actualización**: 2025-10-03

![image](https://github.com/user-attachments/assets/8b4079ef-83f8-43d4-8b1f-6d4411c837cd)
![image](https://github.com/user-attachments/assets/a7684860-7773-43fc-8287-336298720e8e)


