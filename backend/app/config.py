import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
POLICY_DIR = BASE_DIR / "data" / "policies"      # where policy files live
CHROMA_DIR = BASE_DIR / "data" / "chroma"        # where the vector DB is stored
DB_PATH = BASE_DIR / "data" / "app.db"           # SQLite: users, chats

# --- RAG settings ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"             # small, fast, runs on CPU
COLLECTION_NAME = "policies"
CHUNK_SIZE = 800        # characters per chunk
CHUNK_OVERLAP = 120     # overlap so sentences cut at a boundary aren't lost
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_UPLOAD_MB = 10
MIN_SOURCE_SCORE = float(os.getenv("MIN_SOURCE_SCORE", "0.35"))  # hide weak citations

# --- Auth settings ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 480

# --- Web settings ---
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if o.strip()
]

# --- LLM ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
