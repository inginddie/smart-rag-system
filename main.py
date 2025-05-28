# -*- coding: utf-8 -*-
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
    """Crea la estructura de directorios del proyecto"""
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
    """Función principal"""
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
            
            print(f"\n🤖 Pregunta: {args.query}")
            print(f"📝 Respuesta: {result['answer']}")
            
            if result.get('sources'):
                print(f"\n📚 Fuentes consultadas:")
                for i, source in enumerate(result['sources'], 1):
                    print(f"  {i}. {source['metadata'].get('source_file', 'Unknown')}")
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
