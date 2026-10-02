# src/rag/feedback/triage.py
"""Badcase 归因引擎：纯规则，无需 AI"""
from rag.feedback.models import RootCause
from rag.logging_config import get_logger

logger = get_logger(__name__)


def triage(record: dict) -> RootCause:
    """根据反馈记录归因

    规则：
      - 检索为空 → 知识缺失
      - 检索分 < 0.5 → 知识覆盖不足
      - 检索分 0.5~0.7 → 检索策略问题
      - 检索分 >= 0.7 但用户不满意 → Prompt / 模型问题
    """
    scores = record.get("rerank_scores") or []
    snippets = record.get("retrieved_snippets") or []

    # 无检索结果
    if not snippets:
        return RootCause.KNOWLEDGE

    top = scores[0] if scores else 0.0

    if top <  0.5 - 1e-6:
        return RootCause.KNOWLEDGE
    if top <  0.7 - 1e-6:
        return RootCause.RETRIEVAL
    return RootCause.PROMPT


def triage_all(records: list) -> list:
    """批量归因，返回带 root_cause 的记录"""
    out = []
    for r in records:
        r["root_cause"] = triage(r).value
        out.append(r)
    return out