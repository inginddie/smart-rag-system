# Sistema RAG Avanzado
![image](https://github.com/user-attachments/assets/18a05e72-63bc-4ba0-8940-d4012af75a8e)

Un sistema completo de Retrieval-Augmented Generation (RAG) construido con Python, LangChain y Gradio.

## 🚀 Características

- **Múltiples formatos de documentos**: PDF, TXT, DOCX
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

### 4. Configurar API Key
Edita el archivo `.env` y agrega tu API key de OpenAI:
```env
OPENAI_API_KEY=tu_api_key_aqui
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

## 🔧 Configuración Avanzada

Personaliza la configuración en `.env`:

```env
# Modelos
MODEL_NAME=gpt-4
EMBEDDING_MODEL=text-embedding-3-large

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
- Formatos soportados: PDF, TXT, DOCX

### Error de inicialización
- Revisa logs en `logs/app.log`
- Verifica permisos de escritura

## 📝 Licencia

MIT License - ver LICENSE para detalles.
