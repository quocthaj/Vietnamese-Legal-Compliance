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
    CREATE TABLE IF NOT EXISTS legal_chunks (
        id SERIAL PRIMARY KEY,
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