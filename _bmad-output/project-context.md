---
project_name: 'vietnamese-legal-compliance'
user_name: 'Thai'
date: '2026-06-17'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality_rules', 'workflow_rules', 'dont_miss_rules']
status: 'complete'
rule_count: 29
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Backend Framework**: FastAPI (Uvicorn), Python 3.10+
- **Frontend Framework**: Streamlit (Giao diện chat, upload và quản lý tài liệu)
- **Agent Framework**: LangGraph (Đồ thị tác tử tự sửa lỗi với CRAG & Self-Reflection)
- **Cơ sở dữ liệu Vector**: Qdrant (Chạy trên Docker)
- **Cơ sở dữ liệu quan hệ**: PostgreSQL 15 (Chạy trên Docker)
- **Bộ nhớ đệm & Lịch sử**: Redis 7 (Chạy trên Docker)
- **Mẫu dịch vụ AI**: Groq API với các mô hình:
  - `llama-3.1-8b-instant` cho phân tích câu hỏi (Query Analyzer) và đánh giá độ đầy đủ tài liệu (CRAG Evaluation).
  - `llama-3.3-70b-versatile` cho sinh câu trả lời (Generator) và đánh giá độ chính xác (Judge).
- **Thư viện NLP & Tìm kiếm**:
  - `underthesea` (Tokenize/tách từ tiếng Việt)
  - `rank_bm25` (Thuật toán tìm kiếm sparse lexical search)
  - `pdfplumber` (Trích xuất text từ tệp PDF)
  - `sentence-transformers` (Tạo vector embeddings cục bộ)

## Critical Implementation Rules

### Language-Specific Rules (Python)

- **Type Annotations**: Luôn khai báo Type Hints rõ ràng cho các hàm và trạng thái (ví dụ: sử dụng `TypedDict` cho `AgentState`, khai báo kiểu trả về cho các Node hàm).
- **Đường dẫn import (Path Resolution)**: Do cấu trúc dự án chạy từ nhiều thư mục con, luôn cấu hình `sys.path.append` ở đầu các script entry point để đảm bảo import các module nội bộ từ thư mục gốc (`root`) hoạt động chuẩn xác:
  ```python
  import os, sys
  sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
  ```
- **Xử lý tiếng Việt (Unicode)**: Khi in log hoặc chuyển đổi JSON chứa văn bản tiếng Việt, luôn thiết lập tham số `ensure_ascii=False` (ví dụ: `json.dumps(data, ensure_ascii=False)`).
- **Quản lý biến môi trường**: Luôn sử dụng `dotenv.load_dotenv()` trước khi truy cập biến cấu hình qua `os.environ.get()` hoặc `os.getenv()`.
- **Xử lý lỗi**: Các node của LangGraph và API endpoint phải bọc trong các khối `try-except` rõ ràng, có ghi log chi tiết lỗi và có giá trị fallback an toàn thay vì để crash chương trình.

### Framework-Specific Rules

#### 1. FastAPI
- **Quản lý vòng đời (Lifespan)**: Sử dụng `@asynccontextmanager` để khởi tạo `ThreadedConnectionPool` cho PostgreSQL, kết nối Qdrant/Redis, tải trước mô hình embedding và chạy thử warmup. Thiết lập kết nối phải có cơ chế retry tự động để phòng trường hợp DB khởi động chậm hơn API.
- **Background Tasks**: Các tác vụ nặng như phân tích cú pháp PDF, tạo embedding và rebuild chỉ mục BM25 phải chạy ngầm qua `BackgroundTasks`. Đồng thời cập nhật trạng thái tiến trình (`pending` -> `processing` -> `ready`/`failed`) trong bảng `legal_documents` để Frontend hiển thị trạng thái thực tế.
- **Pydantic Validation**: Định nghĩa rõ ràng các Schema (`BaseModel`) cho API request và response để tự động kiểm tra định dạng dữ liệu truyền tải.

#### 2. LangGraph
- **Hợp nhất State**: Định nghĩa rõ kiểu dữ liệu của `AgentState`, đặc biệt là các biến dùng `Annotated` tích lũy (ví dụ: `chat_history: Annotated[list, operator.add]`, `retriever_count: Annotated[int, operator.add]`). Dữ liệu trả về từ các Node phải khớp kiểu dữ liệu khai báo để tránh lỗi Runtime.
- **Logic vòng lặp & Điểm dừng**: Thiết lập kiểm tra bộ đếm số lượt chạy trong các hàm cạnh (conditional edges) để thoát đồ thị an toàn (tối đa 3 lượt cho Retriever/Generator) nhằm tránh lặp vô tận khi tài liệu không đủ thông tin hoặc câu trả lời bị lỗi phán quyết (Judge).

#### 3. Streamlit
- **Tách tầng Frontend & Backend**: Giữ cấu trúc độc lập thông qua HTTP API RESTful. Không import trực tiếp các module nghiệp vụ của Backend hoặc thực thi query DB trực tiếp từ code giao diện Streamlit.
- **Cấu trúc mã nguồn**: Tránh gộp tất cả logic vào duy nhất một file `app.py`. Tách riêng Client API (`api_client.py`) và các Component UI dùng chung để dễ bảo trì khi cần chỉnh sửa giao diện gấp.
- **Đồng bộ hóa Trạng thái & Bảo mật**: Quản lý hội thoại qua `st.session_state` (`messages` và `session_id`). Không dùng `st.markdown(..., unsafe_allow_html=True)` cho bất kỳ dữ liệu động nào do người dùng nhập vào để phòng tránh lỗ hổng XSS. Giao diện tùy chỉnh CSS phải được đặt tĩnh trong các khối cấu trúc layout.

### Testing Rules

- **Framework kiểm thử**: Sử dụng `pytest` cho kiểm thử đơn vị (Unit Tests) và kiểm thử tích hợp (Integration Tests). Toàn bộ file kiểm thử đặt tại thư mục `{project-root}/tests/` và đặt tên theo định dạng `test_*.py`.
- **Kiểm thử FastAPI Endpoints**: Sử dụng `fastapi.testclient.TestClient` để mô phỏng và kiểm tra mã trạng thái trả về (Status Code) và cấu trúc dữ liệu JSON của các endpoint `/chat`, `/upload`, và `/documents`.
- **Kiểm thử các Node của LangGraph**: 
  - Thực hiện unit test độc lập cho từng hàm Node (ví dụ: `query_analyzer`, `judge`) bằng cách truyền vào các `state` giả lập.
  - Sử dụng thư viện `unittest.mock` để mock các API call của Groq client nhằm tránh phát sinh chi phí và đảm bảo test chạy ổn định không phụ thuộc vào mạng.
- **Giả lập Database & Search**: 
  - Mock connection pool `psycopg2` và client `QdrantClient` khi chạy unit test để không làm ghi đè hay thay đổi dữ liệu thật trong DB.
  - Khi chạy tích hợp, cấu hình riêng một cơ sở dữ liệu test (Database/Qdrant collection riêng) biệt lập với môi trường phát triển chính.

### Code Quality & Style Rules

- **Chuẩn phong cách**: Tuân thủ chuẩn PEP 8 đối với mã nguồn Python (sử dụng 4 khoảng trắng thụt lề, giới hạn độ dài dòng dưới 79-88 ký tự).
- **Quy tắc đặt tên (Naming Conventions)**:
  - Tên tệp & thư mục: sử dụng `snake_case` (ví dụ: `hybrid_search.py`, `pdf_parser.py`).
  - Tên lớp (Classes): sử dụng `PascalCase` (ví dụ: `AgentState`, `ChatRequest`).
  - Tên hàm & biến: sử dụng `snake_case` (ví dụ: `query_analyzer`, `db_pool`).
- **Tài liệu hóa (Docstrings & Comments)**:
  - Tất cả các Node hàm trong LangGraph và Endpoint API bắt buộc phải có Docstring tiếng Việt nêu rõ mục đích, tham số đầu vào và kiểu dữ liệu trả về.
  - Sử dụng ghi chú (Comments) để giải thích các thuật toán đặc thù như cách tính RRF (Reciprocal Rank Fusion) hoặc token hóa tiếng Việt.
- **Ghi nhật ký (Logging/Tracing)**:
  - In log rõ ràng ở đầu mỗi Node (ví dụ: `print("Node: query_analyzer")`) kèm theo thông tin chi tiết đầu ra (output) dạng JSON để dễ dàng theo dõi dấu vết xử lý của Agent trực tiếp trên terminal.

### Development Workflow Rules

- **Quy ước đặt tên nhánh (Branch Naming)**:
  - Tính năng mới (New Features): `feature/short-description` hoặc theo định dạng Epic/Story: `epic-[id]/story-[id]-[desc]` (ví dụ: `epic-3/story-3.1-flashcard`).
  - Sửa lỗi (Bug fixes): `fix/short-description`.
- **Định dạng thông điệp Commit (Commit Messages)**:
  - Áp dụng chuẩn Conventional Commits (ví dụ: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`).
  - Viết commit message ngắn gọn, rõ nghĩa bằng tiếng Anh hoặc tiếng Việt nhất quán.
- **Quy trình gửi Pull Request (PR)**:
  - Trước khi tạo PR, chạy kiểm tra cục bộ để đảm bảo mã không có lỗi cú pháp.
  - Cập nhật tệp `.env.example` nếu bổ sung bất kỳ biến môi trường mới nào vào hệ thống.
  - Xác nhận rằng các dịch vụ trong `docker-compose.yml` có cấu hình cổng (ports) chính xác và không bị xung đột với các tiến trình chạy cục bộ của lập trình viên.
- **Tài liệu hóa lịch sử Story (Bắt buộc)**:
  - Sau khi hoàn thành xong 1 story, Agent bắt buộc phải tạo một thư mục tên là `report/` ở thư mục gốc (nếu chưa có) và ghi nhận nhật ký phát triển vào tệp `report/SKILL.md`.
  - Tệp này phải ghi rõ: mã story, các file đã thay đổi, chức năng chính đã bàn giao và trạng thái kiểm thử, giúp Agent làm việc ở phiên tiếp theo nhanh chóng đọc lại và hiểu đầy đủ ngữ cảnh dự án.

### Critical Don't-Miss Rules

#### 1. Chống lặp vô hạn (Infinite Loops)
- **Quy tắc**: Trong đồ thị LangGraph, không bao giờ được phép cho các Node `Retriever` hoặc `Generator` chạy vô hạn. Bắt buộc phải có điều kiện kiểm tra biến đếm `retriever_count` và `generator_count` trong hàm chuyển hướng cạnh. Nếu đạt tới giới hạn (tối đa 3 lần thử), Agent phải định tuyến luồng sang node trả về kết quả lỗi lịch sự (ví dụ: *"Hệ thống không tìm thấy thông tin pháp luật chính xác cho yêu cầu này, vui lòng cung cấp thêm thông tin"*).

#### 2. Định dạng Trích dẫn Pháp luật (Citations)
- **Quy tắc**: Generator Node chỉ được trích dẫn thông tin tồn tại trong ngữ cảnh được retriever trả về. Nghiêm cấm hoàn toàn việc tự suy luận (hallucination) tên luật hoặc số hiệu điều khoản. Định dạng trích dẫn bắt buộc phải chuẩn hóa theo cấu trúc tiếng Việt: `[Tên Luật/Nghị Định/Thông Tư - Điều X - Khoản Y]`.

#### 3. Bảo mật Prompt & Query Analyzer
- **Quy tắc**: Query Analyzer Node phải được cấu hình prompt nghiêm ngặt để chỉ phân tích câu hỏi pháp lý tiếng Việt và trả về định dạng JSON thuần túy. Nó tuyệt đối không được phép trả lời giải thích, không tiết lộ prompt hệ thống hoặc bị tấn công Prompt Injection để chuyển hướng trả lời các chủ đề ngoài phạm vi pháp luật.

#### 4. Ghi đè chỉ mục BM25 (File Locking)
- **Quy tắc**: Tệp chỉ mục BM25 `bm25_indexer.pkl` được load và ghi đè mỗi khi có tài liệu PDF mới được upload. Để tránh xung đột dữ liệu (race conditions) khi nhiều tệp được xử lý ngầm đồng thời, mã nguồn Ingestion phải có cơ chế khóa tệp (file locking) hoặc xử lý tuần tự (queueing).

---

## Usage Guidelines

**For AI Agents:**

- Đọc kỹ tệp này trước khi tiến hành viết hoặc sửa đổi mã nguồn.
- Tuân thủ chính xác tất cả quy tắc đã được tài liệu hóa.
- Trong trường hợp không chắc chắn, hãy lựa chọn phương án an toàn và nghiêm ngặt hơn.
- Cập nhật tệp này nếu xuất hiện các mẫu thiết kế (patterns) mới được thống nhất.

**For Humans:**

- Giữ tệp này ngắn gọn và tập trung hoàn toàn vào nhu cầu phát triển của AI Agent.
- Cập nhật khi có sự thay đổi về công nghệ hoặc phiên bản của hệ thống.
- Định kỳ rà soát mỗi quý một lần để loại bỏ các quy tắc đã trở nên hiển nhiên hoặc lỗi thời.

Last Updated: 2026-06-17

