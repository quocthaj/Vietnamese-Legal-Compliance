"""
gen_test_set.py
───────────────
Auto-generates a retrieval test set from articles (Điều) already ingested
into PostgreSQL. For each sampled article, creates a query that references
the article number and legal document — the kind of query where BM25
exact-match is expected to help most — plus ground-truth for Hit@k eval.

Output: eval/test_set.json
"""

import json
import random
import psycopg2
import os
import sys

# Ensure imports work from eval/ directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ── DB config (matches ingestion/init_db.py & docker-compose.yml) ───────────
DB_CONFIG = dict(
    host="localhost",
    port=5432,
    database="legal_db",
    user="admin",
    password="admin123",
)

# ── SQL matching actual schema from ingestion/init_db.py ────────────────────
# Columns: id, document_id, loai_van_ban, so_hieu, ngay_ban_hanh, ten_file,
#           so_dieu, ten_dieu, noi_dung, vector_id
QUERY_ALL_CHUNKS = """
SELECT so_hieu, ten_file, so_dieu, ten_dieu, noi_dung
FROM legal_chunks
WHERE noi_dung IS NOT NULL AND noi_dung <> ''
ORDER BY id;
"""

N_SAMPLES = 30  # ≥20 for statistically meaningful results

# Map ten_file → human-readable ten_van_ban for natural queries
FILE_TO_NAME = {
    "LuatDulieucanhan.pdf": "Luật Dữ liệu cá nhân",
    "LuatTrituenhantao.pdf": "Luật Trí tuệ nhân tạo",
    "Luatanninhmang.pdf": "Luật An ninh mạng",
    "Luatcongngheso.pdf": "Luật Công nghệ số",
    "Luatso20_2023_QH15_Luatgiaodichdientu.pdf": "Luật Giao dịch điện tử",
}


def build_query(ten_file: str, so_dieu: int, ten_dieu: str) -> str:
    """
    Natural-language question referencing the article number.
    Mix of query styles to test both keyword and semantic retrieval.
    """
    ten_van_ban = FILE_TO_NAME.get(ten_file, ten_file)
    templates = [
        f"Điều {so_dieu} của {ten_van_ban} quy định gì?",
        f"Nội dung Điều {so_dieu} {ten_van_ban} là gì?",
        f"Cho tôi biết Điều {so_dieu} trong {ten_van_ban}.",
        f"{ten_van_ban} quy định về {ten_dieu} như thế nào?",
        f"Hãy giải thích Điều {so_dieu} về {ten_dieu}.",
    ]
    return random.choice(templates)


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(QUERY_ALL_CHUNKS)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        raise RuntimeError(
            "No rows returned — check DB_CONFIG and table schema."
        )

    print(f"Loaded {len(rows)} chunks from PostgreSQL.")

    sample = random.sample(rows, min(N_SAMPLES, len(rows)))

    test_set = []
    for so_hieu, ten_file, so_dieu, ten_dieu, _noi_dung in sample:
        test_set.append({
            "query": build_query(ten_file, so_dieu, ten_dieu or ""),
            "expected_so_hieu": so_hieu,
            "expected_dieu": so_dieu,
            "ten_file": ten_file,
        })

    out_path = os.path.join(os.path.dirname(__file__), "test_set.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(test_set, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(test_set)} test queries -> {out_path}")
    # Preview first 3
    for i, item in enumerate(test_set[:3]):
        print(f"  [{i+1}] {item['query']}")
        print(f"       expected: so_hieu={item['expected_so_hieu']}, dieu={item['expected_dieu']}")


if __name__ == "__main__":
    main()
