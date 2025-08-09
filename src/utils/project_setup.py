# -*- coding: utf-8 -*-
"""Utilities to programmatically create the project structure and files."""
from pathlib import Path
from typing import Dict, Iterable

from src.utils.logger import setup_logger

logger = setup_logger()

DEFAULT_DIRECTORIES = [
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
    "logs",
]


def create_project_structure(directories: Iterable[str] = DEFAULT_DIRECTORIES) -> None:
    """Create base folders and ``__init__.py`` files."""
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

        if not directory.startswith("data") and not directory.startswith("logs"):
            init_file = Path(directory) / "__init__.py"
            if not init_file.exists():
                init_file.touch()

    logger.info("Project structure created successfully")


def write_files(files: Dict[str, str]) -> None:
    """Create files from a ``path`` -> ``content`` mapping."""
    for file_path, content in files.items():
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Created file: {file_path}")
