from pathlib import Path
from typing import Iterator
import pymupdf as fitz
from PIL import Image
import pytesseract
import io


def _ocr_page(page: fitz.Page) -> str:
    """Render page to image and OCR it."""
    pix = page.get_pixmap(dpi=200)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img)


def extract_pdf(path: str | Path) -> Iterator[tuple[int, str]]:
    """
    Yields (page_number_1indexed, text).
    Falls back to OCR if the page has no embedded text.
    """
    doc = fitz.open(str(path))
    for i, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if not text:
            try:
                text = _ocr_page(page).strip()
            except Exception as e:
                text = f"[OCR failed for page {i}: {e}]"
        if text:
            yield i, text
    doc.close()