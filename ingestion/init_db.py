import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="legal_db",
    user="admin",
    password="admin123"
)

cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS legal_documents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        ten_file TEXT,
        loai_van_ban TEXT,
        so_hieu TEXT,
        ngay_ban_hanh DATE,
        trang_thai TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processing_status TEXT DEFAULT 'pending'
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS legal_chunks (
        id SERIAL PRIMARY KEY,
        document_id UUID REFERENCES legal_documents(id),
        loai_van_ban VARCHAR(50),
        so_hieu VARCHAR(50),
        ngay_ban_hanh VARCHAR(20),
        ten_file VARCHAR(200),
        so_dieu INTEGER,
        ten_dieu TEXT,
        noi_dung TEXT,
        vector_id VARCHAR(100)
    )
""")

conn.commit()
cursor.close()
conn.close()
print("Tạo bảng thành công!")