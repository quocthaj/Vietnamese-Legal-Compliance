"""
measure_latency.py
──────────────────
Measures real response latency of the FastAPI /chat endpoint:
  - "Simple" queries: direct lookup, expected to pass CRAG/Judge on first try
  - "Complex" queries: ambiguous / cross-document, likely to trigger CRAG re-retrieve
    or Judge re-generate (self-correction loops)

Prerequisites: FastAPI backend running (python api/main.py)
"""

import time
import statistics
import requests
import uuid

API_URL = "http://localhost:8000/chat"  # Matches api/main.py

# ── Simple queries: direct article lookup (should pass on first try) ────────
SIMPLE_QUERIES = [
    "Điều 20 Luật Giao dịch điện tử quy định gì?",
    "Điều 5 Luật Dữ liệu cá nhân nói về nội dung gì?",
    "Điều 10 Luật An ninh mạng quy định gì?",
    "Điều 3 Luật Trí tuệ nhân tạo giải thích từ ngữ nào?",
    "Điều 15 Luật Công nghệ số quy định về vấn đề gì?",
    "Nội dung Điều 8 Luật An ninh mạng là gì?",
    "Cho tôi biết Điều 12 Luật Giao dịch điện tử.",
    "Điều 25 Luật Dữ liệu cá nhân quy định về quyền gì?",
    "Điều 7 Luật Trí tuệ nhân tạo nói về nguyên tắc gì?",
    "Luật Công nghệ số Điều 20 quy định gì?",
    "Điều 30 Luật An ninh mạng nội dung như thế nào?",
    "Điều 1 Luật Giao dịch điện tử phạm vi điều chỉnh là gì?",
    "Điều 18 Luật Dữ liệu cá nhân quy định gì?",
    "Cho biết Điều 9 Luật Trí tuệ nhân tạo.",
    "Điều 40 Luật Công nghệ số quy định về vấn đề gì?",
]

# ── Complex queries: cross-document, ambiguous, likely trigger loops ────────
COMPLEX_QUERIES = [
    "So sánh quy định về bảo vệ dữ liệu cá nhân giữa Luật Dữ liệu cá nhân và Luật Giao dịch điện tử.",
    "Nếu một công ty AI thu thập dữ liệu người dùng để huấn luyện mô hình, họ cần tuân thủ những điều khoản nào theo cả Luật Trí tuệ nhân tạo và Luật Dữ liệu cá nhân?",
    "Trách nhiệm của nhà cung cấp dịch vụ mạng theo Luật An ninh mạng và Luật Công nghệ số có khác nhau không?",
    "Chữ ký điện tử có giá trị pháp lý như chữ ký tay không? Luật Giao dịch điện tử quy định thế nào?",
    "Quy định về xử lý vi phạm trong lĩnh vực an ninh mạng có áp dụng cho AI không?",
    "Các nguyên tắc đạo đức khi phát triển AI theo Luật Trí tuệ nhân tạo là gì?",
    "Doanh nghiệp nước ngoài kinh doanh tại Việt Nam phải tuân thủ những quy định nào về an ninh mạng và dữ liệu?",
    "Sự khác biệt giữa dữ liệu cá nhân nhạy cảm và dữ liệu cá nhân thông thường theo luật Việt Nam?",
    "Cơ quan nào có thẩm quyền giám sát hoạt động AI theo Luật Trí tuệ nhân tạo?",
    "Một startup fintech cần tuân thủ những quy định gì về giao dịch điện tử và bảo vệ dữ liệu cá nhân?",
]


def call_chat(query: str, session_id: str) -> float:
    """Call the /chat endpoint and return elapsed time in seconds."""
    # Matches ChatRequest schema: {"query": str, "session_id": str}
    payload = {"query": query, "session_id": session_id}
    start = time.perf_counter()
    resp = requests.post(API_URL, json=payload, timeout=60)
    elapsed = time.perf_counter() - start
    resp.raise_for_status()
    return elapsed


def measure(queries: list[str], label: str, repeats: int = 1) -> list[float]:
    """Measure latency for each query, repeating each query `repeats` times."""
    times = []
    session_id = str(uuid.uuid4())  # Use a fresh session for clean test

    for q in queries:
        for r in range(repeats):
            try:
                t = call_chat(q, session_id)
                times.append(t)
                print(f"  [{label}] {t:.2f}s  <- {q[:60]}...")
            except Exception as e:
                print(f"  [{label}] FAILED: {e}  <- {q[:60]}...")
            # Fresh session each repeat to avoid memory effects
            session_id = str(uuid.uuid4())

    if times:
        avg = statistics.mean(times)
        mn = min(times)
        mx = max(times)
        med = statistics.median(times)
        print(
            f"\n{label} latency (n={len(times)}): "
            f"avg={avg:.2f}s  median={med:.2f}s  "
            f"min={mn:.2f}s  max={mx:.2f}s\n"
        )
    else:
        print(f"\n{label}: No successful measurements.\n")

    return times


def main():
    # Check API is reachable
    print("Checking API availability...")
    try:
        requests.get("http://localhost:8000/documents", timeout=5)
        print("✅ API is reachable.\n")
    except Exception as e:
        print(f"❌ API not reachable: {e}")
        print("Start the backend first: python api/main.py")
        return

    print("=" * 60)
    print("=== Simple queries (direct article lookup) ===")
    print("=" * 60)
    simple_times = measure(SIMPLE_QUERIES, "Simple", repeats=1)

    print("=" * 60)
    print("=== Complex queries (likely trigger self-correction) ===")
    print("=" * 60)
    complex_times = measure(COMPLEX_QUERIES, "Complex", repeats=1)

    # Final summary
    print("\n" + "=" * 60)
    print("LATENCY SUMMARY")
    print("=" * 60)
    if simple_times:
        print(
            f"Simple query latency (n={len(simple_times)}): "
            f"avg={statistics.mean(simple_times):.2f}s, "
            f"min={min(simple_times):.2f}s, "
            f"max={max(simple_times):.2f}s"
        )
    if complex_times:
        print(
            f"Complex query latency (n={len(complex_times)}): "
            f"avg={statistics.mean(complex_times):.2f}s, "
            f"min={min(complex_times):.2f}s, "
            f"max={max(complex_times):.2f}s"
        )


if __name__ == "__main__":
    main()
