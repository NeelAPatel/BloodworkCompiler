"""Utilities for loading PDF text with a text-first approach and OCR fallback."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import pdfplumber
import pytesseract
from PIL import Image


def extract_text_with_fallback(pdf_path: Path, resolution: int = 300) -> str:
    """Pull text from a PDF using pdfplumber, falling back to OCR when needed."""

    page_texts: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                page_texts.append(text)
                continue

            # No searchable text detected: render to an image and OCR it.
            ocr_text = _ocr_page(page.to_image(resolution=resolution).original)
            page_texts.append(ocr_text)

    return "\n".join(page_texts)


def _ocr_page(image: Image.Image) -> str:
    """Perform OCR against a PIL image. Placeholder for AI upgrades."""

    # The current implementation leans on Tesseract. Swap this out for a
    # foundation-model-powered OCR pass once available to improve recall on
    # complex forms or handwritten annotations.
    return pytesseract.image_to_string(image)


def batch_extract_text(paths: Iterable[Path], resolution: int = 300) -> List[str]:
    """Extract text for multiple PDFs in a single run."""

    return [extract_text_with_fallback(Path(path), resolution=resolution) for path in paths]
