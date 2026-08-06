---
title: 'Vietnamese Legal Compliance Agent PRD'
status: 'final'
created: '2026-06-17'
updated: '2026-06-17'
---

# Product Requirement Document (PRD)

---

## 1. Tầm nhìn Sản phẩm & Mục tiêu Chiến lược (Product Vision & Objectives)

### 1.1 Tầm nhìn (Product Vision)
Xây dựng một trợ lý pháp lý AI thông minh chuyên biệt về Luật Công nghệ thông tin và An toàn thông tin mạng tại Việt Nam. Hệ thống sở hữu giao diện Streamlit module hóa hiện đại, cho phép tra cứu trích dẫn văn bản gốc trực quan, được vận hành bởi kiến trúc LangGraph tự sửa lỗi (CRAG + Self-Reflection) và sẵn sàng đóng gói triển khai tức thời thông qua Docker và quy trình CI/CD tự động.

### 1.2 Mục tiêu chiến lược (Objectives)
- **Mục tiêu 1 (Vận hành & Hạ tầng)**: Rút ngắn thời gian thiết lập môi trường phát triển và deploy xuống dưới 5 phút thông qua đóng gói Docker Compose toàn bộ dịch vụ (bao gồm Database, Vector DB, Redis, API Backend và Streamlit Frontend).
- **Mục tiêu 2 (Chất lượng mã nguồn)**: Đảm bảo độ ổn định của hệ thống thông qua tích hợp CI/CD tự động hóa toàn bộ quá trình linting và kiểm thử (`pytest`) trước khi đóng gói Docker Image.
- **Mục tiêu 3 (Trải nghiệm tra cứu chuyên sâu)**: Cung cấp tính năng xem trích dẫn gốc (Citation Viewer) và lọc tìm kiếm nâng cao (Metadata Filtering) giúp giảm tỷ lệ người dùng nghi ngờ thông tin AI sinh ra xuống mức thấp nhất.
- **Mục tiêu 4 (Khả năng giám sát)**: Cung cấp chế độ debug hiển thị chi tiết các bước chạy của Agent (Trace Log) giúp lập trình viên và quản trị viên dễ dàng gỡ lỗi luồng suy nghĩ của LangGraph.

---

## 2. Vai trò người dùng & Khả năng cốt lõi (User Roles & Core Capabilities)

### 2.1 Vai trò người dùng (User Roles)
Hệ thống sẽ phục vụ hai nhóm đối tượng chính:
- **Người dùng cuối / Chuyên viên tuân thủ (Auditor / Compliance Officer)**:
  - Mục tiêu: Tra cứu, đặt câu hỏi pháp lý để đánh giá sự tuân thủ IT của công ty.
  - Thao tác chính: Trò chuyện với trợ lý ảo, lọc tài liệu theo danh mục/năm, xem nội dung trích dẫn gốc của điều luật để đối chiếu.
- **Quản trị viên / Lập trình viên (Admin / Developer)**:
  - Mục tiêu: Quản lý cơ sở dữ liệu pháp luật, giám sát hiệu suất và gỡ lỗi hệ thống.
  - Thao tác chính: Upload tài liệu PDF mới, theo dõi trạng thái đồng bộ dữ liệu (ingestion pipeline), bật/tắt chế độ Trace Log để gỡ lỗi Agent, quản lý vận hành qua Docker và CI/CD.

### 2.2 Khả năng cốt lõi (Core Capabilities)
- **Khả năng 1 (Qdrant Metadata Filter)**: Hỗ trợ lọc tài liệu theo trường metadata (Loại văn bản, Năm, Cơ quan ban hành) trước khi tính tương đồng vector, giúp giới hạn phạm vi tìm kiếm chính xác.
- **Khả năng 2 (Smart Citation)**: Tự động phát hiện ký tự điều khoản trích dẫn trong câu trả lời và liên kết hiển thị nội dung gốc của đoạn văn bản đó trên UI.
- **Khả năng 3 (LangGraph Tracer)**: Ghi lại trạng thái đầu vào/đầu ra và các quyết định định tuyến của LangGraph ở dạng logs hoặc sơ đồ luồng hiển thị trên UI.
- **Khả năng 4 (Đóng gói một lệnh & Kiểm thử tự động)**: Triển khai nhanh chóng toàn bộ app bằng Docker Compose, đồng thời tự động kiểm thử tích hợp API qua GitHub Actions CI/CD.

---

## 3. Yêu cầu chức năng (Functional Requirements - FRs)

### 3.1 Giao diện Chat & Lọc Tìm Kiếm Nâng Cao (Streamlit Interface & Filtering)
- **[FR-1] Metadata Filtering**:
  - **FR-1.1**: Sidebar cung cấp các widget lựa chọn: "Loại văn bản" (Luật, Nghị định, Thông tư), "Năm ban hành" (Số/Dải năm), và "Cơ quan ban hành".
  - **FR-1.2**: Khi người dùng gửi tin nhắn, các giá trị bộ lọc đã chọn phải được đóng gói vào payload gửi tới API `/chat`.
  - **FR-1.3**: Bộ lọc metadata phải được áp dụng trực tiếp trong Hybrid Search Node của LangGraph (truyền filter sang Qdrant client để thu hẹp không gian tìm kiếm trước khi tính cosine similarity).

### 3.2 Bộ xem trích dẫn thông minh (Smart Citation Viewer)
- **[FR-2] Citation Links**:
  - **FR-2.1**: Hệ thống tự động phân tích câu trả lời của AI để phát hiện các mẫu trích dẫn dạng chuẩn như `[Luật... - Điều X - Khoản Y]`.
  - **FR-2.2**: Streamlit hiển thị trích dẫn dưới dạng các nút bấm/link nhỏ. Khi bấm vào, nội dung trích dẫn gốc đầy đủ tương ứng (truy xuất từ DB) sẽ hiển thị trong một bảng phụ (`st.expander` ngay dưới câu trả lời hoặc hiển thị ở Sidebar phụ) để tránh làm gián đoạn luồng chat chính.


### 3.3 Bảng giám sát vết Agent (Agent Execution Trace Viewer)
- **[FR-3] Developer Debug Mode**:
  - **FR-3.1**: Trên Sidebar Streamlit có nút toggle "Developer Mode".
  - **FR-3.2**: Khi chế độ này được bật, dưới mỗi câu trả lời của AI sẽ xuất hiện một Expander tên là `🔍 Nhật ký hoạt động của Agent`.
  - **FR-3.3**: Hiển thị sơ đồ dạng văn bản/Mermaid hoặc JSON Trace ghi nhận: node nào đã chạy (ví dụ: `Query Analyzer` -> `Retriever` -> `Judge`), thời gian xử lý từng node (ms), số lượng token sử dụng, và kết quả phán quyết của Judge node.

### 3.4 Docker hóa & Quy trình CI/CD tự động
- **[FR-4] Full Dockerization**:
  - **FR-4.1**: Viết `Dockerfile` riêng cho API Backend và Streamlit Frontend, sử dụng multi-stage build để giảm dung lượng image.
  - **FR-4.2**: Cập nhật `docker-compose.yml` để liên kết tất cả 5 container (`postgres`, `qdrant`, `redis`, `api`, `fe`) qua mạng network nội bộ, đảm bảo khởi động toàn bộ hệ thống bằng lệnh duy nhất.
- **[FR-5] CI/CD Pipeline (GitHub Actions)**:
  - **FR-5.1**: Tự động kích hoạt khi có pull request hoặc push vào nhánh `main`.
  - **FR-5.2**: Chạy công cụ kiểm tra cú pháp và PEP 8 style guide.
  - **FR-5.3**: Chạy tự động bộ unit/integration test sử dụng `pytest`.

---

## 4. Yêu cầu phi chức năng (Non-Functional Requirements - NFRs)

### 4.1 Hiệu năng & Khả năng đáp ứng (Performance)
- **[NFR-1] Phản hồi API**: Thời gian phản hồi của API tư vấn `/chat` thông thường phải đạt dưới 5 giây. Đối với các câu hỏi phức tạp cần LangGraph tự sửa lỗi (lặp lại Retriever/Generator), thời gian xử lý tối đa không được vượt quá 15 giây.
- **[NFR-2] Tác vụ ngầm (Background Tasks)**: Pipeline nạp tài liệu (PDF parsing, chunking, embedding) phải chạy bất động bộ qua FastAPI Background Tasks, đảm bảo Frontend không bị treo khi admin nhấn nút xử lý.

### 4.2 Bảo mật (Security)
- **[NFR-3] Cô lập mạng (Network Isolation)**: FastAPI Backend và Streamlit Frontend giao tiếp thuần túy qua giao thức HTTP RESTful API. Streamlit không có quyền kết nối trực tiếp đến PostgreSQL, Qdrant, hoặc Redis. Các DB này chỉ mở cổng nội bộ bên trong Docker Network của Compose.
- **[NFR-4] Bảo mật đầu vào (Input Sanitization)**: Loại bỏ nguy cơ tấn công XSS trên Streamlit bằng cách tuyệt đối không sử dụng `unsafe_allow_html=True` để hiển thị các dữ liệu động do người dùng nhập vào.
- **[NFR-5] Bảo mật cấu hình**: Các thông tin bảo mật như khóa API Groq (`GROQ_API_KEY`), mật khẩu PostgreSQL phải được nạp thông qua biến môi trường (Environment Variables) từ tệp `.env`, không được hardcode trong mã nguồn.

### 4.3 Khả năng bảo trì & Đóng gói (Maintainability & Deployability)
- **[NFR-6] Tính module của Frontend**: Streamlit UI phải được phân tách rõ ràng. Mã nguồn điều khiển giao diện (`app.py`) chỉ phụ thuộc vào `api_client.py` để tương tác với backend, không chứa logic nghiệp vụ hay truy vấn DB.
- **[NFR-7] Sao lưu & Tự phục hồi**: Các dịch vụ PostgreSQL, Qdrant, và Redis trong Docker Compose phải được định nghĩa volumes lưu trữ dữ liệu bền vững (persistent data) trên máy chủ host, đồng thời cấu hình restart policy là `unless-stopped` để tự khởi động lại khi gặp sự cố đột ngột.

---

## 5. Ranh giới hệ thống & Điểm tích hợp (System Boundaries & Integration Points)

### 5.1 Sơ đồ luồng dữ liệu (Data Flow Overview)
```mermaid
graph TD
    User([Người dùng]) <-->|HTTP/REST| FE[Streamlit Frontend]
    FE <-->|API /chat /upload /documents| BE[FastAPI Backend]
    BE <-->|Lịch sử chat & Session| Redis[(Redis Memory)]
    BE <-->|Lưu trữ metadata tài liệu| Postgres[(PostgreSQL)]
    BE <-->|Tìm kiếm Vector| Qdrant[(Qdrant Vector DB)]
    BE <-->|Tách từ tiếng Việt & Embed| NLP[Underthesea / Sentence-Transformers]
    BE <-->|LLM Queries| Groq[Groq Cloud API]
```

### 5.2 Các điểm tích hợp hệ thống (Integration Points)
- **Groq Cloud API (External Service)**:
  - Mục đích: Thực thi các tác vụ suy luận ngôn ngữ của tác tử LangGraph.
  - Các mô hình tích hợp:
    - `llama-3.1-8b-instant`: Phân tích câu hỏi (Query Analyzer), Đánh giá độ đầy đủ (CRAG Evaluator).
    - `llama-3.3-70b-versatile`: Tạo câu trả lời (Generator), Thẩm định độ chính xác (Judge).
- **Qdrant Vector DB (Internal Service - Dockerized)**:
  - Địa chỉ cổng mặc định: `http://qdrant:6333`.
  - Mục đích: Tìm kiếm dense vector tương đồng (semantic search).
  - Metadata Payload yêu cầu: `doc_id`, `so_hieu`, `loai_van_ban`, `nam_ban_hanh`, `content`.
- **PostgreSQL (Internal Service - Dockerized)**:
  - Địa chỉ cổng mặc định: `postgresql://admin:admin123@postgres:5432/legal_db`.
  - Mục đích: Quản lý trạng thái đồng bộ tài liệu, cấu hình cơ sở dữ liệu quan hệ.
- **Redis Cache (Internal Service - Dockerized)**:
  - Địa chỉ cổng mặc định: `redis://redis:6379`.
  - Mục đích: Quản lý bộ nhớ hội thoại (`session_id`) và lịch sử tin nhắn của LangGraph.

---

## 6. Câu hỏi mở & Giả định (Open Questions & Assumptions)

### 6.1 Giả định (Assumptions)
- **[ASSUMPTION-1] Tài khoản Groq API**: Lập trình viên/Môi trường deploy đã có sẵn `GROQ_API_KEY` hợp lệ với hạn mức (rate limit) đủ lớn để chạy đồng thời mô hình `llama-3.1-8b-instant` và `llama-3.3-70b-versatile`.
- **[ASSUMPTION-2] Định dạng văn bản PDF**: Các tài liệu luật tải lên hệ thống có dạng text-searchable (không phải dạng quét ảnh/scanned PDF thuần túy không có lớp text).
- **[ASSUMPTION-3] Deploy nội bộ**: Phiên bản hiện tại phục vụ thử nghiệm nội bộ, do đó chưa tích hợp các cơ chế xác thực người dùng (Auth/SSO) ở cả Frontend lẫn Backend.

### 6.2 Câu hỏi mở (Open Questions)
- **[OPEN-1] Phân quyền Upload**: Có cần giới hạn quyền tải lên tài liệu pháp luật (Endpoint `/upload`) chỉ dành cho một nhóm IP/Token cụ thể hay không, hay bất kỳ ai mở trang Streamlit đều có thể upload? (Hiện tại chưa cần Auth, cứ cho upload tự do).
- **[OPEN-2] Hạ tầng CI/CD**: Khi chạy GitHub Actions để test và build Docker, chúng ta có cần cấu hình đẩy (push) image lên một Container Registry cụ thể (như Docker Hub, Github Packages - GHCR) hay chỉ cần kiểm tra xem build thành công cục bộ trên Runner? (CI/CD chỉ cần chạy test và build thành công trên Runner, chưa cần push Image).






