# src/rag/feedback/collector.py
"""反馈采集：自动判断是否需要采集"""
from typing import Optional

from rag.feedback.models import (
    CONFIDENCE_THRESHOLD, Feedback, FeedbackType,
)
from rag.feedback.store import save_feedback
from rag.logging_config import get_logger

logger = get_logger(__name__)


def collect_low_confidence(
    session_id: str,
    msg_id: str,
    question: str,
    answer: str,
    rerank_scores: list,
    retrieved_snippets: list,
) -> Optional[Feedback]:
    """自动检查是否为低置信度场景"""
    top_score = rerank_scores[0] if rerank_scores else 0.0
    if top_score >= CONFIDENCE_THRESHOLD:
        return None

    fb = Feedback(
        session_id=session_id,
        msg_id=msg_id,
        feedback_type=FeedbackType.LOW_CONFIDENCE,
        question=question,
        answer=answer,
        rerank_scores=rerank_scores,
        retrieved_snippets=retrieved_snippets,
    )
    save_feedback(fb)
    return fb


def collect_explicit(
    session_id: str,
    msg_id: str,
    question: str,
    answer: str,
    satisfied: bool,
    rerank_scores: list,
    retrieved_snippets: list,
) -> Feedback:
    """用户点击满意/不满意时调用"""
    fb = Feedback(
        session_id=session_id,
        msg_id=msg_id,
        feedback_type=(
            FeedbackType.EXPLICIT_SATISFIED if satisfied
            else FeedbackType.EXPLICIT_UNSATISFIED
        ),
        question=question,
        answer=answer,
        rerank_scores=rerank_scores,
        retrieved_snippets=retrieved_snippets,
    )
    save_feedback(fb)
    return fb