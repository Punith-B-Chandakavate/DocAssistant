# 📚 DocAssistant — Personal AI Assistant for Your Documents

A local-first **RAG (Retrieval-Augmented Generation)** assistant that lets you ask natural-language questions across your own documents — PDFs, Markdown, text files, images, code, and Jupyter notebooks — and get grounded answers with **source + page citations**.

Built with:
- **Local embeddings** (`sentence-transformers`) — free, offline, private
- **Groq** (`llama-3.1` / `gpt-oss`) — free-tier LLM for generation
- **ChromaDB** — local vector database
- **Streamlit** — web UI
- **PyMuPDF + Tesseract** — PDF & image extraction

Everything runs on your machine except the LLM call. Documents never leave your computer.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📄 **Multi-format support** | PDF, TXT, MD, PNG/JPG/JPEG, `.py`, `.sql`, `.ipynb`, `.json`, `.yaml`, `.csv`, and more |
| 🔍 **Semantic search** | Local embeddings via `all-MiniLM-L6-v2` (80 MB, downloads once) |
| 🤖 **Answer generation** | Groq-hosted LLMs (`llama-3.1-8b-instant`, `gpt-oss-20b`, etc.) |
| 📚 **Source citations** | Every answer shows the exact file and page number used |
| 🚫 **No hallucination** | Refuses with *"I don't know based on the provided documents"* when the info isn't there |
| 🔒 **100% local storage** | Vector DB stored in `data/db/` — nothing leaves your machine except LLM calls |
| 💰 **Zero cost** | Groq free tier + local embeddings = $0 forever |
| 🖼️ **OCR for images** | Tesseract extracts text from screenshots, diagrams, scanned PDFs |
| 📓 **Notebook aware** | `.ipynb` files keep cell structure and code outputs |
| 🔁 **Incremental ingest** | Files are hashed — re-ingesting unchanged files is skipped automatically |

---

## 🗂️ Project Structure

```
docassistant/
├── data/                       # Your documents go here
│   ├── 1_SQL/
│   ├── 2_Python/
│   ├── 3_DE_Foundations_ETL_AWS/
│   ├── 4_Spark_Databricks/
│   ├── 5_Snowflake/
│   ├── 6_Airflow/
│   ├── Coding/
│   └── db/                     # ChromaDB storage (auto-created — don't edit)
├── extractors/                 # Document → text extractors
│   ├── __init__.py
│   ├── pdf_extractor.py
│   ├── text_extractor.py
│   ├── image_extractor.py
│   ├── notebook_extractor.py
│   └── chunker.py
├── llm/                        # LLM + embedding clients
│   ├── __init__.py
│   ├── client.py               # Groq client
│   └── embeddings.py           # Local sentence-transformers
├── vectorstore/                # ChromaDB wrapper
│   ├── __init__.py
│   └── chroma_store.py
├── .env                        # Secrets (API key) — DO NOT commit
├── .streamlit/
│   └── config.toml             # Streamlit config (silences watcher noise)
├── config.py                   # Central configuration
├── ingest.py                   # Ingestion CLI
├── rag.py                      # Query CLI
├── app.py                      # Streamlit web UI
├── requirements.txt
└── README.md
```

---

## 🔧 Installation

### Prerequisites

- **Python 3.11 or 3.12** — [Download](https://www.python.org/downloads/)  
  ✅ Check **"Add Python to PATH"** during install
- **Tesseract OCR** (for image/scanned PDF text)  
  - Windows: [UB-Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki)  
    Install to `C:\Program Files\Tesseract-OCR\`
  - macOS: `brew install tesseract`
  - Linux: `sudo apt install tesseract-ocr`
- **Groq API key** (free) — [console.groq.com/keys](https://console.groq.com/keys)

### Step 1 — Clone or create the project

```powershell
cd D:\Personal
mkdir docassistant
cd docassistant
```

Copy all project files into this folder.

### Step 2 — Create virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**If PowerShell blocks the activation script:**

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then retry activation.

### Step 3 — Install Python dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

`requirements.txt`:

```txt
groq>=0.11.0
sentence-transformers>=3.0.0
chromadb>=0.5.0
pymupdf>=1.24.0
langchain-text-splitters>=0.2.0
streamlit>=1.38.0
python-dotenv>=1.0.0
Pillow>=10.0.0
pytesseract>=0.3.10
tiktoken>=0.7.0
```

### Step 4 — Point Tesseract to the right path (Windows)

Open `extractors/image_extractor.py` and `extractors/pdf_extractor.py`, and add at the top:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

(Skip if `tesseract` is already on your PATH — verify with `tesseract --version`.)

---

## ⚙️ Configuration

### Step 1 — Create `.env`

Create a file named `.env` in the project root:

```env
# Groq API
GROQ_API_KEY=gsk_your-key-here
GROQ_MODEL=llama-3.1-8b-instant

# Storage
CHROMA_PATH=./data/db
DATA_DIR=./data
```

**Model options:**
- `llama-3.1-8b-instant` — fastest, good for RAG
- `llama-3.3-70b-versatile` — smarter, slower
- `openai/gpt-oss-20b` — Groq's newer default

Check available models: [console.groq.com/docs/models](https://console.groq.com/docs/models)

### Step 2 — Create `.streamlit/config.toml`

Silences Streamlit's noisy file watcher (which throws harmless `torchvision` warnings):

```powershell
mkdir .streamlit
notepad .streamlit\config.toml
```

Paste:

```toml
[server]
fileWatcherType = "none"

[global]
developmentMode = false
```

### Step 3 — Tune retrieval (optional)

Edit `config.py`:

| Setting | Default | What it does |
|---|---|---|
| `CHUNK_SIZE` | `800` | Tokens per chunk. Larger = more context, less precision |
| `CHUNK_OVERLAP` | `100` | Overlap between chunks (prevents boundary loss) |
| `TOP_K` | `5` | How many chunks to retrieve per question |
| `SIMILARITY_THRESHOLD` | `1.2` | Cosine distance cutoff. **Lower = stricter** (more refusals) |

**Tuning `SIMILARITY_THRESHOLD`:**
- Ask a question you *know* is in your docs → distance ~0.3–0.7
- Ask a question you *know* is NOT in your docs → distance ~0.9–1.4
- Set threshold between those clusters

---

## 🚀 Usage

### 1. Add documents

Drop files into `data/` (subfolders work — the ingester walks recursively):

```powershell
copy C:\path\to\notes.md .\data\
copy C:\path\to\report.pdf .\data\1_SQL\
```

Supported extensions: `.pdf`, `.txt`, `.md`, `.markdown`, `.rst`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.py`, `.sql`, `.ipynb`, `.json`, `.yaml`, `.yml`, `.csv`, `.tsv`, `.log`, `.js`, `.ts`, `.java`, `.scala`, `.r`, `.sh`, `.ps1`, `.bat`, `.html`, `.xml`, `.toml`, `.ini`, `.cfg`

### 2. Ingest

```powershell
# Ingest a single file
python ingest.py .\data\notes.md

# Ingest a folder (recursive)
python ingest.py .\data\

# Ingest a specific subfolder
python ingest.py .\data\1_SQL

# List what's indexed
python ingest.py --list

# Wipe and start over
python ingest.py --reset
```

**Expected output:**
```
Ingesting: .\data\
  ↳ +5 chunks: 1_SQL\06-joins.md
  ↳ +12 chunks: 2_Python\notebook.ipynb
  ↳ +3 chunks: Coding\screenshot.png

Done. Added 20 new chunks. Total in store: 20
```

### 3. Ask questions (CLI)

```powershell
python rag.py "What is the difference between a left join and an inner join?"
python rag.py "Summarize my Airflow notes"
python rag.py "Show me the PySpark code for window functions"
```

**Example output:**
```
=== ANSWER ===
A LEFT JOIN returns every row from the left table plus matching rows from the
right; an INNER JOIN returns only rows with matching keys in both tables.
[06-joins.md, p.1] [05_Joins_in_Spark.md, p.1]

=== SOURCES ===
  - D:\Personal\docassistant\data\1_SQL\sql-notes\06-joins.md  (p.1, distance=0.404)
  - D:\Personal\docassistant\data\4_Spark_Databricks\...\05_Joins_in_Spark.md  (p.1, distance=0.440)
```

### 4. Launch the Web UI

```powershell
streamlit run app.py
```

Browser opens at **http://localhost:8501**

Features:
- 📊 Sidebar shows chunk count and indexed files
- 📤 Drag & drop upload (auto-ingests)
- 💬 Chat interface with expandable source panels
- 🔄 Refresh / Reset buttons

---

## 🛠️ Common Commands Cheatsheet

| Task | Command |
|---|---|
| Activate venv (PowerShell) | `.\.venv\Scripts\Activate.ps1` |
| Add new files | Copy into `data\` |
| Ingest everything | `python ingest.py .\data\` |
| List indexed files | `python ingest.py --list` |
| Wipe & re-ingest | `python ingest.py --reset` then `python ingest.py .\data\` |
| Ask via CLI | `python rag.py "your question"` |
| Start web UI | `streamlit run app.py` |
| Stop web UI | `Ctrl+C` in terminal |

---

## 🔒 Privacy & Data Flow

```
┌─────────────────────────── LOCAL ───────────────────────────┐
│                                                              │
│  Your files (data/) → extractors → chunker                  │
│                          ↓                                   │
│                    local embeddings                          │
│                  (sentence-transformers)                     │
│                          ↓                                   │
│                    ChromaDB (data/db/)                       │
│                                                              │
└──────────────────────────┬───────────────────────────────────┘
                           │
                  ┌────────▼─────────┐
                  │  Groq API call   │
                  │  (question +     │
                  │   retrieved      │
                  │   chunks only)   │
                  └────────┬─────────┘
                           │
                           ▼
                    Answer returned
```

**What leaves your machine:** Only the question text + the retrieved chunks (top 5) sent to Groq per query.

**What stays local:** All your files, embeddings, vector DB, and OCR.

**For fully offline operation:** Swap Groq for **Ollama** (`llama3.2:3b` or `llama3.1:8b`) — see [Optional: Fully Offline Mode](#-optional-fully-offline-mode) below.

---

## 🐛 Troubleshooting

### `GROQ_API_KEY not set`
- `.env` must be in the project root (same folder as `ingest.py`)
- No quotes or spaces around the key
- Get a fresh key at [console.groq.com/keys](https://console.groq.com/keys)

### `Model does not exist or you do not have access to it`
Groq retires models periodically. Check the current list at [console.groq.com/docs/models](https://console.groq.com/docs/models) and update `GROQ_MODEL` in `.env`.

### `ModuleNotFoundError: No module named 'torchvision'` (flooding console)
Harmless. Streamlit's file watcher probes `transformers` optional deps. Fix:
```powershell
streamlit run app.py --server.fileWatcherType none
```
Or add `.streamlit/config.toml` as shown in [Configuration](#step-2--create-streamlitconfigtoml).

### `tesseract is not installed or it's not in your PATH`
Add to `extractors/image_extractor.py` and `extractors/pdf_extractor.py`:
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### `I don't know based on the provided documents.` for everything
Distance threshold is too strict. In `config.py`, raise `SIMILARITY_THRESHOLD` from `1.2` → `1.5`.

### Everything shows `distance=1.05`+
Your query wording doesn't match the document. Try rephrasing, or increase `TOP_K` to 8.

### Ingest says "no text extracted"
- PDFs: check if scanned (image-only) — OCR should handle it, ensure Tesseract is installed
- Empty/blank files
- Unsupported extension — check `SUPPORTED_EXTENSIONS` in `config.py`

### `Activate.ps1 cannot be loaded`
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### First ingest is slow
The embedding model (~80 MB) downloads on first run. Subsequent runs are fast.

### Rate limit from Groq
Wait 60 seconds, or switch to `llama-3.1-8b-instant` (higher free-tier limits).

---

## 🔌 Optional: Fully Offline Mode

Replace Groq with **Ollama** for 100% offline operation (no API key, no network).

### Install Ollama
Download from [ollama.com/download](https://ollama.com/download), then:
```powershell
ollama pull llama3.2:3b
# or, if you have 16GB+ RAM:
ollama pull llama3.1:8b
```

### Install Python client
```powershell
pip install ollama
```

### Update `rag.py`
Replace the Groq call in `RAGEngine.ask()`:

```python
import ollama

resp = ollama.chat(
    model="llama3.1:8b",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ],
    options={"temperature": 0},
)
answer = resp["message"]["content"].strip()
```

Remove `from llm.client import get_groq_client` and `self.client = get_groq_client()`.

That's it — no API key, no cost, no network.

---

## 📈 Recommended Next Upgrades

1. **Hybrid search (BM25 + vector)** — much better recall for code identifiers like `df.groupBy` or `S3KeySensor`
2. **Code-aware chunking** — split `.py` / `.sql` files on function/class boundaries, not character count
3. **Query rewriting** — makes follow-up questions work naturally ("What about in Spark?")
4. **Streaming responses** — show answers word-by-word in the UI
5. **Re-ranking** — send top 20 hits to a reranker, return top 5 to the LLM

---

## 📊 Cost Estimate

| Component | Cost |
|---|---|
| Local embeddings | **$0** |
| ChromaDB | **$0** |
| Tesseract OCR | **$0** |
| Groq (free tier) | **$0** for ~14,400 requests/day |
| **Total** | **$0** |

---

## 📄 License

Personal use. Do whatever you want with it.

---

## 🙏 Built With

- [Groq](https://groq.com) — blazing-fast LLM inference
- [ChromaDB](https://www.trychroma.com) — local vector store
- [sentence-transformers](https://www.sbert.net) — local embeddings
- [PyMuPDF](https://pymupdf.readthedocs.io) — PDF parsing
- [Streamlit](https://streamlit.io) — web UI
- [Tesseract](https://github.com/tesseract-ocr/tesseract) — OCR engine