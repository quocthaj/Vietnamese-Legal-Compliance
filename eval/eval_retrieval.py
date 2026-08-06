"""
eval_retrieval.py
─────────────────
Compares retrieval accuracy of:
  (a) Hybrid Search (BM25 + Qdrant vector via RRF) — production path
  (b) Vector-only Search (Qdrant alone) — baseline

Metric: Hit@k — for each test query, does the top-k retrieved chunk set
contain the chunk matching (expected_so_hieu, expected_dieu)?

Requires: test_set.json (run gen_test_set.py first)
          PostgreSQL, Qdrant, BM25 index all running/available.
"""

import json
import os
import sys
import time

# Ensure imports work from eval/ directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import real retrieval functions from ingestion/hybrid_search.py
from ingestion.hybrid_search import (
    hybrid_search,    # BM25 + Vector → RRF fusion
    search_vector,    # Vector-only (Qdrant cosine similarity)
    search_bm25,      # BM25-only (lexical search)
)

TOP_K = 5  # Match FINAL_TOP_K in hybrid_search.py


def hit(retrieved_chunks: list[dict], expected_so_hieu: str, expected_dieu: int) -> bool:
    """Return True if any retrieved chunk matches the expected article."""
    for chunk in retrieved_chunks:
        # Fields from hybrid_search.py: so_hieu, so_dieu
        so_hieu = chunk.get("so_hieu")
        so_dieu = chunk.get("so_dieu")
        if so_hieu == expected_so_hieu and so_dieu == expected_dieu:
            return True
    return False


def run_eval(test_set: list[dict], search_fn, label: str, top_k: int = TOP_K) -> float:
    """Run a search function against the test set and return accuracy."""
    hits = 0
    errors = 0
    for item in test_set:
        try:
            results = search_fn(item["query"], top_k)
            if hit(results, item["expected_so_hieu"], item["expected_dieu"]):
                hits += 1
        except Exception as e:
            errors += 1
            print(f"  [ERROR] {label}: {e} <- {item['query'][:60]}")

    valid = len(test_set) - errors
    acc = (hits / valid * 100) if valid > 0 else 0.0
    print(f"{label}: {hits}/{valid} ({acc:.1f}%)")
    if errors:
        print(f"  ({errors} queries errored out)")
    return acc


def hybrid_search_wrapper(query: str, top_k: int) -> list[dict]:
    """Wrapper to match eval signature: hybrid_search returns RRF-fused results."""
    return hybrid_search(query, final_top_k=top_k)


def vector_search_wrapper(query: str, top_k: int) -> list[dict]:
    """Wrapper for vector-only search (no BM25, no RRF)."""
    return search_vector(query, top_k=top_k)


def bm25_search_wrapper(query: str, top_k: int) -> list[dict]:
    """Wrapper for BM25-only search (no vector, no RRF)."""
    return search_bm25(query, top_k=top_k)


def main():
    test_set_path = os.path.join(os.path.dirname(__file__), "test_set.json")
    with open(test_set_path, "r", encoding="utf-8") as f:
        test_set = json.load(f)

    print(f"Running retrieval eval on {len(test_set)} queries, top_k={TOP_K}")
    print("=" * 60)

    # Warmup: run one query to ensure models/indexes are loaded
    print("\n⚡ Warming up models and indexes...")
    try:
        hybrid_search("warmup query", final_top_k=1)
        print("✅ Warmup complete.\n")
    except Exception as e:
        print(f"⚠️ Warmup error (non-fatal): {e}\n")

    # (a) Hybrid Search (production)
    print("--- Hybrid Search (BM25 + Vector → RRF) ---")
    hybrid_acc = run_eval(test_set, hybrid_search_wrapper, "Hybrid Search accuracy")

    print()

    # (b) Vector-only (baseline)
    print("--- Vector-only Search (Qdrant cosine) ---")
    vector_acc = run_eval(test_set, vector_search_wrapper, "Vector-only accuracy")

    print()

    # (c) BM25-only (bonus comparison)
    print("--- BM25-only Search (lexical) ---")
    bm25_acc = run_eval(test_set, bm25_search_wrapper, "BM25-only accuracy")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Hybrid Search accuracy:  {hybrid_acc:.1f}%")
    print(f"Vector-only accuracy:    {vector_acc:.1f}%")
    print(f"BM25-only accuracy:      {bm25_acc:.1f}%")
    print(f"Hybrid vs Vector-only:   +{hybrid_acc - vector_acc:.1f} percentage points")
    print(f"Hybrid vs BM25-only:     +{hybrid_acc - bm25_acc:.1f} percentage points")


if __name__ == "__main__":
    main()
