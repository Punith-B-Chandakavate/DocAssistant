# """
# CLI + library for ingesting documents into the vector store.

# Usage:
#     python ingest.py path/to/file.pdf
#     python ingest.py path/to/folder/
#     python ingest.py --reset
#     python ingest.py --list
# """
# import sys
# import hashlib
# from pathlib import Path

# from config import SUPPORTED_EXTENSIONS
# from extractors import (
#     extract_pdf,
#     extract_text_file,
#     extract_image,
#     extract_notebook,
#     chunk_pages,
# )
# from vectorstore import VectorStore


# def _hash_file(path: Path) -> str:
#     h = hashlib.sha256()
#     with open(path, "rb") as f:
#         for block in iter(lambda: f.read(65536), b""):
#             h.update(block)
#     return h.hexdigest()


# def extract_any(path: Path):
#     ext = path.suffix.lower()

#     if ext == ".pdf":
#         yield from extract_pdf(path)
#     elif ext in (".png", ".jpg", ".jpeg", ".webp"):
#         yield from extract_image(path)
#     elif ext == ".ipynb":
#         yield from extract_notebook(path)
#     elif ext in SUPPORTED_EXTENSIONS:
#         yield from extract_text_file(path)


# def ingest_file(store: VectorStore, path: Path) -> int:
#     if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
#         print(f"  ↳ skipped (unsupported): {path.name}")
#         return 0

#     file_hash = _hash_file(path)
#     pages = list(extract_any(path))
#     if not pages:
#         print(f"  ↳ no text extracted: {path.name}")
#         return 0

#     chunks = chunk_pages(pages)
#     added = store.add_chunks(
#         source=str(path.resolve()),
#         chunks=chunks,
#         file_hash=file_hash,
#     )
#     if added == 0:
#         print(f"  ↳ already ingested (unchanged): {path.name}")
#     else:
#         print(f"  ↳ +{added} chunks: {path.name}")
#     return added


# def ingest_path(store: VectorStore, target: Path) -> int:
#     total = 0
#     if target.is_file():
#         total += ingest_file(store, target)
#     elif target.is_dir():
#         for p in sorted(target.rglob("*")):
#             if not p.is_file():
#                 continue
#             if "db" in p.parts:          # skip data/db/**
#                 continue
#             total += ingest_file(store, p)
#     return total


# def main():
#     store = VectorStore()

#     if len(sys.argv) < 2:
#         print(__doc__)
#         return

#     arg = sys.argv[1]

#     if arg == "--reset":
#         store.reset()
#         print("Vector store reset.")
#         return

#     if arg == "--list":
#         sources = store.list_sources()
#         print(f"Collection contains {store.count()} chunks from {len(sources)} files:")
#         for s in sources:
#             print(f"  - {s}")
#         return

#     total = 0
#     for p in sys.argv[1:]:
#         print(f"Ingesting: {p}")
#         total += ingest_path(store, Path(p))

#     print(f"\nDone. Added {total} new chunks. Total in store: {store.count()}")


# if __name__ == "__main__":
#     main()



import sys
import hashlib
from pathlib import Path

from config import SUPPORTED_EXTENSIONS
from extractors import (
    extract_pdf,
    extract_text_file,
    extract_image,
    extract_notebook,
    chunk_pages,
)
from vectorstore import VectorStore


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def extract_any(path: Path):
    ext = path.suffix.lower()
    if ext == ".pdf":
        yield from extract_pdf(path)
    elif ext in (".png", ".jpg", ".jpeg", ".webp"):
        yield from extract_image(path)
    elif ext == ".ipynb":
        yield from extract_notebook(path)
    elif ext in SUPPORTED_EXTENSIONS:
        yield from extract_text_file(path)


def ingest_file(store: VectorStore, path: Path) -> int:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        print(f"  ↳ skipped (unsupported): {path.name}")
        return 0

    file_hash = _hash_file(path)
    pages = list(extract_any(path))
    if not pages:
        print(f"  ↳ no text extracted: {path.name}")
        return 0

    chunks = chunk_pages(pages)
    added = store.add_chunks(
        source=str(path.resolve()),
        chunks=chunks,
        file_hash=file_hash,
    )
    if added == 0:
        print(f"  ↳ already ingested (unchanged): {path.name}")
    else:
        print(f"  ↳ +{added} chunks: {path.name}")
    return added


def ingest_path(store: VectorStore, target: Path) -> int:
    total = 0
    if target.is_file():
        total += ingest_file(store, target)
    elif target.is_dir():
        for p in sorted(target.rglob("*")):
            if not p.is_file():
                continue
            if "db" in p.parts:  # skip data/db/**
                continue
            total += ingest_file(store, p)
    else:
        print(f"Not found: {target}")
    return total


def main():
    store = VectorStore()

    if len(sys.argv) < 2:
        print(__doc__)
        return

    arg = sys.argv[1]

    if arg == "--reset":
        store.reset()
        print("Vector store reset.")
        return

    if arg == "--list":
        sources = store.list_sources()
        print(f"Collection contains {store.count()} chunks from {len(sources)} files:")
        for s in sources:
            print(f"  - {s}")
        return

    total = 0
    for p in sys.argv[1:]:
        print(f"Ingesting: {p}")
        total += ingest_path(store, Path(p))

    print(f"\nDone. Added {total} new chunks. Total in store: {store.count()}")


if __name__ == "__main__":
    main()