import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app import config, retrieval
from app.deps import get_current_user, require_admin
from app.ingestion import load_pages

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(user: dict = Depends(get_current_user)):
    return {"documents": retrieval.list_documents()}


@router.get("/{filename}")
def read_document(filename: str, admin: dict = Depends(require_admin)):
    """Return extracted document text for the admin preview dialog."""
    safe_name = Path(filename).name
    if safe_name != filename or safe_name not in retrieval.list_documents():
        raise HTTPException(status_code=404, detail="Document not found")
    path = config.POLICY_DIR / safe_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Document file is unavailable")
    try:
        pages = load_pages(path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not read this file: {exc}")
    return {"filename": safe_name, "pages": pages}


@router.post("", status_code=201)
def upload_document(file: UploadFile = File(...), admin: dict = Depends(require_admin)):
    # Keep only a safe file name (no folders, no odd characters)
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", Path(file.filename or "").name).lstrip(".")
    if Path(name).suffix.lower() not in config.SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(config.SUPPORTED_EXTENSIONS))
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed}")

    limit = config.MAX_UPLOAD_MB * 1024 * 1024
    data = file.file.read(limit + 1)
    if not data:
        raise HTTPException(status_code=400, detail="The file is empty")
    if len(data) > limit:
        raise HTTPException(status_code=413, detail=f"File larger than {config.MAX_UPLOAD_MB} MB")

    config.POLICY_DIR.mkdir(parents=True, exist_ok=True)
    dest = config.POLICY_DIR / name
    dest.write_bytes(data)
    try:
        chunks = retrieval.ingest_file(dest)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Could not read this file: {exc}")
    if chunks == 0:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="No readable text found in this file")
    return {"filename": name, "chunks": chunks}


@router.delete("/{filename}")
def delete_document(filename: str, admin: dict = Depends(require_admin)):
    if filename not in retrieval.list_documents():
        raise HTTPException(status_code=404, detail="Document not found")
    retrieval.delete_document(filename)
    (config.POLICY_DIR / Path(filename).name).unlink(missing_ok=True)
    return {"deleted": filename}
