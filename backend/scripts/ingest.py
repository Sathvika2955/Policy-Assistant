"""Index every file in data/policies.   Run:  python -m scripts.ingest"""
from app.config import POLICY_DIR, SUPPORTED_EXTENSIONS
from app.retrieval import ingest_file, list_documents

for f in sorted(POLICY_DIR.iterdir()):
    if f.suffix.lower() in SUPPORTED_EXTENSIONS:
        n = ingest_file(f)
        print(f"Indexed {f.name}: {n} chunks")

print("\nDocuments in database:", list_documents())
