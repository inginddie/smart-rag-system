# -*- coding: utf-8 -*-
from pathlib import Path

from src.storage.document_processor import DocumentProcessor, Document


class FakeParser:
    """Minimal parser used for testing injection and OCR metadata."""

    def __init__(self, needs_ocr_return=False):
        self.needs_ocr_return = needs_ocr_return
        self.parse_calls = []

    def parse(self, path, lang="spa+eng"):
        self.parse_calls.append((path, lang))
        return [Document(page_content="content", metadata={"ocr": True, "ocr_lang": lang})]

    def needs_ocr(self, path):
        return self.needs_ocr_return


def test_image_uses_parser(tmp_path):
    img = tmp_path / "test.jpg"
    img.write_bytes(b"fake")

    parser = FakeParser()
    processor = DocumentProcessor(parser=parser)
    docs = processor.load_documents(str(tmp_path))

    assert parser.parse_calls[0][0] == str(img)
    assert docs[0].metadata["ocr"] is True
    assert docs[0].metadata["ocr_lang"] == "spa+eng"


def test_pdf_with_ocr(tmp_path):
    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    parser = FakeParser(needs_ocr_return=True)
    processor = DocumentProcessor(parser=parser)
    docs = processor.load_documents(str(tmp_path))

    assert parser.parse_calls[0][0] == str(pdf)
    assert docs[0].metadata["ocr"] is True
    assert docs[0].metadata["ocr_lang"] == "spa+eng"
