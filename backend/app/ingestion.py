"""Turn a policy file (PDF / DOCX / TXT) into small text chunks with metadata."""
from pathlib import Path

from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.config import CHUNK_OVERLAP, CHUNK_SIZE, SUPPORTED_EXTENSIONS


def load_pages(path: Path) -> list[dict]:
    """Return [{'text': ..., 'page': int}]. page=0 means 'no page concept' (DOCX/TXT)."""
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    if ext == ".pdf":
        reader = PdfReader(str(path))
        return [
            {"text": (p.extract_text() or ""), "page": i + 1}
            for i, p in enumerate(reader.pages)
        ]
    if ext == ".docx":
        doc = Document(str(path))
        text = "\n".join(p.text for p in doc.paragraphs)
        return [{"text": text, "page": 0}]
    return [{"text": path.read_text(encoding="utf-8", errors="ignore"), "page": 0}]


def chunk_file(path: Path) -> list[dict]:
    """Split a file into overlapping chunks. Each chunk remembers its source + page."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = []
    for page in load_pages(path):
        if not page["text"].strip():
            continue
        for i, piece in enumerate(splitter.split_text(page["text"])):
            chunks.append(
                {
                    "id": f"{path.name}::p{page['page']}::c{i}",
                    "text": piece,
                    "source": path.name,
                    "page": page["page"],
                }
            )
    return chunks
