# src/rag/feedback/store.py
"""反馈存储：JSON 文件，零依赖"""
import json
from dataclasses import asdict
from pathlib import Path
from threading import Lock
from typing import List, Optional

from rag.config import settings
from rag.feedback.models import Feedback
from rag.logging_config import get_logger

logger = get_logger(__name__)

_lock = Lock()


def _store_path() -> Path:
    p = settings.project_root / "storage" / "feedback"
    p.mkdir(parents=True, exist_ok=True)
    return p / "feedbacks.jsonl"


def save_feedback(fb: Feedback) -> None:
    """追加写入 JSONL（一行一条，方便追加）"""
    with _lock:
        with open(_store_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(fb), ensure_ascii=False) + "\n")
    logger.info("反馈已保存: %s / %s", fb.feedback_type.value, fb.question[:30])


def load_all(limit: Optional[int] = None) -> List[dict]:
    """读取所有反馈（返回 dict 列表）"""
    p = _store_path()
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    records = [json.loads(line) for line in lines if line.strip()]
    return records[-limit:] if limit else records


def clear_all() -> None:
    """清空反馈（测试用）"""
    p = _store_path()
    if p.exists():
        p.unlink()