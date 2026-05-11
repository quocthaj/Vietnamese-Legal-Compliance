"""
Chat History Manager — Redis-backed conversation memory.

Mỗi session được lưu dưới dạng Redis key: chat:{session_id}
Value là JSON list các message dạng: [{"role": "user", "content": "..."}, ...]
Áp dụng sliding window giữ tối đa MAX_TURNS cặp (user + assistant) gần nhất.
"""

import json
import os
import redis
from typing import List

# ── Config ──────────────────────────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
HISTORY_TTL = int(os.getenv("HISTORY_TTL", 3600))  # 1 giờ mặc định
MAX_TURNS = 10  # Giữ tối đa 10 cặp (user + assistant) = 20 messages

# ── Redis Client (singleton, lazy init) ────────────────────────────────────
_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    """Khởi tạo Redis client (singleton)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,  # tự decode bytes → str
        )
    return _redis_client


def _make_key(session_id: str) -> str:
    """Tạo Redis key cho session."""
    return f"chat:{session_id}"


# ── Public API ──────────────────────────────────────────────────────────────

def get_history(session_id: str) -> List[dict]:
    """
    Lấy chat history từ Redis theo session_id.

    Returns:
        List[dict]: danh sách messages [{"role": "user", "content": "..."}, ...]
                    Trả [] nếu không có history hoặc session không tồn tại.
    """
    r = _get_redis()
    key = _make_key(session_id)
    data = r.get(key)

    if data is None:
        return []

    try:
        history = json.loads(data)
        return history if isinstance(history, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def save_history(session_id: str, history: List[dict]) -> None:
    """
    Lưu chat history vào Redis với sliding window.

    Chỉ giữ lại MAX_TURNS cặp (user + assistant) gần nhất = 2 * MAX_TURNS messages.
    Tự động set TTL để tránh chiếm bộ nhớ mãi mãi.

    Args:
        session_id: ID phiên hội thoại.
        history: danh sách đầy đủ messages cần lưu.
    """
    r = _get_redis()
    key = _make_key(session_id)

    # Sliding window: giữ tối đa MAX_TURNS * 2 messages gần nhất
    max_messages = MAX_TURNS * 2
    trimmed = history[-max_messages:] if len(history) > max_messages else history

    r.set(key, json.dumps(trimmed, ensure_ascii=False))
    r.expire(key, HISTORY_TTL)
