---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - '_bmad-output/planning-artifacts/prds/prd-vietnamese-legal-compliance-2026-06-17/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
---

# vietnamese-legal-compliance - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for vietnamese-legal-compliance, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

- **FR-1**: Cung cấp các widget lựa chọn lọc metadata trên Sidebar (Loại văn bản, Năm ban hành, Cơ quan ban hành).
- **FR-2**: Khi người dùng gửi tin nhắn, các giá trị bộ lọc đã chọn phải được đóng gói vào payload gửi tới API `/chat`.
- **FR-3**: Bộ lọc metadata phải được áp dụng trực tiếp trong Hybrid Search Node của LangGraph để thu hẹp không gian tìm kiếm.
- **FR-4**: Hệ thống tự động phân tích AI để bóc tách trích dẫn dạng chuẩn `[Luật... - Điều X - Khoản Y]`.
- **FR-5**: Streamlit hiển thị trích dẫn dưới dạng các nút bấm/link nhỏ. Khi bấm vào, nội dung trích dẫn gốc đầy đủ sẽ hiển thị trong một bảng phụ (`st.expander` hoặc Sidebar phụ) để không làm gián đoạn luồng chat.
- **FR-6**: Trên Sidebar Streamlit có nút toggle "Developer Mode".
- **FR-7**: Khi chế độ "Developer Mode" được bật, dưới mỗi câu trả lời của AI sẽ xuất hiện một Expander tên là `🔍 Nhật ký hoạt động của Agent`.
- **FR-8**: Hiển thị sơ đồ dạng văn bản/Mermaid hoặc JSON Trace ghi nhận các node đã chạy, thời gian xử lý, số token và kết quả phán quyết của Judge node.
- **FR-9**: Viết `Dockerfile` riêng cho API Backend và Streamlit Frontend, sử dụng multi-stage build.
- **FR-10**: Cập nhật `docker-compose.yml` để liên kết 5 container (postgres, qdrant, redis, api, fe) qua mạng nội bộ.
- **FR-11**: GitHub Actions CI/CD Pipeline tự động kích hoạt khi có pull request hoặc push vào nhánh `main`.
- **FR-12**: CI/CD chạy công cụ kiểm tra cú pháp và PEP 8 style guide.
- **FR-13**: CI/CD chạy tự động bộ unit/integration test sử dụng `pytest`.

### NonFunctional Requirements

- **NFR-1**: Phản hồi API `/chat` thông thường phải đạt dưới 5 giây. Đối với câu hỏi phức tạp cần tự sửa lỗi, tối đa không quá 15 giây.
- **NFR-2**: Pipeline nạp tài liệu (parsing, chunking, embedding) phải chạy bất đồng bộ qua FastAPI Background Tasks.
- **NFR-3**: Cô lập mạng: FastAPI Backend và Streamlit Frontend giao tiếp thuần túy qua HTTP RESTful API. Không kết nối DB trực tiếp từ Streamlit.
- **NFR-4**: Bảo mật đầu vào: Loại bỏ nguy cơ tấn công XSS trên Streamlit bằng cách tuyệt đối không sử dụng `unsafe_allow_html=True` cho dữ liệu nhập.
- **NFR-5**: Bảo mật cấu hình: Khóa API và mật khẩu phải nạp từ biến môi trường (`.env`), không hardcode.
- **NFR-6**: Tính module của Frontend: Tách biệt UI với logic truy vấn, Streamlit điều khiển qua `api_client.py`.
- **NFR-7**: Sao lưu & Tự phục hồi: Các dịch vụ DB (PostgreSQL, Qdrant, Redis) trong Docker Compose phải định nghĩa volumes lưu trữ bền vững và cấu hình `restart: unless-stopped`.

### Additional Requirements

- Khung cơ sở (Starter Template): Sử dụng khung mã nguồn Brownfield hiện tại (Custom Brownfield Foundation). Hệ thống được mở rộng để thêm n8n, hỗ trợ tải file PDF và tích hợp mô hình VLM (Lưu ý cho Epic 1 Story 1).
- Tích hợp VLM: Hỗ trợ nạp mô hình Vision (VLM) cho ảnh qua API `/chat` và LangGraph (VLM Analyzer node).
- VLM Wrapper: Không hardcode Groq API, sử dụng `VLMServiceWrapper` để dễ dàng đổi model tự host.
- Giao tiếp n8n: n8n tải file về lưu vào shared volume `/pdf_storage`, sau đó gọi `POST /api/v1/ingest` để API backend nạp vector.
- Xử lý tệp PDF: API `GET /documents/{doc_id}/pdf` để phục vụ xem/tải file từ shared volume.
- Kiểm tra loại tệp: `pdf_parser.py` cần kiểm tra Magic Bytes của tệp trước khi xử lý, chống tải tệp lỗi.
- Xử lý Scanned PDF: Đánh dấu `ocr_required` và sử dụng VLM Reader nếu nội dung quá ngắn (<100 ký tự/trang).
- Chống trùng lặp (Dedup): PostgreSQL kiểm tra hash SHA-256 của file tải lên; bỏ qua nạp vector nếu đã có.
- Trạng thái Agent: Cập nhật `AgentState` sử dụng immutability.
- Xử lý Lỗi/Timeout VLM: Nếu gọi VLM API timeout (>10s), wrapper raise exception để Graph tự động fallback sang nhánh RAG thuần.
- Quản lý cấu hình: Quản lý biến cấu hình qua tệp `.env`. Cả ứng dụng trực tiếp lẫn docker-compose đều có thể đọc.
- Tự động khôi phục kết nối: Backend dùng thư viện `tenacity` tự động kết nối lại 5 lần nếu DB/Vector Store chưa sẵn sàng.

### UX Design Requirements

N/A

### FR Coverage Map

FR-1: Epic 3 - Sidebar cung cấp widget lựa chọn lọc metadata
FR-2: Epic 3 - Đóng gói giá trị lọc vào payload API `/chat`
FR-3: Epic 3 - Áp dụng filter metadata vào Qdrant Hybrid Search
FR-4: Epic 4 - Tự động phát hiện và bóc tách trích dẫn định dạng chuẩn
FR-5: Epic 4 - Hiển thị nội dung nguyên văn trích dẫn gốc qua st.expander
FR-6: Epic 5 - Thêm nút toggle "Developer Mode" trên UI
FR-7: Epic 5 - Hiển thị bảng "Nhật ký hoạt động của Agent"
FR-8: Epic 5 - Hiển thị JSON Trace / Sơ đồ Node, thời gian, số lượng token
FR-9: Epic 1 - Multi-stage Dockerfile cho Frontend và Backend
FR-10: Epic 1 - Cập nhật docker-compose.yml liên kết 5 containers
FR-11: Epic 1 - Thiết lập GitHub Actions kích hoạt khi có PR
FR-12: Epic 1 - Tự động chạy PEP 8 linting trên CI/CD
FR-13: Epic 1 - Tự động chạy Pytest trên CI/CD

## Epic List

### Epic 1: Triển khai Nền tảng & Tự động hóa (Platform Deployment & Automation)
Quản trị viên (Admin/Dev) có thể khởi chạy toàn bộ hệ thống (Frontend, Backend, Databases) bằng một lệnh duy nhất và đảm bảo chất lượng mã nguồn tự động.
**FRs covered:** FR-9, FR-10, FR-11, FR-12, FR-13

### Story 1.1: Cấu hình Docker Compose cho các dịch vụ phụ trợ

As a Quản trị viên hệ thống,
I want cập nhật `docker-compose.yml` để cấu hình Postgres, Qdrant, Redis, n8n cùng mạng nội bộ và thiết lập volumes,
So that tôi có thể khởi chạy và lưu trữ dữ liệu bền vững cho toàn bộ các database bằng một lệnh duy nhất.

**Acceptance Criteria:**

**Given** môi trường Docker trên máy chủ
**When** chạy lệnh `docker-compose up`
**Then** các container PostgreSQL, Qdrant, Redis và n8n phải được khởi tạo thành công và giao tiếp nội bộ qua chung một network
**And** các persistent volumes (kể cả volume chia sẻ `/pdf_storage`) phải được mount chính xác và cấu hình an toàn từ tệp `.env`.

### Story 1.2: Đóng gói API Backend và Streamlit Frontend

As a Lập trình viên,
I want viết multi-stage Dockerfile cho FastAPI (Backend) và Streamlit (Frontend), sau đó đưa vào Compose,
So that toàn bộ ứng dụng chính chạy trong môi trường container cô lập và bảo mật.

**Acceptance Criteria:**

**Given** mã nguồn FE và BE
**When** build Docker image
**Then** kích thước image phải được tối ưu thông qua kỹ thuật multi-stage build
**And** Frontend kết nối thành công tới API Backend bằng internal hostname (ví dụ: `http://api:8000`)
**And** Backend kết nối được tới các dịch vụ DB (Qdrant, Postgres, Redis) dựa trên cấu hình retry `tenacity`.

### Story 1.3: Tích hợp luồng CI/CD (GitHub Actions)

As a Quản trị viên dự án,
I want cấu hình GitHub Actions pipeline tự động chạy linting và kiểm thử,
So that đảm bảo mã nguồn đẩy lên nhánh `main` không bị lỗi cú pháp PEP 8 và vượt qua bộ test `pytest`.

**Acceptance Criteria:**

**Given** tệp `.github/workflows/ci.yml`
**When** có Push hoặc Pull Request tạo mới vào nhánh `main`
**Then** GitHub Actions tự động kích hoạt và chạy công cụ kiểm tra phong cách mã (linter)
**And** sau khi linting thành công, pipeline tiếp tục chạy bộ test tự động qua lệnh `pytest`
**And** pipeline sẽ báo lỗi đỏ (fail) nếu phát hiện bất kỳ lỗi cú pháp hoặc test nào bị trượt.

### Epic 2: Quản lý & Đồng bộ Dữ liệu Pháp luật (Legal Data Management & Ingestion)
Quản trị viên có thể vận hành luồng thu thập tài liệu tự động qua n8n; hệ thống tự động xử lý PDF (kể cả PDF scan dùng VLM) và nạp vào Vector DB ngầm (background) mà không làm đơ hệ thống.
**FRs covered:** N/A (Kiến trúc bổ sung & NFRs)

### Story 2.1: API nạp dữ liệu chạy ngầm (Background Ingestion API)

As a Quản trị viên,
I want hệ thống cung cấp API `POST /api/v1/ingest` xử lý bất đồng bộ,
So that n8n có thể gọi API sau khi tải file mà không làm treo hệ thống khi xử lý PDF dung lượng lớn.

**Acceptance Criteria:**

**Given** endpoint `/api/v1/ingest` đã sẵn sàng
**When** n8n gửi yêu cầu nạp một file PDF mới
**Then** API phải phản hồi HTTP 202 Accepted ngay lập tức và đẩy tác vụ xử lý vào `BackgroundTasks` của FastAPI
**And** tạo một bản ghi trạng thái ban đầu (`pending`) trong bảng `documents` của PostgreSQL.

### Story 2.2: Pipeline Trích xuất & Lập chỉ mục PDF (PDF Parsing & Indexing)

As a Hệ thống Backend,
I want tự động đọc file PDF, kiểm tra bảo mật, cắt chunk và lập chỉ mục Vector/BM25,
So that dữ liệu được chuẩn bị sẵn sàng và tối ưu nhất cho Hybrid Search.

**Acceptance Criteria:**

**Given** tệp PDF đã nằm trong `/pdf_storage` và task ngầm đang chạy
**When** pipeline bắt đầu xử lý tệp
**Then** hệ thống phải kiểm tra mã băm SHA-256; nếu tệp đã tồn tại trong DB thì bỏ qua (chống trùng lặp)
**And** kiểm tra Magic Bytes của tệp để đảm bảo đó là file PDF hợp lệ, không bị lỗi
**And** sau khi tạo Vector Embedding và lưu vào Qdrant, phải cập nhật file chỉ mục BM25 an toàn (sử dụng cơ chế file lock để tránh xung đột).

### Story 2.3: Xử lý PDF dạng quét bằng VLM (Scanned PDF OCR fallback)

As a Quản trị viên,
I want hệ thống tự nhận diện các file PDF dạng ảnh quét (scan) và kích hoạt VLM để trích xuất chữ,
So that các văn bản pháp luật cũ (chỉ có bản scan) vẫn được lập chỉ mục và tìm kiếm được.

**Acceptance Criteria:**

**Given** một tệp PDF dạng quét thuần túy (không có lớp text ẩn)
**When** đưa qua bước trích xuất văn bản (Parsing)
**Then** hệ thống phát hiện lượng text lấy được quá ngắn (< 100 ký tự/trang) và tự động bật cờ `ocr_required` trong DB
**And** gọi `VLMServiceWrapper` để đọc chữ từ ảnh của các trang đó trước khi tiến hành cắt chunk và embedding.

### Epic 3: Lọc Tìm kiếm & Tư vấn Pháp lý (Filtered Search & Legal Consultation)
Người dùng cuối (Auditor/Compliance Officer) có thể tương tác với trợ lý AI và thiết lập bộ lọc (Năm, Cơ quan, Loại luật) để giới hạn ngữ cảnh, giúp AI tư vấn chính xác, tránh nhầm luật cũ.
**FRs covered:** FR-1, FR-2, FR-3

### Story 3.1: Giao diện Chat & Lọc Metadata (Streamlit UI)

As a Người dùng cuối,
I want giao diện trò chuyện có thanh bên (Sidebar) chứa các bộ lọc như Loại văn bản, Năm, Cơ quan,
So that tôi có thể thiết lập ngữ cảnh tài liệu để giới hạn phạm vi tìm kiếm theo ý muốn.

**Acceptance Criteria:**

**Given** ứng dụng Streamlit đang mở
**When** người dùng chọn các bộ lọc và nhấn gửi câu hỏi
**Then** giá trị bộ lọc được đóng gói an toàn cùng câu hỏi vào payload gọi tới API `/chat`
**And** dữ liệu đầu vào được render an toàn trên giao diện, tuyệt đối không dùng `unsafe_allow_html=True` để chống tấn công XSS.

### Story 3.2: Cơ chế Hybrid Search kết hợp Metadata (Qdrant & LangGraph)

As a Hệ thống Backend,
I want áp dụng bộ lọc từ giao diện trực tiếp vào câu truy vấn của Qdrant bên trong LangGraph,
So that không gian tìm kiếm Vector được thu hẹp trước, tăng độ chính xác của tài liệu ngữ cảnh trả về.

**Acceptance Criteria:**

**Given** request tới `/chat` chứa các tham số lọc metadata hợp lệ
**When** đồ thị LangGraph thực thi tới Node `Retriever`
**Then** hệ thống tự động sinh ra cấu trúc truy vấn Qdrant (`models.Filter`) khớp chính xác với payload
**And** kết quả RAG trả về bắt buộc chỉ nằm trong phạm vi các tài liệu thỏa mãn điều kiện lọc, kết hợp giữa Vector và BM25.

### Story 3.3: Tác tử xử lý ảnh đa phương thức (Multimodal VLM Analyzer)

As a Người dùng cuối,
I want có thể tải ảnh chụp tài liệu pháp lý lên trong khung chat,
So that AI có thể đọc nội dung ảnh và tư vấn dựa trên ngữ cảnh đó kết hợp tra cứu luật.

**Acceptance Criteria:**

**Given** giao diện Streamlit hỗ trợ tải tệp đính kèm dạng hình ảnh
**When** người dùng gửi tin nhắn kèm hình ảnh
**Then** Node `VLM Analyzer` trong LangGraph được kích hoạt để phân tích hình ảnh thông qua `VLMServiceWrapper`
**And** trạng thái hệ thống (`AgentState`) được cập nhật an toàn theo cơ chế immutable
**And** nếu gọi API VLM bị timeout (quá 10s), wrapper phải raise exception để LangGraph tự động fallback sang nhánh xử lý RAG thuần túy (bỏ qua ảnh) thay vì làm sập toàn bộ request.

### Epic 4: Đối chiếu Trích dẫn Minh bạch (Transparent Citation Verification)
Người dùng cuối có thể click vào các trích dẫn pháp luật xuất hiện trong câu trả lời (VD: `[Luật... - Điều X]`) để đọc nguyên văn gốc ngay trên giao diện mà không bị gián đoạn luồng chat.
**FRs covered:** FR-4, FR-5

### Story 4.1: Bóc tách và chuẩn hóa trích dẫn (AI Citation Formatting)

As a Hệ thống Backend,
I want LangGraph phân tích câu trả lời thô và định dạng lại các trích dẫn theo chuẩn nhất quán (VD: `[Luật X - Điều Y]`),
So that giao diện Frontend có thể dễ dàng dùng Regex để nhận diện và biến chúng thành các liên kết (link) tương tác.

**Acceptance Criteria:**

**Given** câu trả lời nháp từ mô hình (Generator Node)
**When** đồ thị LangGraph đưa dữ liệu qua Node `Formatter`
**Then** hệ thống sử dụng một prompt ngắn gọn để bắt LLM định dạng lại mọi trích dẫn pháp lý theo một cấu trúc thống nhất
**And** trả về kết quả cuối cùng cho API cùng metadata về các nguồn tài liệu đã dùng.

### Story 4.2: Giao diện Trình xem Trích dẫn Nguyên văn (Inline Citation Viewer)

As a Người dùng cuối,
I want các trích dẫn trong câu trả lời hiển thị dưới dạng nút bấm/expander mở rộng để xem nội dung gốc,
So that tôi có thể đối chiếu nguyên văn điều luật mà không bị gián đoạn hay phải cuộn (scroll) mất luồng chat.

**Acceptance Criteria:**

**Given** giao diện người dùng Streamlit đang hiển thị câu trả lời của AI
**When** câu trả lời chứa các cụm trích dẫn đã được chuẩn hóa (từ Story 4.1)
**Then** Streamlit chuyển đổi các cụm này thành dạng UI có thể tương tác
**And** khi người dùng click vào, nội dung đoạn văn bản gốc (được cung cấp sẵn từ Context của RAG) sẽ bung ra trong `st.expander` hoặc hiển thị bên sidebar phụ.

### Story 4.3: API Trích xuất & Phục vụ Tệp PDF gốc (PDF Serving API)

As a Lập trình viên Frontend,
I want Backend cung cấp một API `GET /documents/{doc_id}/pdf` để đọc file gốc,
So that tôi có thể nhúng trực tiếp bản PDF gốc (có chữ ký/dấu đỏ) vào UI cho người dùng đối chiếu khi cần bằng chứng pháp lý.

**Acceptance Criteria:**

**Given** một tệp PDF đang được lưu trữ an toàn trong shared volume `/pdf_storage`
**When** người dùng yêu cầu xem tệp và Frontend gọi API `/documents/{doc_id}/pdf`
**Then** FastAPI stream nội dung file PDF về phía Client theo chunks
**And** phản hồi có HTTP Headers đúng định dạng (`application/pdf`) để trình duyệt có thể render trực tiếp thay vì chỉ tải xuống.

### Epic 5: Giám sát & Gỡ lỗi Luồng suy luận (Reasoning Monitoring & Debugging)
Lập trình viên/Admin có thể bật "Developer Mode" để theo dõi trực quan luồng suy nghĩ của AI (thời gian, số token, các Node đã chạy) ngay trên UI, giúp tối ưu hóa hệ thống.
**FRs covered:** FR-6, FR-7, FR-8

### Story 5.1: Giao diện chuyển đổi Developer Mode (Developer Mode Toggle)

As a Quản trị viên / Lập trình viên,
I want có một công tắc "Developer Mode" trên thanh bên (Sidebar) của Streamlit,
So that tôi có thể dễ dàng chuyển đổi qua lại giữa giao diện người dùng bình thường và giao diện gỡ lỗi.

**Acceptance Criteria:**

**Given** thanh bên Streamlit
**When** tôi click bật/tắt công tắc "Developer Mode"
**Then** Streamlit lưu trạng thái này vào `st.session_state` an toàn
**And** cờ (flag) này sẽ quyết định việc giao diện có bung thêm các bảng thông tin kỹ thuật hay không.

### Story 5.2: API Trích xuất Dữ liệu Trace Log (Agent Tracing API Payload)

As a Lập trình viên hệ thống,
I want API `/chat` đóng gói cả dữ liệu ghi log của LangGraph (Trace Log) trả về cùng câu trả lời,
So that Frontend nhận được đầy đủ thông số kỹ thuật (thời gian chạy, số token tiêu thụ, quyết định của node Judge).

**Acceptance Criteria:**

**Given** chu trình LangGraph đã thực thi xong và có câu trả lời cuối
**When** API trả về HTTP Response cho Frontend
**Then** cấu trúc JSON trả về bao gồm nội dung chat VÀ một mảng `trace_log`
**And** mỗi item trong mảng `trace_log` phải chứa: Tên Node, Thời gian thực thi (ms), Số Token (nếu có gọi LLM) và trạng thái thành công/thất bại.

### Story 5.3: Trực quan hóa Nhật ký Hoạt động trên UI (Trace Visualization)

As a Lập trình viên,
I want hiển thị trực quan dữ liệu Trace Log nhận được thành các sơ đồ/bảng khi Developer Mode bật,
So that tôi có thể dễ dàng rà soát nút thắt hiệu năng (bottleneck) hoặc nhánh logic sai của Agent.

**Acceptance Criteria:**

**Given** Frontend nhận được payload API và chế độ `Developer Mode` đang bật (ON)
**When** Streamlit render kết quả trả lời
**Then** ngay bên dưới câu trả lời sẽ xuất hiện một Expander với tiêu đề `🔍 Nhật ký hoạt động của Agent`
**And** bên trong Expander hiển thị bảng thống kê rõ ràng (hoặc sơ đồ Mermaid tĩnh) mô tả thứ tự các Node đã chạy, chi phí token, và thời gian tiêu tốn.

