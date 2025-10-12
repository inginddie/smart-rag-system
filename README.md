# Sistema RAG Avanzado con Orquestación Multi-Agente
![image](https://github.com/user-attachments/assets/18a05e72-63bc-4ba0-8940-d4012af75a8e)

Un sistema completo de Retrieval-Augmented Generation (RAG) con arquitectura de agentes especializados, orquestación inteligente y monitoreo de performance en tiempo real.

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
- **Tests unitarios completos** (50+ tests)

### 🤖 Sistema de Agentes Especializados
- **DocumentSearchAgent**: Búsqueda semántica avanzada y síntesis académica
- **Registro de Agentes**: Descubrimiento automático por capacidades
- **Sistema de Fallback**: Recuperación automática ante errores
- **Métricas y Observabilidad**: Estadísticas detalladas por agente
- **Activación Inteligente**: Selección automática del mejor agente

### 🎯 Orquestación Multi-Agente (NUEVO)
- **AgentSelector**: Selección inteligente basada en keywords y scoring
- **AgentOrchestrator**: Coordinación de múltiples agentes
- **WorkflowEngine**: Ejecución secuencial y paralela de workflows
- **Circuit Breakers**: Protección contra agentes lentos o fallidos
- **Load Balancer**: Distribución inteligente de carga (4 estrategias)
- **Performance Monitor**: Métricas detalladas con percentiles P50/P90/P95/P99

### 📊 Dashboard de Performance (NUEVO)
- **Panel en Gradio**: 6 pestañas de visualización en tiempo real
- **API REST**: 10 endpoints con FastAPI y documentación Swagger
- **Métricas Globales**: Throughput, latencia, tasa de éxito
- **Alertas**: Detección automática de agentes lentos o con fallos
- **Gestión de Circuit Breakers**: Reset manual desde el UI
- **Exportación**: Reportes JSON completos

### 🔧 Administración de Keywords
- **Gestión Dinámica**: Agregar/eliminar keywords sin código
- **Pruebas en Tiempo Real**: Verificar activación de agentes con queries
- **Configuración de Threshold**: Ajustar sensibilidad de activación
- **Soporte Multiidioma**: Keywords en español e inglés
- **Persistencia Segura**: Backups automáticos de configuración
- **Panel de Administración**: Interfaz intuitiva en Gradio

### 💾 Sistema de Memoria Conversacional
- **Memoria por Sesión**: Contexto persistente entre consultas
- **Gestión de Sesiones**: Crear, listar, cambiar y eliminar sesiones
- **Historial Completo**: Ver conversaciones pasadas
- **Exportación**: Descargar historial en JSON
- **Integración Transparente**: Funciona con todos los agentes

## 📦 Instalación Rápida

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd RAG
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
# Copia el template de configuración
cp .env.template .env

# Edita .env y configura tu API key de OpenAI
# OPENAI_API_KEY=tu_api_key_aqui
```

### 5. Lanzar la aplicación

#### Opción A: UI + API (Recomendado)
```bash
python launch_with_api.py
```
Acceder a:
- **Gradio UI**: http://localhost:7860
- **Performance API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

#### Opción B: Solo UI
```bash
python launch_with_api.py --ui-only
```

#### Opción C: Solo API
```bash
python launch_with_api.py --api-only
```

## 🎯 Uso Rápido

### Inicio Básico
1. **Coloca documentos** en `data/documents/`
2. **Lanza la aplicación**: `python launch_with_api.py`
3. **Abre** el navegador en http://localhost:7860
4. **Inicializa** el sistema en la pestaña "⚙️ Administración"
5. **Haz preguntas** en la pestaña "💬 Chat Académico"

### 📊 Dashboard de Performance (Nuevo)
1. **Ve a la pestaña** "📊 Performance"
2. **Explora las 6 secciones**:
   - 📈 Métricas Globales
   - 🤖 Agentes
   - 🔌 Circuit Breakers
   - ⚠️ Alertas
   - ⚖️ Load Balancer
   - 📋 Reporte JSON
3. **Click en "🔄 Actualizar"** para ver métricas en tiempo real
4. **Gestiona circuit breakers** con reset manual si es necesario

### 🔧 Gestión de Keywords
1. **Ve al tab** "🔧 Administración"
2. **Prueba queries** en tiempo real
3. **Agrega keywords** por capacidad
4. **Ajusta threshold** según necesites
5. **Exporta/importa** configuraciones

### 🌐 API REST
```bash
# Métricas globales
curl http://localhost:8000/api/performance/metrics

# Reporte completo
curl http://localhost:8000/api/performance/report

# Health check
curl http://localhost:8000/api/performance/health

# Documentación interactiva
# Abrir: http://localhost:8000/docs
```

## 📁 Estructura del Proyecto

```
RAG/
├── src/
│   ├── agents/
│   │   ├── base/                # Agentes base y registro
│   │   └── orchestration/       # Sistema de orquestación (NUEVO)
│   │       ├── selector.py      # Selector de agentes
│   │       ├── orchestrator.py  # Orquestador principal
│   │       ├── workflow.py      # Motor de workflows
│   │       ├── circuit_breaker.py    # Circuit breakers
│   │       ├── load_balancer.py      # Balanceador de carga
│   │       └── performance_monitor.py # Monitor de performance
│   ├── api/                     # API REST (NUEVO)
│   │   ├── app.py              # Aplicación FastAPI
│   │   └── performance_routes.py # Rutas de performance
│   ├── services/               # Servicios principales
│   ├── memory/                 # Sistema de memoria
│   └── utils/                  # Utilidades
├── ui/
│   ├── components/
│   │   ├── admin_panel.py      # Panel de administración
│   │   ├── memory_panel.py     # Panel de memoria
│   │   └── performance_panel.py # Panel de performance (NUEVO)
│   └── gradio_app.py           # Aplicación Gradio
├── tests/
│   └── agents/
│       ├── test_orchestrator.py # Tests de orquestación
│       ├── test_workflow.py     # Tests de workflows
│       └── test_performance_optimization.py # Tests de performance
├── docs/                        # Documentación completa
│   ├── PERFORMANCE_UI_GUIDE.md
│   ├── INTEGRACION_PERFORMANCE_UI.md
│   ├── QUICKSTART_PERFORMANCE.md
│   └── DEMO_PERFORMANCE_DASHBOARD.md
├── config/                      # Configuración
│   ├── agent_keywords.json      # Keywords de agentes
│   └── backups/                 # Backups automáticos
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




## 🎯 Sistema de Orquestación Multi-Agente

### Componentes Principales

#### 1. AgentSelector
Selecciona el agente más apropiado basándose en keywords y scoring:
- Análisis de query con keywords configurables
- Sistema de scoring con umbral ajustable
- Fallback automático a agente general
- Tracking de decisiones

#### 2. AgentOrchestrator
Coordina la ejecución de múltiples agentes:
- Integración con selector y workflow engine
- Gestión de contexto y sesiones
- Métricas de ejecución
- Manejo de errores robusto

#### 3. WorkflowEngine
Motor de ejecución de workflows:
- **Ejecución secuencial**: Agentes en orden
- **Ejecución paralela**: Múltiples agentes simultáneos
- **Síntesis de resultados**: Combina respuestas de múltiples agentes
- **Detección automática**: Identifica queries que requieren múltiples agentes

#### 4. Circuit Breakers
Protección contra agentes problemáticos:
- **Estados**: CLOSED (normal), OPEN (bloqueado), HALF_OPEN (recuperación)
- **Configuración flexible**: Umbrales personalizables
- **Métricas detalladas**: Tracking de llamadas y fallos
- **Reset manual**: Desde UI o API

#### 5. Load Balancer
Distribución inteligente de carga:
- **4 Estrategias**: Round Robin, Least Connections, Weighted Response Time, Random
- **Load Score**: Basado en conexiones, latencia y tasa de éxito
- **Agentes saludables**: Identificación automática
- **Cambio dinámico**: Ajuste de estrategia en tiempo real

#### 6. Performance Monitor
Monitoreo detallado de performance:
- **Métricas por agente**: Latencia, throughput, tasa de éxito
- **Percentiles**: P50, P90, P95, P99
- **Detección de problemas**: Agentes lentos o con fallos
- **Reportes completos**: Exportación JSON

### Métricas y Umbrales

| Métrica | Bueno | Atención | Crítico |
|---------|-------|----------|---------|
| Success Rate | > 95% | 80-95% | < 80% |
| Latencia | < 2s | 2-5s | > 5s |
| Tasa de Fallos | < 5% | 5-10% | > 10% |

### Uso del Dashboard

```bash
# Iniciar aplicación con UI + API
python launch_with_api.py

# Acceder al dashboard
# http://localhost:7860 → Pestaña "📊 Performance"

# API REST
# http://localhost:8000/docs
```

## 📚 Documentación Completa

### Guías Disponibles

1. **HU5_SISTEMA_ORQUESTACION_COMPLETO.md** - Documentación completa del sistema
2. **docs/QUICKSTART_PERFORMANCE.md** - Inicio rápido (5 minutos)
3. **docs/PERFORMANCE_UI_GUIDE.md** - Guía completa de uso
4. **docs/INTEGRACION_PERFORMANCE_UI.md** - Documentación técnica
5. **docs/DEMO_PERFORMANCE_DASHBOARD.md** - Demo funcional

### Tests

```bash
# Tests completos de orquestación
pytest tests/agents/test_workflow.py tests/agents/test_orchestrator.py tests/agents/test_performance_optimization.py -v

# Resultado: 50/50 tests passed ✅
```

## 🎓 Ejemplos de Uso

### Monitoreo de Performance

```python
import requests

# Verificar salud del sistema
response = requests.get('http://localhost:8000/api/performance/health')
data = response.json()

if data['status'] == 'healthy':
    print("✅ Sistema saludable")
else:
    print(f"⚠️ Sistema degradado: {data}")
```

### Detección de Agentes Lentos

```python
# Obtener agentes lentos (> 3 segundos)
response = requests.get(
    'http://localhost:8000/api/performance/slow-agents',
    params={'threshold_ms': 3000}
)
data = response.json()

if data['data']['count'] > 0:
    print(f"⚠️ {data['data']['count']} agentes lentos detectados")
```

### Reset de Circuit Breaker

```python
# Resetear circuit breaker después de resolver problema
agent_name = "QueryAgent"
response = requests.post(
    f'http://localhost:8000/api/performance/circuit-breakers/{agent_name}/reset'
)
print(response.json()['message'])
```

## 🚀 Características Avanzadas

### Ejecución Paralela de Agentes

El sistema detecta automáticamente queries que requieren múltiples agentes:

```python
# Query que activa múltiples agentes
query = "Busca documentos sobre IA y analiza las metodologías"

# El sistema:
# 1. Detecta que requiere DocumentSearchAgent y AnalysisAgent
# 2. Los ejecuta en paralelo
# 3. Sintetiza los resultados
# 4. Retorna respuesta unificada
```

### Circuit Breakers Automáticos

Protección automática contra agentes problemáticos:

```python
# Si un agente falla 5 veces consecutivas:
# 1. Circuit breaker se abre (OPEN)
# 2. Requests son rechazadas automáticamente
# 3. Después de 60 segundos, intenta recuperación (HALF_OPEN)
# 4. Si tiene éxito, vuelve a normal (CLOSED)
```

### Load Balancing Inteligente

Distribución basada en métricas reales:

```python
# El load balancer considera:
# - Conexiones activas del agente
# - Tiempo de respuesta promedio
# - Tasa de éxito reciente
# - Load score calculado

# Selecciona automáticamente el agente más apropiado
```

## 🔧 Configuración Avanzada

### Circuit Breakers

```python
# En src/agents/orchestration/circuit_breaker.py
@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5      # Fallos antes de abrir
    success_threshold: int = 2      # Éxitos para cerrar
    timeout: float = 60.0           # Segundos antes de intentar recovery
    slow_call_threshold: float = 10.0  # Umbral de llamada lenta
```

### Load Balancer

```python
# Cambiar estrategia de balanceo
from src.agents.orchestration import LoadBalancingStrategy

workflow_engine.load_balancer.change_strategy(
    LoadBalancingStrategy.LEAST_CONNECTIONS
)
```

## 🐛 Troubleshooting

### Puerto en uso

```bash
# Si el puerto 8000 está en uso, usar otro:
python launch_with_api.py --api-port 8001
```

### Panel de Performance vacío

**Solución**: Ejecutar algunas consultas primero para generar métricas.

### Circuit Breaker siempre OPEN

**Solución**:
1. Revisar logs en `logs/app.log`
2. Corregir problema del agente
3. Resetear circuit breaker desde el UI

## 📊 Estado del Proyecto

| Componente | Estado | Tests | Docs |
|------------|--------|-------|------|
| Sistema RAG Base | ✅ | ✅ | ✅ |
| Agentes Especializados | ✅ | ✅ | ✅ |
| Orquestación Multi-Agente | ✅ | ✅ | ✅ |
| Circuit Breakers | ✅ | ✅ | ✅ |
| Load Balancer | ✅ | ✅ | ✅ |
| Performance Monitor | ✅ | ✅ | ✅ |
| Dashboard Gradio | ✅ | N/A | ✅ |
| API REST | ✅ | N/A | ✅ |
| Sistema de Memoria | ✅ | ✅ | ✅ |
| Administración Keywords | ✅ | ✅ | ✅ |

**Total**: 10/10 componentes ✅ | 50+ tests ✅ | Documentación completa ✅

## 🎉 Conclusión

Sistema RAG completo con:
- ✅ Orquestación multi-agente inteligente
- ✅ Monitoreo de performance en tiempo real
- ✅ Circuit breakers y load balancing
- ✅ Dashboard interactivo (Gradio + FastAPI)
- ✅ Sistema de memoria conversacional
- ✅ Administración dinámica de keywords
- ✅ Tests exhaustivos (50+ tests)
- ✅ Documentación completa

**Para empezar**:
```bash
python launch_with_api.py
```

Luego abre http://localhost:7860 y explora todas las funcionalidades.

## 📞 Soporte

- **Documentación**: Ver carpeta `docs/`
- **Tests**: `pytest tests/agents/ -v`
- **Logs**: `logs/app.log`
- **Issues**: Crear issue en el repositorio

## 📄 Licencia

MIT License - Ver archivo LICENSE para más detalles.

---

**Desarrollado con ❤️ para investigación académica en IA**
