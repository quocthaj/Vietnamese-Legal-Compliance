import os
import sys
import time
from dotenv import load_dotenv

# Đảm bảo có thể import từ thư mục cha khi chạy từ root hoặc trong thư mục ingestion
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import các hàm helper từ hybrid_search để đảm bảo tính nhất quán
from ingestion.hybrid_search import _get_model, _get_bm25, tokenize

def run_benchmark():
    """Chạy các bài kiểm tra hiệu năng cho hệ thống Retrieval."""
    load_dotenv()
    
    print("🚀 BẮT ĐẦU BENCHMARK HỆ THỐNG (Retrieval Performance)")
    print("-" * 50)

    # ── Test 1: Startup latency (Loading Model) ──────────────────────────
    print("\n[TEST 1] Load Embedding Model")
    t0 = time.time()
    try:
        model = _get_model()
        print(f"✅ Load model thành công: {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"❌ Lỗi load model: {e}")
        return

    # ── Test 2: BM25 load ────────────────────────────────────────────────
    print("\n[TEST 2] Load BM25 Index")
    t0 = time.time()
    try:
        bm25, chunks = _get_bm25()
        print(f"✅ Load BM25 ({len(chunks)} chunks): {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"❌ Lỗi load BM25: {e}")
        print("💡 Gợi ý: Hãy chạy 'python ingestion/bm25_indexer.py' để build index trước.")
        return

    # ── Test 3: Single query latency ─────────────────────────────────────
    print("\n[TEST 3] Single Query Latency")
    query = "biện pháp bảo vệ an ninh mạng"
    print(f"Query: '{query}'")

    # Benchmarking Embedding
    t0 = time.time()
    _ = model.encode(query, normalize_embeddings=True)
    t_embed = time.time() - t0
    print(f"  - Embedding: {t_embed:.3f}s")

    # Benchmarking Tokenization & BM25
    t0 = time.time()
    tokens = tokenize(query)
    _ = bm25.get_scores(tokens)
    t_bm25 = time.time() - t0
    print(f"  - BM25 Search: {t_bm25:.3f}s")
    print(f"  => Tổng cộng (Local retrieval): {t_embed + t_bm25:.3f}s")

    # ── Test 4: Subsequent queries ───────────────────────────────────────
    print("\n[TEST 4] Subsequent Queries (5 queries liên tiếp)")
    queries = [
        "an ninh mạng là gì",
        "biện pháp bảo vệ hệ thống thông tin",
        "quyền và nghĩa vụ doanh nghiệp",
        "phòng chống tấn công mạng",
        "cấp độ hệ thống thông tin",
    ]
    
    latencies = []
    for i, q in enumerate(queries, 1):
        t_start = time.time()
        
        # Simulating full retrieval steps (Embed + BM25)
        model.encode(q, normalize_embeddings=True)
        tokens = tokenize(q)
        bm25.get_scores(tokens)
        
        dt = time.time() - t_start
        latencies.append(dt)
        print(f"  {i}. '{q[:30]}...': {dt:.3f}s")
    
    avg_latency = sum(latencies) / len(latencies)
    print(f"\n📊 Kết quả thống kê:")
    print(f"  - Trung bình: {avg_latency:.3f}s/query")
    print(f"  - Nhanh nhất: {min(latencies):.3f}s")
    print(f"  - Chậm nhất:  {max(latencies):.3f}s")
    
    print("-" * 50)
    print("🏁 BENCHMARK HOÀN TẤT")

if __name__ == "__main__":
    # Cho phép chạy trực tiếp: python ingestion/benchmark.py
    run_benchmark()