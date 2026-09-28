# from pathlib import Path
# from typing import Iterator
# import base64
# from PIL import Image
# import pytesseract

# from llm.client import get_openai_client
# from config import CHAT_MODEL


# def _ocr_image(path: Path) -> str:
#     return pytesseract.image_to_string(Image.open(path)).strip()


# def _vision_caption(path: Path) -> str:
#     """Use GPT-4o-mini vision to describe the image."""
#     client = get_openai_client()
#     b64 = base64.b64encode(path.read_bytes()).decode()
#     # infer mime
#     ext = path.suffix.lower().lstrip(".")
#     mime = "jpeg" if ext in ("jpg", "jpeg") else ext

#     resp = client.chat.completions.create(
#         model=CHAT_MODEL,
#         messages=[
#             {
#                 "role": "user",
#                 "content": [
#                     {
#                         "type": "text",
#                         "text": (
#                             "Describe this image in detail. If it contains text, "
#                             "transcribe all visible text verbatim. If it's a chart, "
#                             "diagram, or table, describe its structure and content."
#                         ),
#                     },
#                     {
#                         "type": "image_url",
#                         "image_url": {"url": f"data:image/{mime};base64,{b64}"},
#                     },
#                 ],
#             }
#         ],
#         temperature=0,
#     )
#     return resp.choices[0].message.content.strip()


# def extract_image(path: str | Path) -> Iterator[tuple[int, str]]:
#     """
#     Yields (1, text) for an image.
#     Combines OCR (verbatim text) + vision caption (semantic description).
#     """
#     p = Path(path)
#     try:
#         ocr_text = _ocr_image(p)
#     except Exception:
#         ocr_text = ""

#     try:
#         caption = _vision_caption(p)
#     except Exception as e:
#         caption = f"[Vision caption failed: {e}]"

#     combined = ""
#     if ocr_text:
#         combined += f"OCR TEXT:\n{ocr_text}\n\n"
#     if caption:
#         combined += f"IMAGE DESCRIPTION:\n{caption}"

#     if combined.strip():
#         yield 1, combined.strip()

from pathlib import Path
from typing import Iterator
from PIL import Image
import pytesseract

# Windows Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_image(path: str | Path) -> Iterator[tuple[int, str]]:
    p = Path(path)
    try:
        text = pytesseract.image_to_string(Image.open(p)).strip()
    except Exception as e:
        text = f"[OCR failed for {p.name}: {e}]"
    if text:
        yield 1, text