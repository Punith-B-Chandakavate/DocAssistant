from pathlib import Path
from typing import Iterator


def extract_text_file(path: str | Path) -> Iterator[tuple[int, str]]:
    """TXT/MD files: yield (1, full_text) as a single 'page'."""
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="ignore").strip()
    if text:
        yield 1, text