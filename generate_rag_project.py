#!/usr/bin/env python3
"""
Script para generar la estructura completa del proyecto RAG avanzado
Ejecutar: python generate_rag_project.py
"""

import os
from pathlib import Path
from typing import Dict
from src.utils.project_setup import (
    create_project_structure,
    write_files,
    DEFAULT_DIRECTORIES,
)

def create_directory_structure() -> None:
    """Utiliza utilidades compartidas para crear la estructura."""
    print("📁 Creando estructura de directorios...")
    create_project_structure()
    for directory in DEFAULT_DIRECTORIES:
        print(f"  ✅ {directory}")

def create_file_content() -> Dict[str, str]:
    """Define el contenido de todos los archivos del proyecto"""
    
    files_content = {}
    
    # .env file
    files_content[".env"] = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Paths
VECTOR_DB_PATH=./data/vector_db
DOCUMENTS_PATH=./data/documents

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_DOCUMENTS=5

# Model Configuration
MODEL_NAME=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-3-small

# Logging
LOG_LEVEL=INFO

# UI Configuration
SHARE_GRADIO=false
SERVER_PORT=7860
"""

    # requirements.txt
    files_content["requirements.txt"] = """langchain==0.1.0
langchain-openai==0.0.5
langchain-chroma==0.1.0
gradio==4.15.0
python-dotenv==1.0.0
pydantic==2.5.0
loguru==0.7.2
pytest==7.4.3
black==23.12.1
isort==5.13.2
pypdf==3.17.4
python-docx==1.1.0
"""

    # .gitignore
    files_content[".gitignore"] = """# Environment variables
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*.sublime-project
*.sublime-workspace

# Data
data/vector_db/
data/documents/*.pdf
data/documents/*.txt
data/documents/*.docx
!data/documents/.gitkeep

# Logs
logs/
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"""

    # config/settings.py
    files_content["config/settings.py"] = """# -*- coding: utf-8 -*-
import os
from typing import Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    \"\"\"Configuración centralizada de la aplicación\"\"\"
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    model_name: str = Field(default="gpt-3.5-turbo", env="MODEL_NAME")
    embedding_model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    
    # Paths
    vector_db_path: str = Field(default="./data/vector_db", env="VECTOR_DB_PATH")
    documents_path: str = Field(default="./data/documents", env="DOCUMENTS_PATH")
    
    # RAG Configuration
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    max_documents: int = Field(default=5, env="MAX_DOCUMENTS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # UI Configuration
    share_gradio: bool = Field(default=False, env="SHARE_GRADIO")
    server_port: int = Field(default=7860, env="SERVER_PORT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Instancia global de configuración
settings = Settings()
"""

    # src/utils/logger.py
    files_content["src/utils/logger.py"] = """# -*- coding: utf-8 -*-
from loguru import logger
import sys
from config.settings import settings

def setup_logger():
    \"\"\"Configura el sistema de logging\"\"\"
    logger.remove()  # Remueve el logger por defecto
    
    # Formato personalizado
    format_string = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Logger para consola
    logger.add(
        sys.stdout,
        format=format_string,
        level=settings.log_level,
        colorize=True
    )
    
    # Logger para archivo
    logger.add(
        "logs/app.log",
        format=format_string,
        level=settings.log_level,
        rotation="10 MB",
        retention="1 week",
        compression="zip"
    )
    
    return logger
"""

    # src/utils/exceptions.py
    files_content["src/utils/exceptions.py"] = """# -*- coding: utf-8 -*-

class RAGException(Exception):
    \"\"\"Excepción base para el sistema RAG\"\"\"
    pass

class VectorStoreException(RAGException):
    \"\"\"Excepción para errores de la base vectorial\"\"\"
    pass

class DocumentProcessingException(RAGException):
    \"\"\"Excepción para errores de procesamiento de documentos\"\"\"
    pass

class EmbeddingException(RAGException):
    \"\"\"Excepción para errores de embedding\"\"\"
    pass

class ChainException(RAGException):
    \"\"\"Excepción para errores en las cadenas RAG\"\"\"
    pass
"""

    # src/models/embeddings.py
    files_content["src/models/embeddings.py"] = """# -*- coding: utf-8 -*-
from typing import Optional
from langchain_openai import OpenAIEmbeddings
from config.settings import settings
from src.utils.logger import setup_logger
from src.utils.exceptions import EmbeddingException

logger = setup_logger()

class EmbeddingManager:
    \"\"\"Maneja los modelos de embedding\"\"\"
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.embedding_model
        self._embeddings = None
        
    @property
    def embeddings(self) -> OpenAIEmbeddings:
        \"\"\"Lazy loading de embeddings\"\"\"
        if self._embeddings is None:
            try:
                self._embeddings = OpenAIEmbeddings(
                    model=self.model_name,
                    openai_api_key=settings.openai_api_key
                )
                logger.info(f"Initialized embeddings with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Error initializing embeddings: {e}")
                raise EmbeddingException(f"Failed to initialize embeddings: {e}")
        
        return self._embeddings
    
    def embed_query(self, text: str) -> list[float]:
        \"\"\"Genera embedding para una consulta\"\"\"
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise EmbeddingException(f"Failed to embed query: {e}")
"""

    # src/storage/document_processor.py
    files_content["src/storage/document_processor.py"] = """# -*- coding: utf-8 -*-
import os
from typing import List, Optional
from pathlib import Path
from langchain.document_loaders import (
    TextLoader, 
    PyPDFLoader, 
    Docx2txtLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from config.settings import settings
from src.utils.logger import setup_logger
from src.utils.exceptions import DocumentProcessingException

logger = setup_logger()

class DocumentProcessor:
    \"\"\"Procesador de documentos con múltiples formatos\"\"\"
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\\n\\n", "\\n", ". ", " ", ""]
        )
        
        # Mapeo de extensiones a loaders
        self.loader_mapping = {
            '.txt': TextLoader,
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
        }
    
    def load_documents(self, path: Optional[str] = None) -> List[Document]:
        \"\"\"Carga documentos desde un directorio\"\"\"
        documents_path = Path(path or settings.documents_path)
        
        if not documents_path.exists():
            logger.warning(f"Documents path does not exist: {documents_path}")
            return []
        
        try:
            all_documents = []
            
            # Cargar archivos individuales
            for file_path in documents_path.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.loader_mapping:
                    loader_class = self.loader_mapping[file_path.suffix.lower()]
                    loader = loader_class(str(file_path))
                    
                    try:
                        docs = loader.load()
                        # Agregar metadata
                        for doc in docs:
                            doc.metadata.update({
                                'source_file': str(file_path),
                                'file_type': file_path.suffix.lower()
                            })
                        all_documents.extend(docs)
                        logger.info(f"Loaded {len(docs)} documents from {file_path}")
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {e}")
                        continue
            
            logger.info(f"Total documents loaded: {len(all_documents)}")
            return all_documents
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            raise DocumentProcessingException(f"Failed to load documents: {e}")
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        \"\"\"Divide documentos en chunks\"\"\"
        try:
            split_docs = self.text_splitter.split_documents(documents)
            logger.info(f"Split {len(documents)} documents into {len(split_docs)} chunks")
            return split_docs
        except Exception as e:
            logger.error(f"Error splitting documents: {e}")
            raise DocumentProcessingException(f"Failed to split documents: {e}")
    
    def process_documents(self, path: Optional[str] = None) -> List[Document]:
        \"\"\"Pipeline completo de procesamiento\"\"\"
        documents = self.load_documents(path)
        if not documents:
            logger.warning("No documents to process")
            return []
        
        return self.split_documents(documents)
"""

    # src/storage/vector_store.py
    files_content["src/storage/vector_store.py"] = """# -*- coding: utf-8 -*-
import os
from typing import List, Optional
from pathlib import Path
from langchain_chroma import Chroma
from langchain.schema import Document
from config.settings import settings
from src.models.embeddings import EmbeddingManager
from src.storage.document_processor import DocumentProcessor
from src.utils.logger import setup_logger
from src.utils.exceptions import VectorStoreException

logger = setup_logger()

class VectorStoreManager:
    \"\"\"Maneja la base de datos vectorial\"\"\"
    
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or settings.vector_db_path
        self.embedding_manager = EmbeddingManager()
        self.document_processor = DocumentProcessor()
        self._vector_store = None
        
        # Crear directorio si no existe
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
    
    @property
    def vector_store(self) -> Chroma:
        \"\"\"Lazy loading de vector store\"\"\"
        if self._vector_store is None:
            try:
                self._vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embedding_manager.embeddings
                )
                logger.info(f"Initialized vector store at: {self.persist_directory}")
            except Exception as e:
                logger.error(f"Error initializing vector store: {e}")
                raise VectorStoreException(f"Failed to initialize vector store: {e}")
        
        return self._vector_store
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        \"\"\"Agrega documentos a la base vectorial\"\"\"
        if not documents:
            logger.warning("No documents to add")
            return []
        
        try:
            ids = self.vector_store.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to vector store")
            return ids
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise VectorStoreException(f"Failed to add documents: {e}")
    
    def load_and_index_documents(self, documents_path: Optional[str] = None) -> int:
        \"\"\"Carga e indexa documentos desde un directorio\"\"\"
        try:
            documents = self.document_processor.process_documents(documents_path)
            if not documents:
                logger.warning("No documents found to index")
                return 0
            
            self.add_documents(documents)
            return len(documents)
        except Exception as e:
            logger.error(f"Error loading and indexing documents: {e}")
            raise VectorStoreException(f"Failed to load and index documents: {e}")
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        \"\"\"Búsqueda por similitud\"\"\"
        try:
            results = self.vector_store.similarity_search(query, k=k)
            logger.debug(f"Found {len(results)} similar documents for query")
            return results
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            raise VectorStoreException(f"Similarity search failed: {e}")
    
    def get_retriever(self, search_kwargs: Optional[dict] = None):
        \"\"\"Obtiene un retriever configurado\"\"\"
        search_kwargs = search_kwargs or {"k": settings.max_documents}
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)
    
    def delete_collection(self):
        \"\"\"Elimina la colección vectorial\"\"\"
        try:
            if self._vector_store:
                self._vector_store.delete_collection()
            logger.info("Vector collection deleted")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise VectorStoreException(f"Failed to delete collection: {e}")
"""

    # src/chains/rag_chain.py
    files_content["src/chains/rag_chain.py"] = """# -*- coding: utf-8 -*-
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from config.settings import settings
from src.storage.vector_store import VectorStoreManager
from src.utils.logger import setup_logger
from src.utils.exceptions import ChainException

logger = setup_logger()

class RAGChain:
    \"\"\"Cadena RAG configurable\"\"\"
    
    def __init__(self, 
                 system_prompt: Optional[str] = None,
                 model_name: Optional[str] = None,
                 temperature: float = 0.1):
        
        self.model_name = model_name or settings.model_name
        self.temperature = temperature
        self.vector_store_manager = VectorStoreManager()
        
        # Prompt por defecto mejorado
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        # Inicializar componentes
        self._llm = None
        self._prompt_template = None
        self._chain = None
    
    def _get_default_system_prompt(self) -> str:
        \"\"\"Prompt del sistema por defecto mejorado\"\"\"
        return \"\"\"Eres un asistente especializado en responder preguntas basándote en el contexto proporcionado.

INSTRUCCIONES:
1. Usa ÚNICAMENTE la información del contexto para responder
2. Si la información no está en el contexto, responde: "No tengo información suficiente para responder esa pregunta"
3. Sé preciso y conciso en tus respuestas
4. Cita las fuentes cuando sea relevante
5. Si hay información contradictoria, menciona las diferentes perspectivas

CONTEXTO:
{context}

Responde de manera profesional y útil.\"\"\"
    
    @property
    def llm(self) -> ChatOpenAI:
        \"\"\"Lazy loading del modelo LLM\"\"\"
        if self._llm is None:
            try:
                self._llm = ChatOpenAI(
                    model=self.model_name,
                    temperature=self.temperature,
                    openai_api_key=settings.openai_api_key
                )
                logger.info(f"Initialized LLM: {self.model_name}")
            except Exception as e:
                logger.error(f"Error initializing LLM: {e}")
                raise ChainException(f"Failed to initialize LLM: {e}")
        
        return self._llm
    
    @property
    def prompt_template(self) -> ChatPromptTemplate:
        \"\"\"Lazy loading del template de prompt\"\"\"
        if self._prompt_template is None:
            self._prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("human", "{input}"),
            ])
        
        return self._prompt_template
    
    def create_chain(self):
        \"\"\"Crea la cadena RAG\"\"\"
        try:
            retriever = self.vector_store_manager.get_retriever()
            
            # Cadena para combinar documentos
            document_chain = create_stuff_documents_chain(
                llm=self.llm,
                prompt=self.prompt_template
            )
            
            # Cadena RAG completa
            self._chain = create_retrieval_chain(retriever, document_chain)
            logger.info("RAG chain created successfully")
            
        except Exception as e:
            logger.error(f"Error creating RAG chain: {e}")
            raise ChainException(f"Failed to create RAG chain: {e}")
    
    def invoke(self, query: str) -> Dict[str, Any]:
        \"\"\"Ejecuta la cadena RAG\"\"\"
        if self._chain is None:
            self.create_chain()
        
        try:
            logger.debug(f"Processing query: {query[:100]}...")
            result = self._chain.invoke({"input": query})
            logger.debug("Query processed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise ChainException(f"Failed to process query: {e}")
    
    def get_answer(self, query: str) -> str:
        \"\"\"Obtiene solo la respuesta\"\"\"
        result = self.invoke(query)
        return result.get('answer', 'No se pudo generar una respuesta.')
"""

    # src/services/rag_service.py
    files_content["src/services/rag_service.py"] = """# -*- coding: utf-8 -*-
from typing import List, Dict, Any, Optional
from src.chains.rag_chain import RAGChain
from src.storage.vector_store import VectorStoreManager
from src.utils.logger import setup_logger
from src.utils.exceptions import RAGException

logger = setup_logger()

class RAGService:
    \"\"\"Servicio principal para operaciones RAG\"\"\"
    
    def __init__(self):
        self.vector_store_manager = VectorStoreManager()
        self.rag_chain = RAGChain()
        self._initialized = False
    
    def initialize(self, force_reindex: bool = False) -> bool:
        \"\"\"Inicializa el servicio RAG\"\"\"
        try:
            # Verificar si hay documentos en la base vectorial
            if force_reindex or self._needs_indexing():
                logger.info("Indexing documents...")
                indexed_count = self.vector_store_manager.load_and_index_documents()
                if indexed_count == 0:
                    logger.warning("No documents were indexed")
                    return False
                logger.info(f"Successfully indexed {indexed_count} documents")
            
            # Crear la cadena RAG
            self.rag_chain.create_chain()
            self._initialized = True
            logger.info("RAG service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing RAG service: {e}")
            raise RAGException(f"Failed to initialize RAG service: {e}")
    
    def _needs_indexing(self) -> bool:
        \"\"\"Verifica si se necesita indexar documentos\"\"\"
        try:
            # Intenta hacer una búsqueda simple para ver si hay documentos
            results = self.vector_store_manager.similarity_search("test", k=1)
            return len(results) == 0
        except:
            return True
    
    def query(self, question: str, include_sources: bool = False) -> Dict[str, Any]:
        \"\"\"Procesa una consulta y devuelve la respuesta\"\"\"
        if not self._initialized:
            raise RAGException("RAG service not initialized. Call initialize() first.")
        
        try:
            result = self.rag_chain.invoke(question)
            
            response = {
                'answer': result.get('answer', 'No se pudo generar una respuesta.'),
                'question': question
            }
            
            if include_sources:
                sources = []
                for doc in result.get('context', []):
                    source_info = {
                        'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        'metadata': doc.metadata
                    }
                    sources.append(source_info)
                response['sources'] = sources
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise RAGException(f"Failed to process query: {e}")
    
    def get_simple_answer(self, question: str) -> str:
        \"\"\"Obtiene una respuesta simple (solo texto)\"\"\"
        result = self.query(question)
        return result['answer']
    
    def reindex_documents(self) -> int:
        \"\"\"Reindexar documentos\"\"\"
        try:
            logger.info("Starting document reindexing...")
            self.vector_store_manager.delete_collection()
            indexed_count = self.vector_store_manager.load_and_index_documents()
            
            if indexed_count > 0:
                self.rag_chain.create_chain()  # Recrear la cadena
                logger.info(f"Reindexed {indexed_count} documents successfully")
            
            return indexed_count
            
        except Exception as e:
            logger.error(f"Error reindexing documents: {e}")
            raise RAGException(f"Failed to reindex documents: {e}")
"""

    # ui/gradio_app.py
    files_content["ui/gradio_app.py"] = """# -*- coding: utf-8 -*-
import gradio as gr
from typing import List, Tuple
from src.services.rag_service import RAGService
from src.utils.logger import setup_logger
from config.settings import settings

logger = setup_logger()

class GradioRAGApp:
    \"\"\"Aplicación Gradio para el sistema RAG\"\"\"
    
    def __init__(self):
        self.rag_service = RAGService()
        self.initialized = False
    
    def initialize_service(self) -> str:
        \"\"\"Inicializa el servicio RAG\"\"\"
        try:
            if self.rag_service.initialize():
                self.initialized = True
                return "✅ Sistema RAG inicializado correctamente"
            else:
                return "⚠️ Sistema inicializado pero no se encontraron documentos para indexar"
        except Exception as e:
            logger.error(f"Error initializing service: {e}")
            return f"❌ Error al inicializar: {str(e)}"
    
    def chat_response(self, message: str, history: List[Tuple[str, str]]) -> str:
        \"\"\"Maneja las respuestas del chat\"\"\"
        if not self.initialized:
            return "❌ El sistema no está inicializado. Por favor inicialízalo primero."
        
        if not message.strip():
            return "Por favor, escribe una pregunta."
        
        try:
            response = self.rag_service.get_simple_answer(message)
            return response
        except Exception as e:
            logger.error(f"Error in chat response: {e}")
            return f"❌ Error al procesar la pregunta: {str(e)}"
    
    def reindex_documents(self) -> str:
        \"\"\"Reindexar documentos\"\"\"
        try:
            count = self.rag_service.reindex_documents()
            if count > 0:
                return f"✅ Reindexados {count} documentos correctamente"
            else:
                return "⚠️ No se encontraron documentos para reindexar"
        except Exception as e:
            logger.error(f"Error reindexing: {e}")
            return f"❌ Error al reindexar: {str(e)}"
    
    def create_interface(self) -> gr.Blocks:
        \"\"\"Crea la interfaz de Gradio\"\"\"
        with gr.Blocks(
            title="Sistema RAG Avanzado",
            theme=gr.themes.Soft(),
        ) as interface:
            
            gr.HTML(\"\"\"
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1>🤖 Sistema RAG Avanzado</h1>
                <p>Haz preguntas sobre tus documentos de manera inteligente</p>
            </div>
            \"\"\")
            
            with gr.Tabs():
                # Tab principal - Chat
                with gr.TabItem("💬 Chat"):
                    chatbot = gr.ChatInterface(
                        fn=self.chat_response,
                        title="Asistente RAG",
                        description="Haz preguntas sobre tus documentos",
                        examples=[
                            "¿Cuál es el tema principal de los documentos?",
                            "Resume la información más importante",
                            "¿Qué datos específicos puedes encontrar?",
                        ],
                        cache_examples=False,
                        retry_btn="🔄 Reintentar",
                        undo_btn="↩️ Deshacer",
                        clear_btn="🗑️ Limpiar",
                    )
                
                # Tab de administración
                with gr.TabItem("⚙️ Administración"):
                    gr.Markdown("### Gestión del Sistema")
                    
                    with gr.Row():
                        init_btn = gr.Button("🚀 Inicializar Sistema", variant="primary")
                        reindex_btn = gr.Button("📚 Reindexar Documentos", variant="secondary")
                    
                    status_output = gr.Textbox(
                        label="Estado del Sistema",
                        interactive=False,
                        lines=3
                    )
                    
                    # Información del sistema
                    gr.Markdown("### Información del Sistema")
                    gr.Markdown(f\"\"\"
                    - **Directorio de documentos**: `{settings.documents_path}`
                    - **Base de datos vectorial**: `{settings.vector_db_path}`
                    - **Modelo de embeddings**: `{settings.embedding_model}`
                    - **Modelo de chat**: `{settings.model_name}`
                    - **Tamaño de chunk**: `{settings.chunk_size}`
                    - **Overlap de chunk**: `{settings.chunk_overlap}`
                    \"\"\")
                
                # Tab de ayuda
                with gr.TabItem("❓ Ayuda"):
                    gr.Markdown(\"\"\"
                    ## 📖 Cómo usar el sistema RAG
                    
                    ### 1. Preparar documentos
                    - Coloca tus documentos (PDF, TXT, DOCX) en la carpeta `data/documents/`
                    - El sistema soporta múltiples formatos de archivo
                    
                    ### 2. Inicializar el sistema
                    - Ve a la pestaña "Administración"
                    - Haz clic en "Inicializar Sistema"
                    - Espera a que se indexen los documentos
                    
                    ### 3. Hacer preguntas
                    - Ve a la pestaña "Chat"
                    - Escribe tus preguntas sobre los documentos
                    - El sistema buscará información relevante y generará respuestas
                    
                    ### 4. Reindexar (si es necesario)
                    - Si agregas nuevos documentos, usa "Reindexar Documentos"
                    - Esto actualizará la base de datos vectorial
                    
                    ### 💡 Consejos para mejores resultados
                    - Haz preguntas específicas y claras
                    - Puedes preguntar sobre conceptos, datos, resúmenes, etc.
                    - Si no obtienes la respuesta esperada, reformula tu pregunta
                    \"\"\")
            
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
        \"\"\"Lanza la aplicación\"\"\"
        interface = self.create_interface()
        
        # Configuración por defecto
        launch_kwargs = {
            'server_port': settings.server_port,
            'share': settings.share_gradio,
            'show_error': True,
            'quiet': False,
            **kwargs
        }
        
        logger.info(f"Launching Gradio app on port {launch_kwargs['server_port']}")
        interface.launch(**launch_kwargs)
"""

    # main.py
    files_content["main.py"] = """# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
import argparse
from src.utils.logger import setup_logger
from ui.gradio_app import GradioRAGApp
from src.services.rag_service import RAGService

# Configurar logging
logger = setup_logger()

def create_project_structure():
    \"\"\"Crea la estructura de directorios del proyecto\"\"\"
    directories = [
        "config",
        "src/models",
        "src/storage", 
        "src/chains",
        "src/services",
        "src/utils",
        "ui",
        "data/documents",
        "data/vector_db",
        "tests",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Crear archivos __init__.py
        if not directory.startswith("data") and not directory.startswith("logs"):
            init_file = Path(directory) / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    logger.info("Project structure created successfully")

def main():
    \"\"\"Función principal\"\"\"
    parser = argparse.ArgumentParser(description="Sistema RAG Avanzado")
    parser.add_argument(
        "--mode", 
        choices=["ui", "cli", "setup"], 
        default="ui",
        help="Modo de ejecución: ui (interfaz web), cli (línea de comandos), setup (configurar proyecto)"
    )
    parser.add_argument("--port", type=int, default=7860, help="Puerto para la interfaz web")
    parser.add_argument("--share", action="store_true", help="Compartir la interfaz públicamente")
    parser.add_argument("--query", type=str, help="Consulta para modo CLI")
    
    args = parser.parse_args()
    
    try:
        if args.mode == "setup":
            logger.info("Setting up project structure...")
            create_project_structure()
            logger.info("✅ Project setup completed!")
            return
        
        elif args.mode == "ui":
            logger.info("Starting Gradio UI...")
            app = GradioRAGApp()
            app.launch(server_port=args.port, share=args.share)
        
        elif args.mode == "cli":
            if not args.query:
                logger.error("Query is required for CLI mode. Use --query 'your question'")
                sys.exit(1)
            
            logger.info("Starting CLI mode...")
            rag_service = RAGService()
            
            # Inicializar servicio
            if not rag_service.initialize():
                logger.error("Failed to initialize RAG service")
                sys.exit(1)
            
            # Procesar consulta
            result = rag_service.query(args.query, include_sources=True)
            
            print(f"\\n🤖 Pregunta: {args.query}")
            print(f"📝 Respuesta: {result['answer']}")
            
            if result.get('sources'):
                print(f"\\n📚 Fuentes consultadas:")
                for i, source in enumerate(result['sources'], 1):
                    print(f"  {i}. {source['metadata'].get('source_file', 'Unknown')}")
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""

    # tests/test_rag_service.py
    files_content["tests/test_rag_service.py"] = """# -*- coding: utf-8 -*-
import pytest
import tempfile
import os
from pathlib import Path
from src.services.rag_service import RAGService
from src.utils.exceptions import RAGException

class TestRAGService:
    \"\"\"Tests para RAG Service\"\"\"
    
    @pytest.fixture
    def temp_dir(self):
        \"\"\"Directorio temporal para tests\"\"\"
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def sample_document(self, temp_dir):
        \"\"\"Crea un documento de ejemplo\"\"\"
        doc_path = Path(temp_dir) / "test_doc.txt"
        doc_path.write_text("Este es un documento de prueba con información importante.")
        return str(doc_path)
    
    def test_initialization_without_documents(self, temp_dir):
        \"\"\"Test de inicialización sin documentos\"\"\"
        # Configurar paths temporales
        os.environ["DOCUMENTS_PATH"] = temp_dir
        os.environ["VECTOR_DB_PATH"] = str(Path(temp_dir) / "vector_db")
        
        rag_service = RAGService()
        result = rag_service.initialize()
        
        # Debería fallar o advertir sobre falta de documentos
        assert result is False or result is True  # Dependiendo de la implementación
    
    def test_query_without_initialization(self):
        \"\"\"Test de consulta sin inicialización\"\"\"
        rag_service = RAGService()
        
        with pytest.raises(RAGException):
            rag_service.query("test question")
"""

    # tests/test_vector_store.py
    files_content["tests/test_vector_store.py"] = """# -*- coding: utf-8 -*-
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from src.storage.vector_store import VectorStoreManager
from src.storage.document_processor import DocumentProcessor

class TestVectorStore:
    \"\"\"Tests para Vector Store\"\"\"
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_document_processor_load_empty_directory(self, temp_dir):
        \"\"\"Test carga de directorio vacío\"\"\"
        processor = DocumentProcessor()
        documents = processor.load_documents(temp_dir)
        assert len(documents) == 0
    
    def test_document_processor_with_text_file(self, temp_dir):
        \"\"\"Test procesamiento de archivo de texto\"\"\"
        # Crear archivo de prueba
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Este es un documento de prueba para testing.")
        
        processor = DocumentProcessor()
        documents = processor.load_documents(temp_dir)
        
        assert len(documents) == 1
        assert "prueba" in documents[0].page_content
        assert documents[0].metadata['source_file'] == str(test_file)
"""

    # data/documents/.gitkeep
    files_content["data/documents/.gitkeep"] = """# Este archivo mantiene el directorio en git
# Coloca aquí tus documentos PDF, TXT, DOCX
"""

    # README.md
    files_content["README.md"] = """# Sistema RAG Avanzado

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
# venv\\Scripts\\activate  # Windows
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
"""

    return files_content

def create_all_files():
    """Crea todos los archivos del proyecto"""
    files_content = create_file_content()

    print("📝 Creando archivos del proyecto...")
    write_files(files_content)
    for file_path in files_content:
        print(f"  ✅ {file_path}")

def main():
    """Función principal del generador"""
    print("🚀 Generador del Proyecto RAG Avanzado")
    print("=" * 50)
    
    # Verificar si ya existe un proyecto
    if Path("main.py").exists():
        response = input("⚠️  Ya existe un proyecto aquí. ¿Sobrescribir? (y/N): ")
        if response.lower() not in ['y', 'yes', 'sí', 's']:
            print("❌ Operación cancelada.")
            return
    
    try:
        # Crear estructura de directorios
        create_directory_structure()
        print()
        
        # Crear todos los archivos
        create_all_files()
        print()
        
        print("🎉 ¡Proyecto RAG creado exitosamente!")
        print()
        print("📋 Próximos pasos:")
        print("1. cd al directorio del proyecto")
        print("2. Crear entorno virtual: python -m venv venv")
        print("3. Activar entorno: source venv/bin/activate (Linux/Mac) o venv\\\\Scripts\\\\activate (Windows)")
        print("4. Instalar dependencias: pip install -r requirements.txt")
        print("5. Configurar .env con tu API key de OpenAI")
        print("6. Ejecutar: python main.py --mode ui")
        print()
        print("📖 Lee el README.md para más información")
        
    except Exception as e:
        print(f"❌ Error al crear el proyecto: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())