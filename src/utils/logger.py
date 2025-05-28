# -*- coding: utf-8 -*-
from loguru import logger
import sys
from config.settings import settings

def setup_logger():
    """Configura el sistema de logging"""
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
