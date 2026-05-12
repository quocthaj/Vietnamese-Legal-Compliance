import os
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
import shutil
import subprocess
import psycopg2

# Cấu hình sys.path để import được module từ thư mục gốc
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.graph import app as graph_app
from agent.chat_history import get_history, save_history
from ingestion.hybrid_search import _get_model, _get_bm25, _get_qdrant
from ingestion.pdf_parser import parse_and_insert

from psycopg2 import pool

# Global database connection pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Quản lý vòng đời của ứng dụng: Load model và index lúc startup.
    """
    global db_pool
    print("\n" + "="*50)
    print("🚀 ĐANG KHỞI TẠO HỆ THỐNG PHÁP LUẬT...")
    try:
        # Khởi tạo Connection Pool
        db_pool = pool.ThreadedConnectionPool(1, 20, host="localhost", port=5432, database="legal_db", user="admin", password="admin123")
        print("✅ Đã khởi tạo Database Connection Pool!")

        # Pre-load các tài nguyên nặng
        model = _get_model()   # Load SentenceTransformer
        _get_bm25()            # Load BM25 Index
        _get_qdrant()          # Kết nối Qdrant
        
        # 🔥 WARMUP: Chạy thử một câu query giả để model thực sự sẵn sàng
        print("⚡ Đang thực hiện warmup (chạy thử inference)...")
        model.encode("warmup query", normalize_embeddings=True)
        
        print("✅ Tất cả tài nguyên đã sẵn sàng & Warmup hoàn tất!")
    except Exception as e:
        print(f"❌ Lỗi khi khởi tạo tài nguyên: {e}")
    print("="*50 + "\n")
    
    yield
    
    print("\n👋 Đang đóng hệ thống...")
    if db_pool:
        db_pool.closeall()
        print("🔒 Đã đóng Database Connection Pool!")

# Khởi tạo ứng dụng FastAPI với lifespan
app = FastAPI(
    title="Vietnamese Legal Compliance Agent API",
    description="API cho trợ lý ảo tư vấn pháp luật Việt Nam",
    version="1.0.0",
    lifespan=lifespan
)

# Model nhận dữ liệu từ request
class ChatRequest(BaseModel):
    query: str
    session_id: str  # client gửi hoặc server tự tạo

# Model trả về cho client
class ChatResponse(BaseModel):
    session_id: str
    answer: str
    intent: str
    retriever_count: int
    generator_count: int
    pass_judge: bool
    chat_history: list  # lịch sử hội thoại tích lũy

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint nhận câu hỏi và chạy qua toàn bộ LangGraph workflow.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Câu hỏi không được để trống.")

    session_id = request.session_id

    try:
        # ① Lấy chat history cũ từ Redis
        old_history = get_history(session_id)
        print(f"\n[API] session_id={session_id} | history_len={len(old_history)}")

        # ② Khởi tạo state ban đầu — inject history vào
        initial_state = {
            "query": request.query,
            "retriever_count": 0,
            "generator_count": 0,
            "is_ambiguous": False,
            "is_sufficient": False,
            "pass_judge": False,
            "context": "",
            "answer": "",
            "keywords": [],
            "so_dieu": None,
            "ten_van_ban": None,
            "intent": "",
            "chat_history": old_history  # inject history cũ để agent có context
        }

        # ③ Kích hoạt đồ thị (workflow)
        print(f"[API] Đang xử lý câu hỏi: {request.query}")
        result = graph_app.invoke(initial_state)
        print("[API] Đã xử lý xong.")

        # ④ Lưu history mới vào Redis (sliding window 10 turns)
        new_history = result.get("chat_history", old_history)
        save_history(session_id, new_history)
        print(f"[API] Đã lưu history: {len(new_history)} messages")

        # Trả response kèm session_id
        return ChatResponse(
            session_id=session_id,
            answer=result.get("answer", "Xin lỗi, đã xảy ra lỗi không xác định."),
            intent=result.get("intent", ""),
            retriever_count=result.get("retriever_count", 0),
            generator_count=result.get("generator_count", 0),
            pass_judge=result.get("pass_judge", False),
            chat_history=new_history
        )
        
    except Exception as e:
        print(f"[API Error]: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server: {str(e)}")

def process_pdf_pipeline(filename: str):
    """
    Background task: parse PDF, extract chunks and insert to DB.
    """
    try:
        print(f"[Pipeline] Bắt đầu xử lý: {filename}")
        
        # 1. Parse & Insert (trạng thái là 'processing' do pdf_parser đảm nhiệm khi tạo document)
        parse_and_insert(filename)
        
        # 2. Chạy embedder
        print(f"[Pipeline] Chạy embedder.py...")
        from ingestion.hybrid_search import _get_model
        from ingestion.embedder import run_embedding
        loaded_model = _get_model()
        run_embedding(model=loaded_model)
        
        # 3. Chạy rebuild BM25 (xoá file pkl để ép build lại)
        print(f"[Pipeline] Chạy rebuild BM25...")
        bm25_cache = os.path.join(os.path.dirname(__file__), "..", "ingestion", "bm25_indexer.pkl")
        if os.path.exists(bm25_cache):
            os.remove(bm25_cache)
        from ingestion.bm25_indexer import run_indexer
        run_indexer()
        
        from ingestion.hybrid_search import reset_bm25
        reset_bm25()
        print(f"[Pipeline] Đã reset BM25 cache in memory.")
        
        # 4. Hoàn tất -> UPDATE status='ready'
        print(f"[Pipeline] Cập nhật trạng thái thành ready...")
        conn = db_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE legal_documents SET processing_status = 'ready' WHERE ten_file = %s", (filename,))
            conn.commit()
            cursor.close()
        finally:
            db_pool.putconn(conn)

        print(f"[Pipeline] Hoàn tất toàn bộ pipeline: {filename}")
    except Exception as e:
        print(f"[Pipeline Error] Lỗi xử lý {filename}: {e}")
        try:
            # Nếu có lỗi, đánh dấu failed
            conn = db_pool.getconn()
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE legal_documents SET processing_status = 'failed' WHERE ten_file = %s", (filename,))
                conn.commit()
                cursor.close()
            finally:
                db_pool.putconn(conn)
        except Exception as db_e:
            print(f"[Pipeline Error] Không thể update status failed: {db_e}")

@app.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # 1. Validate file là PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file PDF.")

    # 2. Lưu file vào disk
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Chạy pipeline (background)
    background_tasks.add_task(process_pdf_pipeline, file.filename)

    # 4. Trả response
    return {"message": f"Đã nhận file {file.filename}, đang xử lý dưới background."}

@app.get("/documents")
async def get_documents():
    """
    Lấy danh sách các tài liệu pháp luật hiện có trong hệ thống.
    """
    try:
        conn = db_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ten_van_ban, so_hieu, ngay_ban_hanh, trang_thai, processing_status FROM legal_documents")
            rows = cursor.fetchall()
            
            documents = []
            for row in rows:
                documents.append({
                    "ten_van_ban": row[0],
                    "so_hieu": row[1],
                    "ngay_ban_hanh": row[2].isoformat() if row[2] else None,
                    "trang_thai": row[3],
                    "processing_status": row[4]
                })
                
            cursor.close()
        finally:
            db_pool.putconn(conn)
        return documents
    except Exception as e:
        print(f"[API Error /documents]: {e}")
        raise HTTPException(status_code=500, detail="Lỗi khi truy xuất danh sách tài liệu.")

# Khởi chạy server khi chạy trực tiếp file này
if __name__ == "__main__":
    import uvicorn
    # Lưu ý: chạy bằng lệnh `python api/main.py` từ thư mục gốc
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
