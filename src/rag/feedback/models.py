# src/rag/feedback/models.py
"""反馈数据模型"""
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class FeedbackType(str, Enum):
    EXPLICIT_SATISFIED = "satisfied"        # 用户点满意
    EXPLICIT_UNSATISFIED = "unsatisfied"    # 用户点不满意
    IMPLICIT_REPHRASE = "rephrase"          # 换说法追问
    IMPLICIT_TRANSFER = "transfer"          # 转人工
    LOW_CONFIDENCE = "low_conf"             # 系统识别低置信度


class RootCause(str, Enum):
    KNOWLEDGE = "knowledge"      # 知识库没有
    RETRIEVAL = "retrieval"      # 检索策略问题
    PROMPT = "prompt"            # Prompt / 模型问题
    MODEL = "model"              # LLM 能力不足
    UNKNOWN = "unknown"


@dataclass
class Feedback:
    session_id: str
    msg_id: str
    feedback_type: FeedbackType
    question: str
    answer: str
    rerank_scores: List[float] = field(default_factory=list)
    retrieved_snippets: List[str] = field(default_factory=list)
    latency_ms: int = 0
    llm_cost: float = 0.0
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    root_cause: Optional[RootCause] = None    # 归因后填充
    extra: Dict[str, Any] = field(default_factory=dict)


# 置信度阈值
CONFIDENCE_THRESHOLD = 0.7