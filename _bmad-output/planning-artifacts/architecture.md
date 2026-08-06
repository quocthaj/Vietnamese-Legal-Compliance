---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - '_bmad-output/planning-artifacts/prds/prd-vietnamese-legal-compliance-2026-06-17/prd.md'
  - '_bmad-output/project-context.md'
workflowType: 'architecture'
project_name: 'vietnamese-legal-compliance'
user_name: 'Thai'
date: '2026-06-17'
lastStep: 8
status: 'complete'
completedAt: '2026-06-17'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

---

## 1. Phân tích bối cảnh dự án (Project Context Analysis)

### 1.1 Tóm tắt Yêu cầu (Requirements Overview)

**Yêu cầu Chức năng (Functional Requirements):**
- **[FR-1] Metadata Filtering**: Thanh bên Streamlit truyền bộ lọc (Loại luật, Năm, Cơ quan) xuống FastAPI `/chat`, dịch thành câu truy vấn lọc payload của Qdrant trước khi tính tương đồng vector.
- **[FR-2] Smart Citation**: Tự động bóc tách trích dẫn định dạng Việt Nam (ví dụ: `[Luật... - Điều X]`) và map với văn bản nguồn để hiển thị bằng `st.expander` hoặc thanh bên Streamlit mà không làm gián đoạn luồng trò chuyện.
- **[FR-3] Developer Debug Mode**: Công tắc toggle hiển thị trực quan luồng chạy của LangGraph (node nào chạy, thời gian thực thi, số lượng token tiêu thụ và quyết định của Judge).
- **[FR-4] Full Dockerization**: Tạo Dockerfile riêng cho Frontend (`fe`) và Backend (`api`), tích hợp vào `docker-compose.yml` cùng với 3 cơ sở dữ liệu (`postgres`, `qdrant`, `redis`) trên mạng bridge nội bộ.
- **[FR-5] CI/CD Pipeline**: GitHub Actions tự động kiểm tra code style (PEP 8 linting) và khởi chạy bộ unit/integration test bằng `pytest` khi có push/PR.

**Yêu cầu Phi chức năng (Non-Functional Requirements):**
- **Hiệu năng**: Thời gian phản hồi chat thông thường dưới 5 giây, tối đa 15 giây nếu có loop kiểm định của Agent; xử lý tài liệu chạy bất đồng bộ trong background.
- **Bảo mật**: Streamlit hoàn toàn cô lập với các cơ sở dữ liệu, chỉ giao tiếp qua FastAPI REST API. Không dùng `unsafe_allow_html=True` cho dữ liệu nhập từ người dùng. Biến môi trường được quản lý qua tệp `.env`.
- **Bảo trì**: Tách biệt `app.py` and `api_client.py`. Cấu hình volumes lưu trữ bền vững và restart policy `unless-stopped` cho các container database.

### 1.2 Đánh giá Quy mô & Độ phức tạp (Scale & Complexity)
- **Miền kỹ thuật chính**: Hệ thống RAG & AI Agent đa dịch vụ (FastAPI + Streamlit + LangGraph + Vector DB).
- **Mức độ phức tạp**: **Trung bình (Medium)** (Do phải đóng gói đa dịch vụ chạy trong mạng Docker nội bộ, tích hợp thư viện NLP cục bộ và theo dõi dấu vết hoạt động của Agent).
- **Số lượng thành phần kiến trúc dự kiến**: 5 dịch vụ runtime chính, 1 cấu hình CI/CD và 1 cơ chế báo cáo lịch sử.

### 1.3 Ràng buộc kỹ thuật & Điểm giao cắt (Constraints & Cross-Cutting Concerns)
- **Ràng buộc kết nối Docker**: Các dịch vụ bên trong container phải giao tiếp qua tên dịch vụ (ví dụ: `http://qdrant:6333`, `postgres:5432`) thay vì dùng `localhost`.
- **Quản lý biến môi trường đồng nhất**: Tệp `.env` cần được thiết kế để cả môi trường chạy local chạy trực tiếp (python) và chạy Docker Compose đều có thể đọc chính xác.
- **Đồng bộ trạng thái Agent**: `AgentState` trong LangGraph cần lưu trữ các trường filter động và thông tin trace token để chuyển tiếp về API response.

---

## 2. Đánh giá Khung cơ sở & Chọn lựa Công nghệ (Starter Template & Technology Stack)

### 2.1 Lựa chọn Khung cơ sở (Selected Foundation)
- **Lựa chọn**: Khung mã nguồn Brownfield hiện tại (Custom Brownfield Foundation).
- **Lý do**: Mã nguồn hiện tại đã phát triển sẵn logic cốt lõi. Việc khởi tạo từ đầu là không cần thiết. Hệ thống sẽ được mở rộng trực tiếp để hỗ trợ n8n, VLM và tải file PDF.

### 2.2 Các thành phần công nghệ được phê duyệt (Approved Tech Stack)
- **Backend**: Python 3.11+ / FastAPI (0.137.1) / LangGraph (>=0.0.30).
- **Frontend**: Streamlit (1.58.0) tích hợp bộ upload file `st.file_uploader` và nút tải file gốc.
- **Tự động hóa (Scraping/Crawling)**: n8n Docker image chính thức (`docker.n8n.io/n8nio/n8n`).
- **Mô hình VLM**: `llama-3.2-11b-vision-preview` thông qua Groq Cloud API (cấu hình mở rộng cắm rút để hỗ trợ self-host Hugging Face models sau này).
- **Cơ sở dữ liệu**:
  - PostgreSQL 15 (Metadata & n8n state).
  - Qdrant (Vector DB).
  - Redis 7-alpine (Bộ nhớ hội thoại / Chat History).
- **Bộ nhớ lưu trữ dùng chung (Shared Storage Volume)**: Volume Docker `pdf_storage` ánh xạ đến `/app/shared_pdfs` trong container `api` và `/data/pdfs` trong container `n8n`.

---

## 3. Quyết định Kiến trúc Cốt lõi (Core Architectural Decisions)

### 3.1 Kiến trúc Dữ liệu & Lưu trữ (Data Architecture)
- **Lưu trữ Metadata (PostgreSQL)**:
  - Bảng `documents`: Lưu thông tin file PDF (`id`, `file_name`, `file_path`, `source_url`, `ngay_tao`).
  - Khi n8n tải file về, nó ghi nhận metadata vào bảng này và kích hoạt backend nạp vector.
- **Lưu trữ Vector (Qdrant)**:
  - Payload cấu hình: `doc_id`, `so_hieu`, `loai_van_ban`, `nam_ban_hanh`, `content`.
  - Thực hiện Pre-filtering qua bộ lọc metadata để tối ưu hóa tìm kiếm trước khi so khớp vector.
- **Shared Storage (Volume)**:
  - Volume `pdf_storage` dùng chung cho `api` và `n8n` container để lưu trữ và tải tệp PDF gốc.

### 3.2 Luồng xử lý Đa phương tiện & VLM (Vision & Agent Workflow)
- **Mô hình VLM**: Hỗ trợ cắm rút thông qua VLM Service Wrapper. Tạm thời sử dụng API Groq (`llama-3.2-11b-vision-preview`), cho phép dễ dàng chuyển đổi sang self-hosted Hugging Face models (như Qwen2-VL, vLLM endpoint) bằng cấu hình `.env`.
- **Định nghĩa API endpoint `/chat`**:
  - Giao thức: `POST` / `multipart/form-data`.
  - Tham số: `message` (text), `image` (file upload - optional), `session_id` (str), `filters` (JSON string - bộ lọc metadata).
- **Định tuyến LangGraph**:
  - Nhánh có hình ảnh: Node `VLM Analyzer` nhận ảnh -> trích xuất văn bản/ngữ cảnh -> chuyển câu hỏi tinh chỉnh sang `Retriever` để truy vấn luật -> `Generator` tổng hợp -> `Judge` thẩm định.
  - Nhánh không có hình ảnh: Chạy RAG thông thường.

### 3.3 Tải file PDF trực tiếp (PDF Serving)
- **Endpoint Backend**: `GET /documents/{doc_id}/pdf` trả về file PDF gốc dưới dạng `FileResponse` từ volume `pdf_storage` kèm header `Content-Disposition: attachment`.
- **Giao diện Frontend**: Nút `Tải PDF gốc` sử dụng `st.download_button` xuất hiện cạnh các trích dẫn/citation.

### 3.4 Đóng gói Hạ tầng & CI/CD
- **Docker Compose**: Chạy 6 dịch vụ: `fe`, `api`, `postgres`, `qdrant`, `redis`, và `n8n`.
- **CI/CD**: GitHub Actions tự động linting (PEP 8), chạy pytest và build thử Docker Image.

---

## 4. Mẫu triển khai & Quy tắc nhất quán (Implementation Patterns & Consistency Rules)

### 4.1 Quy tắc đặt tên (Naming Patterns)
- **Cơ sở dữ liệu (PostgreSQL)**:
  - Tên bảng: snake_case, số nhiều. Ví dụ: `documents`.
  - Tên cột: snake_case, chữ thường. Ví dụ: `file_name`, `source_url`.
- **API Endpoints (FastAPI)**:
  - Sử dụng RESTful style, snake_case. Ví dụ: `/api/v1/chat`, `/api/v1/ingest`, `/api/v1/documents/{doc_id}/pdf`.
  - JSON payload fields: snake_case. Ví dụ: `{"session_id": "123", "filters": "..."}`.
- **Mã nguồn (Python)**:
  - Module/File: snake_case. Ví dụ: `vlm_service.py`, `pdf_parser.py`.
  - Class/Model: PascalCase. Ví dụ: `VLMServiceWrapper`, `DocumentState`.
  - Biến & Hàm: snake_case. Ví dụ: `get_document_pdf()`.

### 4.2 Cấu trúc dự án & Tổ chức mã nguồn (Structure Patterns)
- **Thư mục kiểm thử**: Đặt trong thư mục `tests/` ở gốc dự án, được phân tách rõ ràng thành `test_api.py`, `test_agent.py`.
- **Module dịch vụ VLM**:
  - Đóng gói toàn bộ logic gọi VLM trong `agent/vlm_service.py` bằng lớp `VLMServiceWrapper`.
  - Không được hardcode gọi API Groq trực tiếp trong các Node của Graph để dễ dàng tráo đổi sang các model tự host trên Hugging Face.

### 4.3 Định dạng Dữ liệu & Trao đổi API (Format Patterns)
- **API thành công**: `{"status": "success", "data": ...}`.
- **API thất bại**: Trả về thông qua Exception Handler của FastAPI:
  `{"status": "error", "error": {"message": "Mô tả lỗi tiếng Việt", "code": HTTP_STATUS_CODE}}`.

### 4.4 Quản lý trạng thái & Xử lý lỗi (Process Patterns)
- **Đồng bộ LangGraph State**: Trạng thái Graph (`AgentState`) kế thừa `TypedDict`. Cập nhật trạng thái bằng cách trả về một dict mới chứa các key cần thay thế (immutable state updates).
- **Xử lý Timeout / Lỗi VLM**: Nếu VLM API bị timeout (quá 10 giây), wrapper phải tự động raise exception để Graph Node chuyển sang nhánh RAG thông thường chỉ sử dụng text nhằm duy trì dịch vụ.

---

## 5. Cấu trúc Thư mục & Ranh giới Kiến trúc (Project Structure & Boundaries)

### 5.1 Sơ đồ Cấu trúc Thư mục Dự án (Project Directory Tree)
```
vietnamese-legal-compliance/
├── .env                  # Biến cấu hình môi trường chạy cục bộ (không commit)
├── .env.example          # Tệp biến môi trường mẫu
├── .gitignore            # Bỏ qua logs, __pycache__, .env, pdf_storage
├── docker-compose.yml    # Thiết lập 6 containers (api, fe, postgres, qdrant, redis, n8n)
├── requirements.txt      # Thư viện Python (FastAPI, Streamlit, LangGraph, Qdrant-client, etc.)
├── README.MD             # Hướng dẫn chạy và deploy dự án
├── api/
│   ├── Dockerfile        # Dockerfile multi-stage cho FastAPI Backend
│   ├── main.py           # Khởi chạy FastAPI App & Đăng ký routes
│   └── routes.py         # Các endpoints: POST /chat, POST /ingest, GET /documents/{id}/pdf
├── fe/
│   ├── Dockerfile        # Dockerfile cho Streamlit Frontend
│   ├── app.py            # Streamlit UI (khung chat, upload, bộ lọc sidebar, trace viewer)
│   └── api_client.py     # Logic kết nối API Backend qua HTTP requests
├── agent/
│   ├── __init__.py
│   ├── graph.py          # Định nghĩa cấu trúc LangGraph (nodes, conditional edges)
│   ├── nodes.py          # Logic chi tiết các Node (Retriever, Generator, Judge, VLM Analyzer)
│   ├── state.py          # Định nghĩa cấu trúc dữ liệu AgentState
│   └── vlm_service.py    # Wrapper gọi mô hình VLM (Groq API / Hugging Face local model)
├── ingestion/
│   ├── __init__.py
│   ├── pdf_parser.py     # Đọc PDF, cắt nhỏ văn bản, kiểm tra Magic Bytes và xử lý OCR
│   ├── embedder.py       # Tạo dense vector tương đồng (Sentence-Transformers)
│   ├── bm25_indexer.py   # Lập chỉ mục BM25 phục vụ Hybrid Search
│   ├── hybrid_search.py  # Thực thi tìm kiếm lai kết hợp Qdrant + BM25
│   └── init_db.py        # Khởi tạo database PostgreSQL và Collections Qdrant
├── tests/
│   ├── __init__.py
│   ├── test_api.py       # Integration tests cho REST API endpoints
│   └── test_agent.py     # Unit/Integration tests cho LangGraph workflow
└── .github/
    └── workflows/
        └── ci.yml        # Tệp cấu hình GitHub Actions (ruff lint, pytest, docker build test)
```

### 5.2 Ranh giới Tích hợp & Kiểm soát Biên (Architectural Boundaries & Edge Cases)
- **Giao tiếp Frontend - Backend**: Streamlit (`fe/app.py`) tuyệt đối không import trực tiếp DB hoặc Agent. Mọi tương tác phải đi qua `fe/api_client.py` gọi HTTP đến `/api/v1/...`.
- **Giao tiếp n8n - Backend**: Sau khi tải và lưu PDF vào volume chia sẻ `/pdf_storage`, n8n sẽ gọi `POST /api/v1/ingest` để API backend thực thi pipeline nạp vector bất đồng bộ.
- **Xử lý tệp tải lên (Corrupt/Empty File)**: `ingestion/pdf_parser.py` sẽ kiểm tra Magic Bytes của tệp trước khi ghi vào Shared Volume. Streamlit giới hạn kích thước tải lên tối đa là 4MB (ảnh) và 20MB (PDF).
- **Xử lý PDF dạng quét (Scanned PDF)**: Nếu văn bản trích xuất từ PDF quá ngắn (<100 ký tự/trang), hệ thống sẽ đánh dấu `ocr_required` trong DB và kích hoạt VLM Reader phân tích ảnh trang thay vì bỏ qua.
- **Chống trùng lặp (Dedup)**: DB PostgreSQL sẽ kiểm tra mã băm SHA-256 của file tải lên; bỏ qua và không tạo vector nếu mã băm đã tồn tại.
- **Kiểm soát Payload VLM**: Streamlit frontend sử dụng `Pillow` tự động nén/resize ảnh xuống mức FullHD (JPEG 80%) trước khi gửi đi nếu kích thước vượt ngưỡng.
- **Tính sẵn sàng của container**: Cấu hình `depends_on` với `condition: service_healthy` được thiết lập trong `docker-compose.yml`. Backend sử dụng thư viện `tenacity` để tự động kết nối lại 5 lần nếu DB hoặc Vector Store chưa sẵn sàng.

---

## 6. Kết quả Kiểm định Kiến trúc (Architecture Validation Results)

### 6.1 Kiểm định tính đồng nhất (Coherence Validation) ✅
- **Tương thích Quyết định**: Các công nghệ đã chọn (FastAPI, Streamlit, LangGraph, Qdrant, PostgreSQL, Redis, n8n) có độ trưởng thành cao và hoạt động tốt cùng nhau trong môi trường Docker Network nội bộ. Không có xung đột phiên bản.
- **Tính Nhất quán của Mẫu**: Các quy tắc đặt tên (snake_case) đồng nhất từ SQL Database, FastAPI endpoints đến các biến/hàm Python.
- **Căn chỉnh Cấu trúc**: Cấu trúc thư mục phân tách rõ rệt (api, fe, agent, ingestion) tương ứng hoàn toàn với các ranh giới dịch vụ được định nghĩa.

### 6.2 Kiểm định mức độ bao phủ Yêu cầu (Requirements Coverage Validation) ✅
- **Yêu cầu Chức năng (FRs)**:
  - **[FR-1] Metadata Filtering**: Hỗ trợ qua query params `/chat` truyền bộ lọc xuống Qdrant payload filters.
  - **[FR-2] Smart Citation**: Tách trích dẫn ở LangGraph nodes và Streamlit UI hiển thị qua `st.expander`.
  - **[FR-3] Developer Debug Mode**: Lưu log chạy và token dùng vào `AgentState` để hiển thị trên Streamlit.
  - **[FR-4] Full Dockerization**: Cấu hình chi tiết qua 6 container trong `docker-compose.yml`.
  - **[FR-5] CI/CD Pipeline**: GitHub Actions tự động kiểm thử và kiểm tra code style.
- **Yêu cầu mở rộng (VLM & n8n)**:
  - Hỗ trợ ảnh tại `/chat` đa phương tiện (VLM node trong LangGraph).
  - Tự động hóa crawl qua n8n và đồng bộ dữ liệu PDF qua shared volume `/pdf_storage`.
  - Endpoint `GET /documents/{doc_id}/pdf` hỗ trợ tải tệp tin PDF gốc.
- **Yêu cầu Phi Chức năng (NFRs)**: Bảo mật (tách DB khỏi FE), Hiệu năng (lưu cache lịch sử hội thoại trên Redis), khả năng bảo trì (VLM service wrapper tách biệt).

### 6.3 Đánh giá mức độ sẵn sàng triển khai (Implementation Readiness) ✅
- **Đầy đủ quyết định**: Đầy đủ các phiên bản thư viện cốt lõi, cơ sở dữ liệu và công cụ CI/CD.
- **Phân tích khoảng trống (Gap Analysis)**:
  - *Khoảng trống nghiêm trọng (Critical)*: Không có.
  - *Khoảng trống nhỏ (Deferred)*: Lựa chọn mô hình VLM tự chạy (self-hosted) cụ thể trên Hugging Face. Việc này sẽ được nghiên cứu và quyết định sau dựa trên benchmark thực tế, không ảnh hưởng đến kiến trúc API/Graph hiện tại (vì đã dùng VLM Service Wrapper trừu tượng).

### 6.4 Bảng kiểm hoàn thiện Kiến trúc (Completeness Checklist)
- [x] Phân tích bối cảnh dự án chi tiết
- [x] Đánh giá quy mô & độ phức tạp hệ thống
- [x] Xác định các ràng buộc kỹ thuật
- [x] Ánh xạ các điểm giao thoa bảo mật/hiệu năng
- [x] Tài liệu hóa các quyết định kèm số phiên bản
- [x] Lựa chọn & xác định đầy đủ Tech Stack
- [x] Thiết lập ranh giới giao tiếp & tích hợp
- [x] Giải quyết hiệu năng và caching (Redis)
- [x] Thiết lập quy tắc đặt tên (Database, API, Code)
- [x] Quy định cấu trúc tệp tin/thư mục và test
- [x] Quy định định dạng JSON API (snake_case)
- [x] Xây dựng cơ chế xử lý lỗi/timeout của VLM và Fallback RAG
- [x] Định nghĩa sơ đồ cây thư mục chi tiết
- [x] Phân định ranh giới kết nối của các thành phần
- [x] Xác định các điểm tích hợp (n8n, Shared Volume)
- [x] Ánh xạ yêu cầu chức năng vào từng file cụ thể

### 6.5 Đánh giá Mức độ Sẵn sàng & Bàn giao
- **Trạng thái:** **SẴN SÀNG TRIỂN KHAI (READY FOR IMPLEMENTATION)** (Tất cả 16/16 mục kiểm tra đều đạt yêu cầu).
- **Độ tự tin:** **Rất cao (High)**.
- **Nguyên tắc bàn giao cho AI Agent:**
  - Tuyệt đối tuân thủ sơ đồ thư mục và ranh giới đã quy định.
  - Các node LangGraph không gọi trực tiếp API Groq mà phải thông qua lớp wrapper `VLMServiceWrapper` để dễ cắm rút sau này.
  - Viết test song song với tính năng (`tests/test_api.py`, `tests/test_agent.py`).
