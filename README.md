# Sistema RAG Avanzado
<img width="1262" height="588" alt="image" src="https://github.com/user-attachments/assets/fda14722-44a3-43c1-ad50-3eeacf34300c" />


Un sistema completo de Retrieval-Augmented Generation (RAG) construido con Python, LangChain y Gradio.

## 🚀 Características

- **Múltiples formatos de documentos**: PDF, TXT, DOCX, XLS/XLSX
- **Soporte para datos en PostgreSQL**
- **Interfaz web intuitiva** con Gradio
- **Modo CLI** para consultas por línea de comandos
- **Sistema de logging avanzado**
- **Configuración centralizada** con variables de entorno
- **Manejo robusto de errores**
- **Arquitectura modular y escalable**
- **Tests unitarios incluidos**

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

> **Nota:** Para el procesamiento OCR se requiere tener instalado **Tesseract OCR** en el sistema (`sudo apt install tesseract-ocr` en Debian/Ubuntu, `brew install tesseract` en macOS).

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

1. **Coloca documentos** en `data/documents/`
2. **Abre** http://localhost:7860
3. **Inicializa** el sistema en la pestaña "Administración"
4. **Haz preguntas** en la pestaña "Chat"

## 📁 Estructura del Proyecto

```
rag_system/
├── config/           # Configuración
├── src/
│   ├── models/       # Modelos de embedding
│   ├── storage/      # Base vectorial y procesamiento
│   ├── chains/       # Cadenas RAG
│   ├── services/     # Lógica de negocio
│   └── utils/        # Utilidades
├── ui/               # Interfaz Gradio
├── data/             # Datos y documentos
├── tests/            # Tests unitarios
└── logs/             # Archivos de log
```

## 🛠️ Comandos Útiles

### Interfaces
```bash
python main.py --mode ui        # Interfaz web
python main.py --mode cli --query "tu pregunta"  # CLI
python main.py --mode setup     # Configurar proyecto
```

### Testing
```bash
pytest tests/ -v
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

## 🔧 Configuración Avanzada

Personaliza la configuración en `.env`:

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

## 📝 Licencia

MIT License - ver LICENSE para detalles.
![image](https://github.com/user-attachments/assets/8b4079ef-83f8-43d4-8b1f-6d4411c837cd)
![image](https://github.com/user-attachments/assets/a7684860-7773-43fc-8287-336298720e8e)


