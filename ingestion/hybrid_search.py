"""
hybrid_search.py
────────────────
Hybrid Retrieval = BM25  ∥  Vector Search  →  RRF Fusion  →  Top-K

Pipeline:
  1. Nhận query (string)
  2. Tokenize bằng underthesea (word_tokenize)
  3. Chạy song song:
       [BM25 search] ──┐
                        ├──→ Reciprocal Rank Fusion → top K chunks
       [Vector search] ─┘
  4. In kết quả ra console để review

Cài đặt:
    pip install rank-bm25 psycopg2-binary python-dotenv underthesea \
                sentence-transformers qdrant-client

Chạy:
    python hybrid_search.py
"""

import os
import pickle
import heapq
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# ── Tokenizer tiếng Việt ────────────────────────────────────────────────────
try:
    from underthesea import word_tokenize

    def tokenize(text: str) -> list[str]:
        """Tách từ tiếng Việt bằng underthesea, trả về list token lowercase."""
        return word_tokenize(text.lower(), format="text").split()

    _TOKENIZER = "underthesea"
except ImportError:

    def tokenize(text: str) -> list[str]:
        return text.lower().split()

    _TOKENIZER = "whitespace"

print(f"🔤 Tokenizer: {_TOKENIZER}")


# ── Config ──────────────────────────────────────────────────────────────────
load_dotenv(dotenv_path="../.env")

MODEL_NAME    = "mainguyen9/vietlegal-harrier-0.6b"
COLLECTION    = "legal_chunks"
VECTOR_SIZE   = 1024
BM25_CACHE    = "bm25_indexer.pkl"      # cache BM25 (do bm25_indexer.py tạo)

DB_CONFIG = dict(
    host="localhost",
    port=5432,
    database="legal_db",
    user="admin",
    password="admin123",
)

# ── RRF parameters ──────────────────────────────────────────────────────────
RRF_K       = 60       # hằng số smoothing mặc định (paper gốc dùng 60)
DEFAULT_TOP = 10       # số kết quả mỗi nhánh trả về trước khi fuse
FINAL_TOP_K = 5        # số kết quả cuối cùng sau RRF


# ════════════════════════════════════════════════════════════════════════════
# Lazy singletons – chỉ load 1 lần
# ════════════════════════════════════════════════════════════════════════════
_bm25:   BM25Okapi | None       = None
_chunks: list[dict] | None      = None
_model:  SentenceTransformer | None = None
_qdrant: QdrantClient | None    = None


def _get_bm25():
    """Load BM25 index + chunks từ cache (pickle)."""
    global _bm25, _chunks
    if _bm25 is not None:
        return _bm25, _chunks

    if not os.path.exists(BM25_CACHE):
        raise FileNotFoundError(
            f"Không tìm thấy '{BM25_CACHE}'. "
            f"Hãy chạy bm25_indexer.py trước để build index."
        )
    with open(BM25_CACHE, "rb") as f:
        data = pickle.load(f)
    _bm25   = data["bm25"]
    _chunks = data["chunks"]
    print(f"📂 BM25 index loaded — {len(_chunks)} chunks.")
    return _bm25, _chunks


def _get_model():
    """Load SentenceTransformer (cached sau lần đầu)."""
    global _model
    if _model is not None:
        return _model
    print("🔄 Loading embedding model…")
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        os.environ["HUGGING_FACE_HUB_TOKEN"] = hf_token
    _model = SentenceTransformer(MODEL_NAME)
    print(f"✅ Model '{MODEL_NAME}' ready.")
    return _model


def _get_qdrant():
    """Kết nối Qdrant (singleton)."""
    global _qdrant
    if _qdrant is not None:
        return _qdrant
    _qdrant = QdrantClient(host="localhost", port=6333)
    print("✅ Qdrant connected.")
    return _qdrant


# ════════════════════════════════════════════════════════════════════════════
# 1. BM25 Search
# ════════════════════════════════════════════════════════════════════════════
def search_bm25(query: str, top_k: int = DEFAULT_TOP) -> list[dict]:
    """
    Trả về top_k chunks từ BM25, mỗi item gồm:
        pg_id, rank, bm25_score, + metadata
    """
    bm25, chunks = _get_bm25()
    query_tokens = tokenize(query)
    scores       = bm25.get_scores(query_tokens)

    top_indices = heapq.nlargest(top_k, range(len(scores)), key=lambda i: scores[i])

    results = []
    for rank, idx in enumerate(top_indices, start=1):
        if scores[idx] == 0.0:
            continue
        c = chunks[idx]
        results.append({
            "pg_id":        c["pg_id"],
            "rank":         rank,
            "bm25_score":   round(float(scores[idx]), 4),
            "so_hieu":      c["so_hieu"],
            "loai_van_ban": c["loai_van_ban"],
            "so_dieu":      c["so_dieu"],
            "ten_dieu":     c["ten_dieu"],
            "noi_dung":     c["noi_dung"],
        })
    return results


# ════════════════════════════════════════════════════════════════════════════
# 2. Vector Search (Qdrant)
# ════════════════════════════════════════════════════════════════════════════
def search_vector(query: str, top_k: int = DEFAULT_TOP) -> list[dict]:
    """
    Trả về top_k chunks từ Qdrant (cosine similarity), mỗi item gồm:
        pg_id, rank, vector_score, + metadata
    """
    model  = _get_model()
    qdrant = _get_qdrant()

    query_vector = model.encode(query, normalize_embeddings=True)

    hits = qdrant.query_points(
        collection_name=COLLECTION,
        query=query_vector.tolist(),
        limit=top_k,
    ).points

    results = []
    for rank, hit in enumerate(hits, start=1):
        p = hit.payload
        results.append({
            "pg_id":        p.get("pg_id"),
            "rank":         rank,
            "vector_score": round(float(hit.score), 4),
            "so_hieu":      p.get("so_hieu"),
            "loai_van_ban": p.get("loai_van_ban"),
            "so_dieu":      p.get("so_dieu"),
            "ten_dieu":     p.get("ten_dieu"),
            "noi_dung":     p.get("noi_dung"),
        })
    return results


# ════════════════════════════════════════════════════════════════════════════
# 3. Reciprocal Rank Fusion (RRF)
# ════════════════════════════════════════════════════════════════════════════
def reciprocal_rank_fusion(
    bm25_results:   list[dict],
    vector_results: list[dict],
    k: int = RRF_K,
    top_k: int = FINAL_TOP_K,
) -> list[dict]:
    """
    RRF score(d) = Σ  1 / (k + rank_i(d))

    Gộp kết quả từ 2 nhánh theo pg_id, tính RRF score, sắp xếp giảm dần.
    Trả về top_k chunks kèm điểm từ cả 2 nguồn.
    """
    # Dict: pg_id → fused record
    fused: dict[int, dict] = {}

    # ── Tích luỹ BM25 ──────────────────────────────────────────────────────
    for item in bm25_results:
        pid = item["pg_id"]
        if pid not in fused:
            fused[pid] = {
                "pg_id":        pid,
                "rrf_score":    0.0,
                "bm25_rank":    None,
                "bm25_score":   None,
                "vector_rank":  None,
                "vector_score": None,
                "so_hieu":      item["so_hieu"],
                "loai_van_ban": item["loai_van_ban"],
                "so_dieu":      item["so_dieu"],
                "ten_dieu":     item["ten_dieu"],
                "noi_dung":     item["noi_dung"],
            }
        fused[pid]["bm25_rank"]  = item["rank"]
        fused[pid]["bm25_score"] = item["bm25_score"]
        fused[pid]["rrf_score"] += 1.0 / (k + item["rank"])

    # ── Tích luỹ Vector ────────────────────────────────────────────────────
    for item in vector_results:
        pid = item["pg_id"]
        if pid not in fused:
            fused[pid] = {
                "pg_id":        pid,
                "rrf_score":    0.0,
                "bm25_rank":    None,
                "bm25_score":   None,
                "vector_rank":  None,
                "vector_score": None,
                "so_hieu":      item["so_hieu"],
                "loai_van_ban": item["loai_van_ban"],
                "so_dieu":      item["so_dieu"],
                "ten_dieu":     item["ten_dieu"],
                "noi_dung":     item["noi_dung"],
            }
        fused[pid]["vector_rank"]  = item["rank"]
        fused[pid]["vector_score"] = item["vector_score"]
        fused[pid]["rrf_score"]   += 1.0 / (k + item["rank"])

    # ── Sắp xếp theo RRF score giảm dần ────────────────────────────────────
    ranked = sorted(fused.values(), key=lambda d: d["rrf_score"], reverse=True)
    # Gán final rank & làm tròn
    for i, rec in enumerate(ranked[:top_k], start=1):
        rec["final_rank"] = i
        rec["rrf_score"]  = round(rec["rrf_score"], 6)

    return ranked[:top_k]


# ════════════════════════════════════════════════════════════════════════════
# 4. Hybrid Search  (entry-point chính)
# ════════════════════════════════════════════════════════════════════════════
def hybrid_search(
    query: str,
    bm25_top: int  = DEFAULT_TOP,
    vector_top: int = DEFAULT_TOP,
    final_top_k: int = FINAL_TOP_K,
    rrf_k: int = RRF_K,
) -> list[dict]:
    """
    Chạy BM25 + Vector search song song → RRF → trả top_k chunks.
    """
    # Song song: BM25 & Vector
    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_bm25   = pool.submit(search_bm25,   query, bm25_top)
        fut_vector = pool.submit(search_vector, query, vector_top)

    bm25_results   = fut_bm25.result()
    vector_results = fut_vector.result()

    # Fuse & rank
    fused = reciprocal_rank_fusion(
        bm25_results, vector_results, k=rrf_k, top_k=final_top_k
    )
    return fused

