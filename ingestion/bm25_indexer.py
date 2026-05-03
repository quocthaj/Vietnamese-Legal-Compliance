"""
bm25_indexer.py
---------------
Standalone script: đọc chunks từ PostgreSQL → build BM25 index → demo search.
KHÔNG sửa bất kỳ file hệ thống nào.

Cài thêm nếu thiếu:
    pip install rank-bm25 psycopg2-binary python-dotenv underthesea

Chạy:
    python bm25_indexer.py
"""

import pickle
import psycopg2
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi

# ── tokenizer tiếng Việt ────────────────────────────────────────────────────
# Dùng underthesea nếu cài được, fallback split khoảng trắng
try:
    from underthesea import word_tokenize
    def tokenize(text: str) -> list[str]:
        return word_tokenize(text.lower(), format="text").split()
    print("🔤 Tokenizer: underthesea (word_tokenize)")
except ImportError:
    def tokenize(text: str) -> list[str]:
        return text.lower().split()
    print("🔤 Tokenizer: whitespace split (cài underthesea để tốt hơn)")


# ── Config ──────────────────────────────────────────────────────────────────
load_dotenv(dotenv_path="../.env")

DB_CONFIG = dict(
    host="localhost",
    port=5432,
    database="legal_db",
    user="admin",
    password="admin123",
)

BM25_CACHE_PATH = "bm25_indexer.pkl"   # cache để không phải build lại mỗi lần


# ════════════════════════════════════════════════════════════════════════════
# SQL: lấy toàn bộ chunks cần thiết để build BM25
# ══════════════════════════════════════════════════════════════2══════════════
SQL_LOAD_CHUNKS = """
SELECT
    id,
    loai_van_ban,
    so_hieu,
    ngay_ban_hanh,
    ten_file,
    so_dieu,
    ten_dieu,
    noi_dung
FROM legal_chunks
WHERE noi_dung IS NOT NULL
  AND noi_dung <> ''
ORDER BY id;
"""

# SQL thống kê nhanh
SQL_STATS = """
SELECT
    COUNT(*)                                        AS tong_chunks,
    COUNT(DISTINCT so_hieu)                         AS so_van_ban,
    COUNT(DISTINCT loai_van_ban)                    AS so_loai_vb,
    SUM(CASE WHEN noi_dung IS NULL THEN 1 ELSE 0 END) AS chunks_trong
FROM legal_chunks;
"""


# ════════════════════════════════════════════════════════════════════════════
# 1. Kết nối & kéo dữ liệu
# ════════════════════════════════════════════════════════════════════════════
def load_chunks_from_pg() -> list[dict]:
    """Trả về list of dict, mỗi dict là 1 chunk."""
    print("\n📡 Kết nối PostgreSQL...")
    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # In thống kê
    cursor.execute(SQL_STATS)
    stats = cursor.fetchone()
    print(f"   Tổng chunks  : {stats[0]}")
    print(f"   Số văn bản   : {stats[1]}")
    print(f"   Loại văn bản : {stats[2]}")
    print(f"   Chunks trống : {stats[3]}")

    # Kéo toàn bộ
    cursor.execute(SQL_LOAD_CHUNKS)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    print(f"\n✅ Đã load {len(rows)} chunks từ PostgreSQL.\n")

    chunks = []
    for row in rows:
        pg_id, loai_vb, so_hieu, ngay, ten_file, so_dieu, ten_dieu, noi_dung = row
        # Văn bản đầu vào cho BM25: ghép tiêu đề điều + nội dung
        text = f"Điều {so_dieu}. {ten_dieu or ''}\n{noi_dung or ''}".strip()
        chunks.append({
            "pg_id":        pg_id,
            "loai_van_ban": loai_vb,
            "so_hieu":      so_hieu,
            "ngay_ban_hanh": ngay,
            "ten_file":     ten_file,
            "so_dieu":      so_dieu,
            "ten_dieu":     ten_dieu,
            "noi_dung":     noi_dung,
            "text":         text,       # text đã ghép, dùng để tokenize
        })
    return chunks


# ════════════════════════════════════════════════════════════════════════════
# 2. Build BM25
# ════════════════════════════════════════════════════════════════════════════
def build_bm25(chunks: list[dict]) -> BM25Okapi:
    print("🔨 Tokenizing & building BM25...")
    tokenized_corpus = [tokenize(c["text"]) for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    print(f"✅ BM25 index sẵn sàng — {len(tokenized_corpus)} documents.\n")
    return bm25


def save_index(bm25: BM25Okapi, chunks: list[dict], path: str = BM25_CACHE_PATH):
    """Lưu BM25 + metadata chunks ra file để reuse."""
    with open(path, "wb") as f:
        pickle.dump({"bm25": bm25, "chunks": chunks}, f)
    print(f"💾 Đã lưu BM25 index → {path}")


def load_index(path: str = BM25_CACHE_PATH):
    """Load BM25 + chunks từ cache (không cần kéo lại PG)."""
    with open(path, "rb") as f:
        data = pickle.load(f)
    print(f"📂 Đã load BM25 index từ cache: {path}")
    return data["bm25"], data["chunks"]


# ════════════════════════════════════════════════════════════════════════════
# 3. Search
# ════════════════════════════════════════════════════════════════════════════
def search_bm25(
    query: str,
    bm25: BM25Okapi,
    chunks: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """
    Trả về top_k kết quả BM25 cho query, kèm score và metadata.
    """
    query_tokens = tokenize(query)
    scores       = bm25.get_scores(query_tokens)

    # Lấy top_k index có score cao nhất
    import heapq
    top_indices = heapq.nlargest(top_k, range(len(scores)), key=lambda i: scores[i])

    results = []
    for idx in top_indices:
        if scores[idx] == 0.0:
            continue  # bỏ kết quả không liên quan
        c = chunks[idx]
        results.append({
            "score":        round(float(scores[idx]), 4),
            "pg_id":        c["pg_id"],
            "so_hieu":      c["so_hieu"],
            "loai_van_ban": c["loai_van_ban"],
            "so_dieu":      c["so_dieu"],
            "ten_dieu":     c["ten_dieu"],
            "noi_dung":     (c["noi_dung"] or "")[:300],  # preview 300 ký tự
        })
    return results


# ════════════════════════════════════════════════════════════════════════════
# 4. Main
# ════════════════════════════════════════════════════════════════════════════
def main():
    import os

    # Build mới hoặc load từ cache
    if os.path.exists(BM25_CACHE_PATH):
        print(f"⚡ Tìm thấy cache '{BM25_CACHE_PATH}' — load nhanh (bỏ qua PG).")
        bm25, chunks = load_index()
    else:
        chunks = load_chunks_from_pg()
        bm25   = build_bm25(chunks)
        save_index(bm25, chunks)

    # ── Demo search ─────────────────────────────────────────────────────────
    demo_queries = [
        "Phạm vi điều chỉnh và đối tượng áp dụng",
        "xử phạt vi phạm hành chính",
        "quyền và nghĩa vụ của người lao động",
    ]

    for query in demo_queries:
        print("=" * 70)
        print(f"🔍 Query: {query}")
        results = search_bm25(query, bm25, chunks, top_k=3)
        if not results:
            print("  (Không có kết quả)")
            continue
        for i, r in enumerate(results, 1):
            print(f"\n  [{i}] Score={r['score']}  |  Điều {r['so_dieu']} — {r['ten_dieu']}")
            print(f"       Văn bản: {r['loai_van_ban']} {r['so_hieu']}")
            print(f"       Nội dung: {r['noi_dung'][:150]}...")
    print("=" * 70)
    print("\n🎉 Hoàn thành!")


if __name__ == "__main__":
    main()
