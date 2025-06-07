# -*- coding: utf-8 -*-
try:
    from loguru import logger
    _using_loguru = True
except ImportError:  # pragma: no cover - fallback if loguru is missing
    import logging
    logger = logging.getLogger(__name__)
    _using_loguru = False

import sys
from config.settings import settings

def setup_logger():
    """Configura el sistema de logging"""
    if _using_loguru:
        logger.remove()

        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

        logger.add(
            sys.stdout,
            format=format_string,
            level=settings.log_level,
            colorize=True,
        )

        logger.add(
            "logs/app.log",
            format=format_string,
            level=settings.log_level,
            rotation="10 MB",
            retention="1 week",
            compression="zip",
        )
    else:
        logging.basicConfig(level=settings.log_level)

    return logger
