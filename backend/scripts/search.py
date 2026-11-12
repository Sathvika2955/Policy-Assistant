"""Try a search.   Run:  python -m scripts.search "how many sick days do I get?" """
import sys

from app.retrieval import search

query = " ".join(sys.argv[1:]) or "How many days of annual leave do I get?"
print(f"Q: {query}\n")
for i, h in enumerate(search(query, k=3), 1):
    page = f", page {h['page']}" if h["page"] else ""
    print(f"[{i}] {h['source']}{page}  (score {h['score']})")
    print(f"    {h['text'][:200].strip()}...\n")
