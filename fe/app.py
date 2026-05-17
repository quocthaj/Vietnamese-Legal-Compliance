"""
app.py — Vietnamese Legal Compliance AI — Streamlit Frontend
Kết nối với FastAPI backend tại http://localhost:8000
"""
import time
import uuid
import streamlit as st
import requests

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VietLegal AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


API_BASE = "http://localhost:8000"

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Root vars ── */
:root {
    --bg-primary:    #0f1117;
    --bg-secondary:  #1a1d27;
    --bg-card:       #1e2130;
    --accent:        #4f8ef7;
    --accent-soft:   #2a3a5c;
    --accent-green:  #22c55e;
    --accent-amber:  #f59e0b;
    --accent-red:    #ef4444;
    --text-primary:  #e8eaf0;
    --text-muted:    #8892a4;
    --border:        #2a2d3e;
    --radius:        12px;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
/* Giữ header để nút ☰ sidebar toggle hoạt động */
[data-testid="stToolbar"]          { display: none !important; }
[data-testid="stDecoration"]       { display: none !important; }
[data-testid="stStatusWidget"]     { display: none !important; }
/* Luôn hiện nút toggle sidebar */
[data-testid="stSidebarCollapsedControl"] { display: flex !important; visibility: visible !important; }

.block-container { padding: 1.5rem 2rem !important; max-width: 100% !important; }

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg-primary);
    color: var(--text-primary);
}


/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container { padding: 1rem !important; }

/* ── Page header ── */
.page-header {
    background: linear-gradient(135deg, #1a2744 0%, #1e2130 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
}
.page-header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; color: var(--text-primary); }
.page-header p  { margin: .3rem 0 0; color: var(--text-muted); font-size: .9rem; }

/* ── Nav buttons (sidebar only) ── */
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    text-align: left !important;
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    padding: .6rem 1rem !important;
    font-size: .95rem !important;
    font-weight: 500 !important;
    transition: all .2s ease !important;
    margin-bottom: 4px !important;
    box-shadow: none !important;
    display: flex !important;
    align-items: center !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #2a3a5c !important;
    border-color: #4f8ef7 !important;
    color: #ffffff !important;
}

/* ── Chat messages ── */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: .75rem;
    padding: .5rem 0;
}
.msg-user {
    display: flex;
    justify-content: flex-end;
}
.msg-user .bubble {
    background: #ffffff;
    color: #1a1d27;
    border-radius: 18px 18px 4px 18px;
    padding: .75rem 1.1rem;
    max-width: 72%;
    font-size: .93rem;
    line-height: 1.55;
    box-shadow: 0 2px 8px rgba(0,0,0,.15);
}
.msg-ai {
    display: flex;
    justify-content: flex-start;
    gap: .6rem;
    align-items: flex-start;
}
.msg-ai .avatar {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, #4f8ef7, #7c3aed);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: .85rem;
    flex-shrink: 0;
    margin-top: 4px;
}
.msg-ai .bubble {
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--text-primary);
    border-radius: 4px 18px 18px 18px;
    padding: .75rem 1.1rem;
    max-width: 78%;
    font-size: .93rem;
    line-height: 1.6;
}

/* ── Typing indicator ── */
.typing-indicator {
    display: flex; gap: 5px; align-items: center; padding: .5rem 1rem;
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 4px 18px 18px 18px; width: fit-content;
}
.typing-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--accent); opacity: .4;
    animation: bounce .8s infinite;
}
.typing-dot:nth-child(2) { animation-delay: .15s; }
.typing-dot:nth-child(3) { animation-delay: .3s;  }
@keyframes bounce {
    0%, 80%, 100% { transform: translateY(0); opacity: .4; }
    40%            { transform: translateY(-6px); opacity: 1; }
}

/* ── Stats chips ── */
.stat-chips { display: flex; gap: .5rem; flex-wrap: wrap; margin-top: .4rem; }
.chip {
    font-size: .75rem; padding: .15rem .55rem; border-radius: 20px;
    font-weight: 500; letter-spacing: .02em;
}
.chip-blue  { background: rgba(79,142,247,.15); color: #4f8ef7; border: 1px solid rgba(79,142,247,.3); }
.chip-green { background: rgba(34,197,94,.15);  color: #22c55e; border: 1px solid rgba(34,197,94,.3); }
.chip-amber { background: rgba(245,158,11,.15); color: #f59e0b; border: 1px solid rgba(245,158,11,.3); }

/* ── Upload zone ── */
[data-testid="stFileUploader"] {
    background: var(--bg-card) !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem !important;
    transition: border-color .2s;
}
[data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }

/* ── Table ── */
[data-testid="stDataFrame"] { border-radius: var(--radius); overflow: hidden; }

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
}
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: .8rem !important; }
[data-testid="stMetricValue"] { color: var(--text-primary) !important; font-size: 1.6rem !important; font-weight: 700 !important; }

/* ── Status badge ── */
.status-ready      { color: #22c55e; font-weight: 600; }
.status-processing { color: #f59e0b; font-weight: 600; }
.status-failed     { color: #ef4444; font-weight: 600; }

/* ── Input ── */
[data-testid="stChatInput"] textarea,
.stTextInput input {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
}
[data-testid="stChatInputSubmitButton"] { color: var(--accent) !important; }

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: var(--radius); }

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1rem 0 !important; }

/* ── Info cards ── */
.info-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
    margin-bottom: .75rem;
}
.info-card h4 { margin: 0 0 .3rem; font-size: .95rem; color: var(--text-primary); }
.info-card p  { margin: 0; font-size: .83rem; color: var(--text-muted); }

.section-label {
    font-size: .7rem;
    font-weight: 600;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--text-muted);
    padding: .5rem .3rem .3rem;
}
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
if "page"        not in st.session_state: st.session_state.page = "chat"
if "session_id"  not in st.session_state: st.session_state.session_id = str(uuid.uuid4())
if "messages"    not in st.session_state: st.session_state.messages = []  # {"role","content","meta"}


# ── Helpers ───────────────────────────────────────────────────────────────────
def post_chat(query: str) -> dict:
    payload = {"query": query, "session_id": st.session_state.session_id}
    try:
        r = requests.post(f"{API_BASE}/chat", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Không thể kết nối đến API. Hãy đảm bảo server đang chạy tại localhost:8000."}
    except Exception as e:
        return {"error": str(e)}


def get_documents() -> list:
    try:
        r = requests.get(f"{API_BASE}/documents", timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return []
    except Exception:
        return []


def upload_pdf(file) -> dict:
    try:
        r = requests.post(
            f"{API_BASE}/upload",
            files={"file": (file.name, file.getvalue(), "application/pdf")},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Không kết nối được API."}
    except Exception as e:
        return {"error": str(e)}


def render_message(msg: dict):
    role    = msg["role"]
    content = msg["content"]

    if role == "user":
        st.markdown(f"""
        <div class="msg-user">
            <div class="bubble">{content}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="msg-ai">
            <div class="avatar">⚖️</div>
            <div class="bubble">{content}</div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo & title
    st.markdown("""
    <div style="padding: .5rem 0 1rem; text-align: center;">
        <div style="font-size:2.2rem">⚖️</div>
        <div style="font-size:1.05rem; font-weight:700; color:#e8eaf0; margin-top:.3rem">VietLegal AI</div>
        <div style="font-size:.75rem; color:#8892a4;">Vietnamese Legal Compliance</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Navigation</div>', unsafe_allow_html=True)

    if st.button("Chat", use_container_width=True):
        st.session_state.page = "chat"
        st.rerun()
    if st.button("Upload", use_container_width=True):
        st.session_state.page = "upload"
        st.rerun()
    if st.button("Documents", use_container_width=True):
        st.session_state.page = "documents"
        st.rerun()


    if st.button("New Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages   = []
        st.rerun()

    st.markdown("---")
    st.markdown('<div style="font-size:.72rem; color:#4a5568; text-align:center; padding:.5rem 0;">Powered by LangGraph + Qdrant + BM25</div>', unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CHAT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "chat":
    st.markdown("""
    <div class="page-header">
        <h1>💬 Tư vấn Pháp luật AI</h1>
        <p>Đặt câu hỏi về pháp luật Việt Nam trong lĩnh vực IT — hệ thống sẽ tra cứu và trả lời dựa trên văn bản pháp quy.</p>
    </div>
    """, unsafe_allow_html=True)

    # Render existing messages
    for msg in st.session_state.messages:
        render_message(msg)

    # Empty state
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center; padding: 3rem 0; color: #4a5568;">
            <div style="font-size:3.5rem">⚖️</div>
            <div style="font-size:1.1rem; font-weight:600; color:#8892a4; margin-top:1rem">Bắt đầu đặt câu hỏi pháp lý</div>
        </div>
        """, unsafe_allow_html=True)

    # Chat input
    user_input = st.chat_input("Hỏi về pháp luật Việt Nam…")

    if user_input and user_input.strip():
        # Append user message immediately
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        render_message({"role": "user", "content": user_input.strip()})

        # Typing indicator + call API
        with st.spinner(""):
            typing_placeholder = st.empty()
            typing_placeholder.markdown("""
            <div class="msg-ai">
                <div class="avatar">⚖️</div>
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            result = post_chat(user_input.strip())
            typing_placeholder.empty()

        if "error" in result:
            st.error(f"❌ {result['error']}")
        else:
            answer = result.get("answer", "Không có câu trả lời.")
            meta   = {
                "intent":          result.get("intent", ""),
                "pass_judge":      result.get("pass_judge", False),
                "retriever_count": result.get("retriever_count", 0),
                "generator_count": result.get("generator_count", 0),
            }
            ai_msg = {"role": "assistant", "content": answer, "meta": meta}
            st.session_state.messages.append(ai_msg)
            render_message(ai_msg)

        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "upload":
    st.markdown("""
    <div class="page-header">
        <h1>📤 Upload Văn bản Pháp luật</h1>
        <p>Tải lên file PDF — hệ thống tự động parse, embed và index vào knowledge base.</p>
    </div>
    """, unsafe_allow_html=True)


    uploaded_file = st.file_uploader(
        "Kéo thả hoặc click để chọn file PDF",
        type=["pdf"],
        help="Chỉ hỗ trợ file PDF. Tên file nên là số hiệu văn bản.",
    )

    if uploaded_file:
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.markdown(f"""
            <div class="info-card">
                <h4>📄 {uploaded_file.name}</h4>
                <p>Kích thước: {uploaded_file.size / 1024:.1f} KB</p>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            if st.button("🚀 Bắt đầu xử lý", type="primary", use_container_width=True):
                with st.spinner("Đang upload và khởi động pipeline…"):
                    result = upload_pdf(uploaded_file)

                if "error" in result:
                    st.error(f"❌ {result['error']}")
                else:
                    st.success(f"✅ {result.get('message', 'Upload thành công!')}")
                    st.info("⏳ Pipeline đang chạy trong background. Kiểm tra tab **Documents** sau ít phút.")

    st.markdown("---")
    st.markdown("""
    <div class="info-card">
        <h4>📌 Hướng dẫn đặt tên file</h4>
        <p>Nên đặt tên file theo số hiệu văn bản để hệ thống metadata extraction chính xác hơn.<br>
        VD: <code style="color:#4f8ef7">13_2022_ND_CP.pdf</code>, <code style="color:#4f8ef7">luat_giao_thong_2008.pdf</code></p>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "documents":
    st.markdown("""
    <div class="page-header">
        <h1>📚 Kho Văn bản Pháp luật</h1>
        <p>Toàn bộ tài liệu đã được ingested vào knowledge base.</p>
    </div>
    """, unsafe_allow_html=True)

    col_refresh, _ = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Làm mới", use_container_width=True):
            st.rerun()

    with st.spinner("Đang tải danh sách tài liệu…"):
        docs = get_documents()

    if not docs:
        st.warning("⚠️ Không thể tải danh sách tài liệu. Đảm bảo API server đang chạy.")
    else:
        # Summary metrics
        total   = len(docs)
        ready   = sum(1 for d in docs if d.get("processing_status") == "ready")
        proc    = sum(1 for d in docs if d.get("processing_status") == "processing")
        failed  = total - ready - proc

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tổng tài liệu",  total)
        m2.metric("✅ Sẵn sàng",       ready)
        m3.metric("Đang xử lý",     proc)
        m4.metric("❌ Lỗi",            failed)

        st.markdown("---")

        # Document list
        for doc in docs:
            status = doc.get("processing_status", "unknown")
            status_cls  = {"ready": "status-ready", "processing": "status-processing", "failed": "status-failed"}.get(status, "")
            status_icon = {"ready": "✅", "processing": "⏳", "failed": "❌"}.get(status, "❓")
            date_str = doc.get("ngay_ban_hanh", "")[:10] if doc.get("ngay_ban_hanh") else "—"

            st.markdown(f"""
            <div class="info-card" style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h4>📄 {doc.get('ten_van_ban', 'Không rõ')}</h4>
                    <p>Số hiệu: <b style="color:#4f8ef7">{doc.get('so_hieu', '—')}</b> &nbsp;|&nbsp; Ngày ban hành: {date_str}</p>
                </div>
                <div class="{status_cls}" style="font-size:.9rem">{status_icon} {status.capitalize()}</div>
            </div>
            """, unsafe_allow_html=True)