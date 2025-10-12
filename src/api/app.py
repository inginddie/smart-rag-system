#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Application for Performance Monitoring
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.performance_routes import router as performance_router, set_workflow_engine
from src.agents.orchestration import WorkflowEngine
import logging

logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="RAG System Performance API",
    description="API para monitoreo de performance del sistema RAG",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas
app.include_router(performance_router)

# Instancia global del workflow engine
_workflow_engine = None


def initialize_workflow_engine():
    """Inicializa el workflow engine"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
        set_workflow_engine(_workflow_engine)
        logger.info("WorkflowEngine initialized for API")
    return _workflow_engine


def get_workflow_engine():
    """Obtiene la instancia del workflow engine"""
    if _workflow_engine is None:
        return initialize_workflow_engine()
    return _workflow_engine


@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info("Starting FastAPI Performance API...")
    initialize_workflow_engine()


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "RAG System Performance API",
        "version": "1.0.0",
        "endpoints": {
            "performance": "/api/performance",
            "docs": "/docs",
            "health": "/api/performance/health"
        }
    }


@app.get("/health")
async def health():
    """Health check general"""
    return {
        "status": "healthy",
        "service": "performance-api"
    }
