"""
embedder.py
-----------
Pipeline:
  1. Đọc toàn bộ chunks từ PostgreSQL (bảng legal_chunks)
  2. Embed từng chunk bằng sentence-transformers (bge-m3 hoặc multilingual-e5)
  3. Upsert lên Qdrant (collection: legal_chunks)
  4. Ghi vector_id ngược lại vào PostgreSQL để truy vết

Chạy:  python embedder.py
"""
import os
import uuid
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

# ── Config ─────────────────────────────────────────────────────────────────
load_dotenv(dotenv_path="../.env")

MODEL_NAME   = "mainguyen9/vietlegal-harrier-0.6b"          
COLLECTION   = "legal_chunks"
VECTOR_SIZE  = 1024
BATCH_SIZE   = 16                      # số chunk embed cùng lúc

DB_CONFIG = dict(
    host="localhost",
    port=5432,
    database="legal_db",
    user="admin",
    password="admin123",
)

# ── 1. Load model ───────────────────────────────────────────────────────────
print("🔄 Đang load model embedding...")
hf_token = os.getenv("HF_TOKEN")
if hf_token:
    os.environ["HUGGING_FACE_HUB_TOKEN"] = hf_token   # tăng tốc download
model = SentenceTransformer(MODEL_NAME)
print(f"✅ Model '{MODEL_NAME}' sẵn sàng.\n")

# ── 2. Kết nối PostgreSQL & Qdrant ─────────────────────────────────────────
pg_conn   = psycopg2.connect(**DB_CONFIG)
pg_cursor = pg_conn.cursor()
print("✅ Kết nối PostgreSQL thành công.")

qdrant = QdrantClient(host="localhost", port=6333)
print("✅ Kết nối Qdrant thành công.\n")

# Tạo collection nếu chưa có (idempotent)
existing = [c.name for c in qdrant.get_collections().collections]
if COLLECTION not in existing:
    qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    print(f"📦 Đã tạo collection '{COLLECTION}'.")
else:
    print(f"📦 Collection '{COLLECTION}' đã tồn tại, tiếp tục upsert.")

# ── 3. Đọc tất cả chunks từ PostgreSQL ────────────────────────────────────
pg_cursor.execute("""
    SELECT id, loai_van_ban, so_hieu, ngay_ban_hanh, ten_file,
           so_dieu, ten_dieu, noi_dung
    FROM legal_chunks
    ORDER BY id
""")
rows = pg_cursor.fetchall()
print(f"📄 Tổng số chunks: {len(rows)}\n")

# ── 4. Embed & Upsert theo batch ───────────────────────────────────────────
total_upserted = 0

for batch_start in range(0, len(rows), BATCH_SIZE):
    batch = rows[batch_start : batch_start + BATCH_SIZE]

    # Tạo text đầu vào cho model: ghép tiêu đề + nội dung
    texts = []
    for row in batch:
        _, loai, so_hieu, ngay, ten_file, so_dieu, ten_dieu, noi_dung = row
        text = f"Điều {so_dieu}. {ten_dieu}\n{noi_dung or ''}".strip()
        texts.append(text)

    # Embed cả batch
    vectors = model.encode(
        texts,
        normalize_embeddings=True,   # cosine similarity tốt hơn
        show_progress_bar=False,
    )

    # Tạo danh sách PointStruct
    points = []
    for i, row in enumerate(batch):
        row_id, loai, so_hieu, ngay, ten_file, so_dieu, ten_dieu, noi_dung = row
        vector_id = str(uuid.uuid4())

        points.append(
            PointStruct(
                id=row_id,                     # dùng PG id làm Qdrant id
                vector=vectors[i].tolist(),
                payload={
                    "pg_id":        row_id,
                    "so_dieu":      so_dieu,
                    "ten_dieu":     ten_dieu,
                    "so_hieu":      so_hieu,
                    "loai_van_ban": loai,
                    "ngay_ban_hanh": ngay,
                    "ten_file":     ten_file,
                    "noi_dung":     (noi_dung or "")[:500],  # preview payload
                },
            )
        )

        # Ghi vector_id (UUID) ngược về PostgreSQL
        pg_cursor.execute(
            "UPDATE legal_chunks SET vector_id = %s WHERE id = %s",
            (str(row_id), row_id),   # dùng id PG làm vector_id cho dễ map
        )

    # Upsert batch lên Qdrant
    qdrant.upsert(collection_name=COLLECTION, points=points)
    pg_conn.commit()

    total_upserted += len(batch)
    print(f"  ✅ Batch {batch_start // BATCH_SIZE + 1}: upserted {len(batch)} chunks "
          f"(tổng: {total_upserted}/{len(rows)})")

# ── 5. Dọn dẹp ─────────────────────────────────────────────────────────────
pg_cursor.close()
pg_conn.close()

print(f"\n🎉 Hoàn thành! Đã embed & upsert {total_upserted} chunks vào Qdrant.")
print(f"   Collection : {COLLECTION}")
print(f"   Vector size: {VECTOR_SIZE}")
print(f"   Model      : {MODEL_NAME}")
print("🔒 Đã đóng kết nối PostgreSQL.")