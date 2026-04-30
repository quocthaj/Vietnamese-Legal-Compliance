import pdfplumber
import re
import psycopg2
import os

CONTENT_PREVIEW = 100  # Giới hạn ký tự nội dung hiển thị khi print
TEN_FILE = "Luatanninhmang.pdf"

# ── Kết nối PostgreSQL ──────────────────────────────────────────────────
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="legal_db",
    user="admin",
    password="admin123"
)
cursor = conn.cursor()
print("✅ Kết nối PostgreSQL thành công!")

# ── Đọc PDF ────────────────────────────────────────────────────────────
with pdfplumber.open(f"../data/{TEN_FILE}") as pdf:
    full_text = ""
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            full_text += text.replace('\r', '') + "\n"

    # ── 1. METADATA ────────────────────────────────────────────────────

    # Số hiệu luật — VD: 116/2025/QH15
    match_luat = re.search(r'Luật số[:\s]+(\d+/\d{4}/QH\d+)', full_text)
    so_hieu_luat = match_luat.group(1) if match_luat else None

    # Loại văn bản — dòng riêng chứa chữ in hoa
    match_loai = re.search(
        r'(?m)^(LUẬT|NGHỊ ĐỊNH|THÔNG TƯ|QUYẾT ĐỊNH|NGHỊ QUYẾT|PHÁP LỆNH)\s*$',
        full_text
    )
    loai_van_ban = match_loai.group(1).strip() if match_loai else None

    # Ngày ban hành — "thông qua ngày DD tháng MM năm YYYY"
    match_ngay = re.search(
        r'thông qua ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})',
        full_text, re.IGNORECASE
    )
    if match_ngay:
        d, m, y = match_ngay.group(1), match_ngay.group(2), match_ngay.group(3)
        ngay_ban_hanh = f"{d.zfill(2)}/{m.zfill(2)}/{y}"
    else:
        ngay_ban_hanh = None

    print("=" * 60)
    print(f"  Loại văn bản : {loai_van_ban}")
    print(f"  Số hiệu      : {so_hieu_luat}")
    print(f"  Ngày ban hành: {ngay_ban_hanh}")
    print("=" * 60)

    # ── 2. PARSE & INSERT TỪNG ĐIỀU ────────────────────────────────────
    chunks = re.split(r'\n\s*["\']?\s*(Điều\s+\d+\.)', '\n' + full_text)

    insert_count = 0
    for i in range(1, len(chunks) - 1, 2):
        article = chunks[i] + chunks[i + 1]
        lines = article.strip().split('\n')
        if not lines:
            continue

        first_line = lines[0]
        match_dieu = re.match(r'Điều\s+(\d+)\.\s*(.*)', first_line)
        if not match_dieu:
            continue

        so_dieu = int(match_dieu.group(1))
        ten_dieu_lines = []

        title_inline = match_dieu.group(2).strip()
        if title_inline:
            ten_dieu_lines.append(title_inline)

        body_start_idx = 1
        for idx, line in enumerate(lines[1:], start=1):
            line_stripped = line.strip()
            if not line_stripped:
                if ten_dieu_lines:
                    body_start_idx = idx + 1
                    break
                continue
            if not ten_dieu_lines:
                ten_dieu_lines.append(line_stripped)
                continue
            if re.match(r'^(\d+\.|[a-z]\)|[-+])', line_stripped) or line_stripped[0].isupper():
                body_start_idx = idx
                break
            ten_dieu_lines.append(line_stripped)
        else:
            body_start_idx = len(lines)

        ten_dieu = " ".join(ten_dieu_lines)
        if not ten_dieu:
            continue

        noi_dung = "\n".join(lines[body_start_idx:]).strip()
        content_preview = noi_dung[:CONTENT_PREVIEW] + ("..." if len(noi_dung) > CONTENT_PREVIEW else "")

        # ── INSERT vào PostgreSQL ──────────────────────────────────────
        cursor.execute(
            """
            INSERT INTO legal_chunks
                (loai_van_ban, so_hieu, ngay_ban_hanh, ten_file, so_dieu, ten_dieu, noi_dung)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (loai_van_ban, so_hieu_luat, ngay_ban_hanh, TEN_FILE, so_dieu, ten_dieu, noi_dung)
        )
        insert_count += 1

        print(f"  [Điều {so_dieu:>3}] {ten_dieu[:50]}")
        print(f"           {content_preview}")
        print("-" * 60)

    conn.commit()
    print(f"\n✅ Đã INSERT {insert_count} điều vào bảng legal_chunks.")

cursor.close()
conn.close()
print("🔒 Đã đóng kết nối PostgreSQL.")