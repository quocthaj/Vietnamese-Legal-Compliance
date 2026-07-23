# Story 1.1: Cấu hình Docker Compose cho các dịch vụ phụ trợ

## 1. Vấn đề hoặc Cơ hội (Problem or Opportunity)
Hệ thống bao gồm nhiều dịch vụ độc lập như FastAPI, Streamlit, PostgreSQL, Qdrant, Redis, và n8n. Quản trị viên cần một phương pháp tiêu chuẩn để khởi chạy toàn bộ môi trường nội bộ cùng nhau, bảo mật kết nối và duy trì trạng thái dữ liệu (persistence) trên máy chủ. Docker Compose là giải pháp tối ưu cho nhu cầu này.

## 2. Câu chuyện Người dùng (User Story)
**As a** Quản trị viên hệ thống,
**I want** cập nhật `docker-compose.yml` để cấu hình Postgres, Qdrant, Redis, n8n cùng mạng nội bộ và thiết lập volumes,
**So that** tôi có thể khởi chạy và lưu trữ dữ liệu bền vững cho toàn bộ các database bằng một lệnh duy nhất.

## 3. Tiêu chí Chấp nhận (Acceptance Criteria)
* **Given** môi trường Docker trên máy chủ
* **When** chạy lệnh `docker-compose up`
* **Then** các container PostgreSQL, Qdrant, Redis và n8n phải được khởi tạo thành công và giao tiếp nội bộ qua chung một network
* **And** các persistent volumes (kể cả volume chia sẻ `/pdf_storage`) phải được mount chính xác và cấu hình an toàn từ tệp `.env`.

## 4. Bối cảnh Kỹ thuật & Ràng buộc (Technical Context & Constraints)
### Kiến trúc Tuân thủ
- **Database**: PostgreSQL 15, Qdrant (bản chuẩn), Redis 7-alpine.
- **n8n**: Docker image chính thức (`docker.n8n.io/n8nio/n8n`).
- **Storage Volumes**:
  - `postgres_data` -> `/var/lib/postgresql/data`
  - `qdrant_data` -> `/qdrant/storage`
  - `redis_data` -> `/data`
  - `pdf_storage` -> `/app/shared_pdfs` (API) & `/data/pdfs` (n8n)
- **Networking**: Tạo một bridge network (ví dụ: `vlc_network`) để giới hạn các port.
- **Biến môi trường**: Đọc từ file `.env`. Không hardcode password/key trong `docker-compose.yml`.

### Yêu cầu đặc thù về Cấu trúc Tệp
Tệp `docker-compose.yml` nên được đặt ở gốc dự án. Cần tạo file `.env.example` chứa các biến mẫu (như POSTGRES_USER, POSTGRES_PASSWORD, QDRANT_HOST, REDIS_URL, v.v.).

## 5. Tình trạng (Status)
**Status:** ready-for-dev
