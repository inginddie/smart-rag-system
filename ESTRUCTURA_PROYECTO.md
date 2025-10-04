# 🏗️ Estructura del Proyecto RAG con Agentes

## 📁 Árbol de Directorios Completo

```
RAG/
│
├── 📄 README.md                        # Documentación principal
├── 📄 CHANGELOG.md                     # Historial de cambios
├── 📄 DOCUMENTACION_FINAL.md          # Índice de documentación
├── 📄 CONTRIBUTING.md                  # Guía de contribución
├── 📄 SECURITY.md                      # Políticas de seguridad
├── 📄 LICENSE                          # Licencia MIT
│
├── 🚀 launch_app.py                    # Launcher principal (RECOMENDADO)
├── 🚀 main.py                          # Entry point alternativo
├── 🔧 generate_rag_project.py         # Generador del proyecto
│
├── 📋 requirements.txt                 # Dependencias de producción
├── 📋 requirements-dev.txt             # Dependencias de desarrollo
├── 📋 config.template                  # Template de configuración
├── 📋 .env.template                    # Template de variables de entorno
│
├── 🐳 Dockerfile                       # Configuración Docker
├── 🐳 docker-compose.yml              # Docker Compose
├── 🐳 .dockerignore                   # Exclusiones Docker
│
├── 📚 docs/                            # 📚 DOCUMENTACIÓN
│   │
│   ├── 📖 guides/                      # Guías de usuario
│   │   ├── COMO_EJECUTAR_LA_APP.md    # 🚀 Guía de ejecución
│   │   ├── QUICKSTART_KEYWORD_ADMIN.md # ⚡ Inicio rápido keywords
│   │   └── EJEMPLOS_QUERIES_AGENTES.md # 💬 Ejemplos de queries
│   │
│   ├── 🔧 technical/                   # Documentación técnica
│   │   ├── HU2_KEYWORD_ADMIN_COMPLETADO.md # 📘 Doc técnica keywords
│   │   ├── KEYWORD_ADMIN_VISUAL_SUMMARY.md # 🎨 Resumen visual
│   │   └── DEMO_AGENTES_RESULTADO.md  # 🎯 Demos de agentes
│   │
│   └── 👨‍💻 development/                 # Documentación de desarrollo
│       ├── AGENT_DEVELOPMENT_PROGRESS.md # 🤖 Progreso de agentes
│       └── DEVELOPMENT_LOG.md         # 📋 Log de desarrollo
│
├── 💻 src/                             # 💻 CÓDIGO FUENTE
│   │
│   ├── 🔧 admin/                       # Módulo de administración
│   │   ├── __init__.py
│   │   ├── keyword_manager.py         # Gestor de keywords
│   │   └── keyword_storage.py         # Persistencia de keywords
│   │
│   ├── 🤖 agents/                      # Sistema de agentes
│   │   ├── __init__.py
│   │   │
│   │   ├── base/                       # Arquitectura base
│   │   │   ├── __init__.py
│   │   │   ├── agent.py               # BaseAgent abstracto
│   │   │   ├── registry.py            # Registro de agentes
│   │   │   ├── fallback.py            # Sistema de fallback
│   │   │   └── exceptions.py          # Excepciones personalizadas
│   │   │
│   │   └── specialized/                # Agentes especializados
│   │       ├── __init__.py
│   │       └── document_search.py     # DocumentSearchAgent
│   │
│   ├── 🔗 chains/                      # Cadenas RAG
│   │   ├── __init__.py
│   │   └── rag_chain.py
│   │
│   ├── 🧠 models/                      # Modelos de embedding
│   │   ├── __init__.py
│   │   └── embedding_model.py
│   │
│   ├── 🎭 orchestration/               # Orquestación
│   │   ├── __init__.py
│   │   └── template_orchestrator.py
│   │
│   ├── 🔌 services/                    # Servicios de negocio
│   │   ├── __init__.py
│   │   └── rag_service.py             # Servicio principal RAG
│   │
│   ├── 💾 storage/                     # Almacenamiento
│   │   ├── __init__.py
│   │   ├── document_processor.py
│   │   └── vector_store.py
│   │
│   └── 🛠️ utils/                       # Utilidades
│       ├── __init__.py
│       ├── logger.py
│       ├── exceptions.py
│       ├── faq_manager.py
│       ├── metrics.py
│       ├── query_advisor.py
│       ├── query_validator.py
│       ├── refinement_suggester.py
│       ├── usage_analytics.py
│       └── ... (otros utils)
│
├── 🎨 ui/                              # 🎨 INTERFAZ DE USUARIO
│   ├── __init__.py
│   │
│   ├── components/                     # Componentes UI
│   │   ├── __init__.py
│   │   └── admin_panel.py             # Panel de administración
│   │
│   └── gradio_app.py                  # Aplicación Gradio principal
│
├── 🧪 tests/                           # 🧪 TESTS
│   │
│   ├── agents/                         # Tests de agentes
│   │   ├── __init__.py
│   │   ├── test_base_agent.py
│   │   ├── test_registry.py
│   │   ├── test_fallback.py
│   │   └── test_document_search_agent.py
│   │
│   ├── test_keyword_admin.py          # Tests de keywords
│   ├── test_agent_activation.py       # Tests de activación
│   └── test_agentstats.py             # Tests de estadísticas
│
├── ⚙️ config/                          # ⚙️ CONFIGURACIÓN
│   ├── agent_keywords.json            # Keywords de agentes
│   │
│   └── backups/                        # Backups automáticos
│       └── agent_keywords_*.json
│
├── 📊 data/                            # 📊 DATOS
│   ├── documents/                      # Documentos para RAG
│   ├── vector_db/                      # Base de datos vectorial
│   └── traces.db                       # Trazas de LLM
│
├── 📝 logs/                            # 📝 LOGS
│   └── app.log                         # Logs de la aplicación
│
├── 🔧 scripts/                         # 🔧 SCRIPTS
│   ├── export_daily_cost.py
│   └── ... (otros scripts)
│
├── 🔐 .kiro/                           # 🔐 CONFIGURACIÓN KIRO
│   ├── settings/
│   └── specs/
│       └── agentic-rag-completion/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
│
├── 🐍 .venv/                           # Entorno virtual Python
├── 🐍 venv/                            # Entorno virtual alternativo
│
└── 🔒 .git/                            # Control de versiones Git
```

---

## 📊 Resumen por Categoría

### 📚 Documentación (13 archivos)
- **Raíz**: 5 archivos (README, CHANGELOG, etc.)
- **docs/guides**: 3 guías de usuario
- **docs/technical**: 3 documentos técnicos
- **docs/development**: 2 documentos de desarrollo

### 💻 Código Fuente (src/)
- **admin**: 2 archivos (keyword management)
- **agents**: 6 archivos (base + specialized)
- **chains**: 1 archivo
- **models**: 1 archivo
- **orchestration**: 1 archivo
- **services**: 1 archivo
- **storage**: 2 archivos
- **utils**: 10+ archivos

### 🎨 Interfaz (ui/)
- **components**: 1 archivo (admin_panel)
- **Aplicación principal**: 1 archivo (gradio_app)

### 🧪 Tests (tests/)
- **agents**: 4 archivos
- **Raíz**: 3 archivos (keyword, activation, stats)

### ⚙️ Configuración
- **config**: 1 archivo + backups
- **Raíz**: 4 archivos de configuración

---

## 🎯 Archivos Clave por Función

### Para Ejecutar
```
launch_app.py              # ⭐ RECOMENDADO
main.py                    # Alternativo
```

### Para Documentarse
```
README.md                  # ⭐ Inicio aquí
DOCUMENTACION_FINAL.md     # Índice completo
docs/guides/               # Guías de uso
```

### Para Desarrollar
```
src/                       # Código fuente
tests/                     # Tests
docs/development/          # Docs de desarrollo
```

### Para Administrar
```
docs/guides/QUICKSTART_KEYWORD_ADMIN.md
docs/technical/HU2_KEYWORD_ADMIN_COMPLETADO.md
ui/components/admin_panel.py
```

---

## 📈 Estadísticas del Proyecto

### Líneas de Código (aproximado)
- **Código fuente (src/)**: ~5,000 líneas
- **Tests**: ~1,500 líneas
- **UI**: ~800 líneas
- **Documentación**: ~3,000 líneas
- **Total**: ~10,300 líneas

### Archivos por Tipo
- **Python (.py)**: ~40 archivos
- **Markdown (.md)**: 13 archivos
- **Configuración**: 6 archivos
- **Total**: ~59 archivos principales

### Módulos Principales
- **Sistema RAG Base**: ✅ Completo
- **Sistema de Agentes**: ✅ Completo
- **Administración de Keywords**: ✅ Completo
- **Interfaz Gradio**: ✅ Completo
- **Tests**: ✅ Completo

---

## 🚀 Navegación Rápida

### Quiero ejecutar la app
```
1. Ver: docs/guides/COMO_EJECUTAR_LA_APP.md
2. Ejecutar: python launch_app.py
```

### Quiero gestionar keywords
```
1. Ver: docs/guides/QUICKSTART_KEYWORD_ADMIN.md
2. Abrir: Tab "🔧 Administración" en la UI
```

### Quiero entender el código
```
1. Ver: docs/technical/
2. Explorar: src/
3. Revisar: tests/
```

### Quiero contribuir
```
1. Ver: CONTRIBUTING.md
2. Ver: docs/development/
3. Crear: Pull Request
```

---

**Versión**: 2.0.0  
**Última Actualización**: 2025-10-03  
**Estado**: ✅ ORGANIZADO Y DOCUMENTADO
