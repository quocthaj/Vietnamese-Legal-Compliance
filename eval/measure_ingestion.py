"""
measure_ingestion.py
────────────────────
Times the full ingestion pipeline end-to-end:
  1. PDF parsing + metadata extraction + chunk insertion into PostgreSQL
  2. Embedding chunks with SentenceTransformer + upsert to Qdrant
  3. Building BM25 index (tokenize + pickle)

This gives the real number: "processing 143 pages / 223 articles in X seconds".

Prerequisites: PostgreSQL and Qdrant running (docker compose up -d postgres qdrant)
Warning: This will DELETE existing data and re-ingest from scratch!
"""

import time
import os
import sys
import psycopg2

# Ensure imports work from eval/ directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DB_CONFIG = dict(
    host="localhost",
    port=5432,
    database="legal_db",
    user="admin",
    password="admin123",
)


def clean_db():
    """Remove all existing chunks and documents so we re-ingest from scratch."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("DELETE FROM legal_chunks;")
    cur.execute("DELETE FROM legal_documents;")
    conn.commit()
    cur.close()
    conn.close()
    print("🗑️ Cleaned existing data from PostgreSQL.")


def clean_qdrant():
    """Delete and recreate the Qdrant collection."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance
    qdrant = QdrantClient(host="localhost", port=6333)
    try:
        qdrant.delete_collection("legal_chunks")
        print("🗑️ Deleted Qdrant collection 'legal_chunks'.")
    except Exception:
        pass
    qdrant.create_collection(
        collection_name="legal_chunks",
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )
    print("📦 Recreated Qdrant collection 'legal_chunks'.")


def clean_bm25():
    """Remove BM25 cache file."""
    bm25_path = os.path.join(os.path.dirname(__file__), '..', 'ingestion', 'bm25_indexer.pkl')
    if os.path.exists(bm25_path):
        os.remove(bm25_path)
        print("🗑️ Removed BM25 cache (bm25_indexer.pkl).")


def count_results():
    """Count chunks in PostgreSQL and Qdrant after ingestion."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM legal_chunks;")
    pg_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM legal_documents;")
    doc_count = cur.fetchone()[0]
    cur.close()
    conn.close()

    from qdrant_client import QdrantClient
    qdrant = QdrantClient(host="localhost", port=6333)
    qdrant_count = qdrant.get_collection("legal_chunks").points_count

    return doc_count, pg_count, qdrant_count


def main():
    print("=" * 60)
    print("INGESTION PIPELINE BENCHMARK")
    print("=" * 60)

    # Step 0: Clean everything
    print("\n--- Step 0: Cleaning existing data ---")
    clean_db()
    clean_qdrant()
    clean_bm25()

    # Step 1: PDF Parsing
    print("\n--- Step 1: PDF Parsing + PostgreSQL Insert ---")
    t1_start = time.perf_counter()

    from ingestion.pdf_parser import parse_and_insert, PDF_FILES, conn, cursor
    total_articles = 0
    for f in PDF_FILES:
        total_articles += parse_and_insert(f)
    # Close the parser's global connection
    cursor.close()
    conn.close()

    t1_end = time.perf_counter()
    t1_elapsed = t1_end - t1_start
    print(f"\n⏱️ PDF Parsing: {t1_elapsed:.2f}s ({total_articles} articles)")

    # Step 2: Embedding + Qdrant Upsert
    print("\n--- Step 2: Embedding + Qdrant Upsert ---")
    t2_start = time.perf_counter()

    from ingestion.embedder import run_embedding
    run_embedding()

    t2_end = time.perf_counter()
    t2_elapsed = t2_end - t2_start
    print(f"\n⏱️ Embedding: {t2_elapsed:.2f}s")

    # Step 3: BM25 Index Build
    print("\n--- Step 3: BM25 Index Build ---")
    t3_start = time.perf_counter()

    from ingestion.bm25_indexer import run_indexer
    run_indexer()

    t3_end = time.perf_counter()
    t3_elapsed = t3_end - t3_start
    print(f"\n⏱️ BM25 Indexing: {t3_elapsed:.2f}s")

    # Final Results
    total_elapsed = t1_elapsed + t2_elapsed + t3_elapsed
    doc_count, pg_count, qdrant_count = count_results()

    print("\n" + "=" * 60)
    print("INGESTION PIPELINE RESULTS")
    print("=" * 60)
    print(f"Documents processed:  {doc_count}")
    print(f"Articles extracted:   {pg_count}")
    print(f"Vectors in Qdrant:    {qdrant_count}")
    print(f"")
    print(f"Step 1 (PDF Parse):   {t1_elapsed:.2f}s")
    print(f"Step 2 (Embedding):   {t2_elapsed:.2f}s")
    print(f"Step 3 (BM25 Index):  {t3_elapsed:.2f}s")
    print(f"──────────────────────────────")
    print(f"TOTAL:                {total_elapsed:.2f}s")
    print(f"")
    print(f"Ingestion pipeline: 143 pages, {pg_count} articles processed in {total_elapsed:.1f}s")


if __name__ == "__main__":
    main()
