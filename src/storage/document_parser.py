# -*- coding: utf-8 -*-
"""Utilities for parsing documents using OCR when needed."""

from pathlib import Path
from typing import List

from src.utils.exceptions import DocumentProcessingException
from src.utils.logger import setup_logger

try:  # Optional dependency
    from langchain.schema import Document
except ImportError:  # pragma: no cover - fallback if langchain is missing
    from dataclasses import dataclass

    @dataclass
    class Document:  # type: ignore
        page_content: str
        metadata: dict

logger = setup_logger()


def needs_ocr(filepath: str) -> bool:
    """Determine if the file requires OCR.

    Returns ``True`` for images or PDF files without embedded text.
    """
    suffix = Path(filepath).suffix.lower()
    if suffix != ".pdf":
        return True

    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(filepath)
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                return False
        return True
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to inspect PDF %s: %s", filepath, exc)
        return True


def parse_image(path: str, lang: str) -> List[Document]:
    """OCR an image file using OpenCV preprocessing and pytesseract."""
    try:
        import cv2
        import numpy as np
        import pytesseract
    except ImportError as exc:  # pragma: no cover - dependencies are optional
        raise DocumentProcessingException("OCR dependencies are missing") from exc

    image = cv2.imread(path)
    if image is None:
        raise DocumentProcessingException(f"Unable to read image: {path}")

    # Deskew
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    coords = np.column_stack(np.where(gray > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    h, w = gray.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    image = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # Denoise
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)

    # Merge lines
    kernel = np.ones((1, 1), np.uint8)
    gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

    text = pytesseract.image_to_string(gray, lang=lang)

    return [
        Document(
            page_content=text,
            metadata={
                "source": path,
                "doc_type": "image",
                "page_number": 1,
                "section_title": None,
                "ocr": True,
                "ocr_lang": lang,
            },
        )
    ]


def parse_pdf(path: str, lang: str) -> List[Document]:
    """Parse a PDF file, applying OCR if necessary."""
    documents: List[Document] = []
    if not needs_ocr(path):
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(path)
            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": path,
                            "page_number": idx,
                            "section_title": None,
                            "doc_type": "pdf",
                            "ocr": False,
                        },
                    )
                )
            return documents
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Failed to read PDF %s: %s", path, exc)
            # Fallback to OCR

    try:
        from pdf2image import convert_from_path
    except ImportError as exc:
        raise DocumentProcessingException("pdf2image is required for PDF OCR") from exc

    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as tmpdir:
        images = convert_from_path(path)
        for idx, image in enumerate(images, start=1):
            img_path = f"{tmpdir}/page_{idx}.png"
            image.save(img_path, "PNG")
            doc = parse_image(img_path, lang)[0]
            doc.metadata["source"] = path
            doc.metadata["page_number"] = idx
            doc.metadata["section_title"] = None
            doc.metadata["doc_type"] = "pdf"
            documents.append(doc)

    return documents


def parse(path: str, lang: str = "spa+eng") -> List[Document]:
    """Parse an image or PDF and return a list of ``Document`` objects."""
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(path, lang)
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif"}:
        return parse_image(path, lang)
    raise DocumentProcessingException(f"Unsupported file type: {path}")
