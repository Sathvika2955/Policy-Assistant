"""App entry point.   Run:  uvicorn app.main:app --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config, retrieval
from app.database import init_db
from app.routers import auth, chat, documents


def index_policies_if_empty() -> None:
    """On a fresh server (e.g. free hosting with a wiped disk) index the bundled policies."""
    if retrieval.list_documents():
        return
    for f in sorted(config.POLICY_DIR.glob("*")):
        if f.suffix.lower() in config.SUPPORTED_EXTENSIONS:
            retrieval.ingest_file(f)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    index_policies_if_empty()
    yield


app = FastAPI(title="Enterprise Policy Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}
