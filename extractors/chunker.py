from typing import Iterable
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_pages(
    pages: Iterable[tuple[int, str]],
) -> list[dict]:
    """
    Input: iterable of (page_number, text)
    Output: list of chunks: {"text": ..., "page": ..., "chunk_index": ...}
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for page_num, text in pages:
        for i, piece in enumerate(splitter.split_text(text)):
            piece = piece.strip()
            if piece:
                chunks.append(
                    {"text": piece, "page": page_num, "chunk_index": i}
                )
    return chunks