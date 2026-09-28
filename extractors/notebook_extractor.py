# from pathlib import Path
# from typing import Iterator
# import json


# def extract_notebook(path: str | Path) -> Iterator[tuple[int, str]]:
#     """Extract cell contents from a Jupyter notebook.
#     Yields (cell_index, text) as a pseudo 'page'."""
#     p = Path(path)
#     try:
#         nb = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
#     except Exception as e:
#         return

#     for i, cell in enumerate(nb.get("cells", [])):
#         cell_type = cell.get("cell_type", "")
#         source = "".join(cell.get("source", []))
#         if not source.strip():
#             continue

#         text = f"[{cell_type.upper()} CELL]\n{source.strip()}"

#         # Include outputs for code cells (helps with dataframes/results)
#         if cell_type == "code":
#             outputs = cell.get("outputs", [])
#             out_text = []
#             for o in outputs:
#                 if "text" in o:
#                     out_text.append("".join(o["text"]))
#                 elif "data" in o and "text/plain" in o["data"]:
#                     out_text.append("".join(o["data"]["text/plain"]))
#             if out_text:
#                 text += "\n\n[OUTPUT]\n" + "\n".join(out_text)

#         yield i + 1, text


from pathlib import Path
from typing import Iterator
import json


def extract_notebook(path: str | Path) -> Iterator[tuple[int, str]]:
    p = Path(path)
    try:
        nb = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return

    for i, cell in enumerate(nb.get("cells", [])):
        cell_type = cell.get("cell_type", "")
        source = "".join(cell.get("source", []))
        if not source.strip():
            continue

        text = f"[{cell_type.upper()} CELL]\n{source.strip()}"

        if cell_type == "code":
            outputs = cell.get("outputs", [])
            out_text = []
            for o in outputs:
                if "text" in o:
                    out_text.append("".join(o["text"]))
                elif "data" in o and "text/plain" in o["data"]:
                    out_text.append("".join(o["data"]["text/plain"]))
            if out_text:
                text += "\n\n[OUTPUT]\n" + "\n".join(out_text)

        yield i + 1, text