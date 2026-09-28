import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/db")
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
TOP_K = 5
SIMILARITY_THRESHOLD = 1.2

SUPPORTED_EXTENSIONS = {
    ".pdf", ".txt", ".md", ".markdown", ".rst",
    ".png", ".jpg", ".jpeg", ".webp",
    ".py", ".sql", ".ipynb", ".json", ".yaml", ".yml",
    ".csv", ".tsv", ".log",
    ".js", ".ts", ".java", ".scala", ".r",
    ".sh", ".ps1", ".bat",
    ".html", ".xml", ".toml", ".ini", ".cfg",
}

DATA_DIR.mkdir(parents=True, exist_ok=True)
Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)