# src/rag/platform/models.py
"""平台无关的统一消息模型"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Platform(str, Enum):
    JINGMAI = "jingmai"
    QIANNIU = "qianniu"
    DOUDIAN = "doudian"
    MOCK = "mock"


@dataclass
class IncomingMessage:
    platform: Platform
    shop_id: str
    buyer_id: str
    session_id: str
    msg_id: str
    content: str
    timestamp: int
    context: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OutgoingMessage:
    session_id: str
    content: str
    reply_type: str = "text"
    references: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 新增：问答追溯字段（用于反馈归因）
    msg_id: str = ""
    question: str = ""
    rerank_scores: List[float] = field(default_factory=list)


@dataclass
class ReplyResult:
    success: bool
    platform_msg_id: Optional[str] = None
    error: Optional[str] = None