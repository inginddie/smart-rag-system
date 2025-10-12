#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher para la aplicación con Gradio UI y FastAPI Performance API
"""

import os
import sys
import argparse
import threading
import uvicorn
from src.utils.logger import setup_logger
from ui.gradio_app import GradioRAGApp
from src.api.app import app as fastapi_app, initialize_workflow_engine
from config.settings import settings

logger = setup_logger()


def run_fastapi(host: str = "0.0.0.0", port: int = 8000):
    """Ejecuta el servidor FastAPI"""
    try:
        logger.info(f"Starting FastAPI Performance API on {host}:{port}")
        uvicorn.run(fastapi_app, host=host, port=port, log_level="info")
    except Exception as e:
        logger.error(f"Error starting FastAPI: {e}")
        raise


def run_gradio(port: int = 7860, share: bool = False):
    """Ejecuta la aplicación Gradio"""
    logger.info(f"Starting Gradio UI on port {port}")
    app = GradioRAGApp()
    app.launch(server_port=port, share=share)


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Sistema RAG con UI Gradio y API de Performance"
    )
    parser.add_argument(
        "--gradio-port",
        type=int,
        default=7860,
        help="Puerto para Gradio UI (default: 7860)"
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8000,
        help="Puerto para FastAPI (default: 8000)"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Compartir Gradio públicamente"
    )
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Solo ejecutar FastAPI (sin Gradio)"
    )
    parser.add_argument(
        "--ui-only",
        action="store_true",
        help="Solo ejecutar Gradio (sin FastAPI)"
    )
    
    args = parser.parse_args()
    
    # Verificar API key
    if not settings.openai_api_key:
        logger.error(
            "OpenAI API key missing. Set OPENAI_API_KEY in your environment or .env file."
        )
        sys.exit(1)
    
    try:
        logger.info("=" * 60)
        logger.info("🚀 Iniciando Sistema RAG Avanzado")
        logger.info("=" * 60)
        
        if args.api_only:
            # Solo FastAPI
            logger.info("Modo: Solo API")
            initialize_workflow_engine()
            run_fastapi(port=args.api_port)
        
        elif args.ui_only:
            # Solo Gradio
            logger.info("Modo: Solo UI")
            run_gradio(port=args.gradio_port, share=args.share)
        
        else:
            # Ambos servicios
            logger.info("Modo: UI + API")
            
            # Inicializar workflow engine
            initialize_workflow_engine()
            
            # Ejecutar FastAPI en un thread separado
            api_thread = threading.Thread(
                target=run_fastapi,
                kwargs={"port": args.api_port},
                daemon=True
            )
            api_thread.start()
            
            logger.info(f"✅ FastAPI iniciado en http://localhost:{args.api_port}")
            logger.info(f"📊 Performance API: http://localhost:{args.api_port}/api/performance")
            logger.info(f"📚 API Docs: http://localhost:{args.api_port}/docs")
            
            # Ejecutar Gradio en el thread principal
            logger.info(f"✅ Iniciando Gradio UI en http://localhost:{args.gradio_port}")
            run_gradio(port=args.gradio_port, share=args.share)
    
    except KeyboardInterrupt:
        logger.info("\n👋 Aplicación interrumpida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error en la aplicación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
