"""Measure retrieval quality.   Run:  python -m scripts.evaluate

Two scores per question:
  * Source-level : did the right DOCUMENT appear in the top-k results?   (lenient)
  * Chunk-level  : did a chunk from the right document that actually
                   CONTAINS the answer text appear in the top-k?        (strict)
"""
import json

from app.config import BASE_DIR
from app.retrieval import search

EVAL_FILE = BASE_DIR / "data" / "eval_set.json"
K = 3


def first_rank(hits, predicate):
    """1-based position of the first hit satisfying predicate, else None."""
    for i, h in enumerate(hits, 1):
        if predicate(h):
            return i
    return None


def recall(ranks, k):
    return sum(1 for r in ranks if r is not None and r <= k) / len(ranks)


def main():
    cases = json.loads(EVAL_FILE.read_text(encoding="utf-8"))
    source_ranks, chunk_ranks, failures = [], [], []

    for c in cases:
        hits = search(c["question"], k=K)
        src = first_rank(hits, lambda h: h["source"] == c["expected_source"])
        chk = first_rank(
            hits,
            lambda h: h["source"] == c["expected_source"]
            and c["must_contain"].lower() in h["text"].lower(),
        )
        source_ranks.append(src)
        chunk_ranks.append(chk)
        if chk != 1:
            failures.append((c, hits, chk))

    print(f"Questions evaluated: {len(cases)}\n")
    print(f"{'':16}{'Recall@1':>10}{'Recall@3':>10}")
    print(f"{'Source-level':16}{recall(source_ranks, 1):>10.0%}{recall(source_ranks, 3):>10.0%}")
    print(f"{'Chunk-level':16}{recall(chunk_ranks, 1):>10.0%}{recall(chunk_ranks, 3):>10.0%}")

    if failures:
        print("\n--- Questions where the right chunk was NOT the #1 result ---")
        for c, hits, chk in failures:
            print(f"\nQ: {c['question']}")
            print(f"   expected: {c['expected_source']} containing '{c['must_contain']}'")
            print(f"   found at rank: {chk or 'not in top ' + str(K)}")
            for h in hits:
                print(f"   got: {h['source']} (score {h['score']})")


if __name__ == "__main__":
    main()
