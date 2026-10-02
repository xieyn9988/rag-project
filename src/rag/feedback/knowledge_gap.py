# src/rag/feedback/knowledge_gap.py
"""知识缺口报告：从 Badcase 里提取需要补充的知识点"""
from collections import Counter
from typing import Dict, List

from rag.feedback.triage import triage_all
from rag.logging_config import get_logger

logger = get_logger(__name__)


ROUTE_ACTION = {
    "knowledge": "知识运营：补充/修订文档",
    "retrieval": "工程优化：调 chunk_size / top_k / Reranker",
    "prompt":    "Prompt 优化：改模板 / 换模型",
    "model":     "模型升级：换更强的 LLM",
    "unknown":   "人工介入：人工复核",
}


def generate_report(records: List[dict]) -> Dict:
    """生成知识缺口报告"""
    triaged = triage_all(records)
    badcases = [r for r in triaged
                if r["feedback_type"] in ("unsatisfied", "low_conf")]

    # 按归因分类
    by_cause = Counter(r["root_cause"] for r in badcases)

    # 提取知识缺失的具体问题
    knowledge_gaps = [
        {"question": r["question"], "top_score": (r.get("rerank_scores") or [0])[0]}
        for r in badcases if r["root_cause"] == "knowledge"
    ]

    # 建议动作
    actions = [
        f"[{cause}] {ROUTE_ACTION[cause]} —— {count} 条"
        for cause, count in by_cause.most_common()
    ]

    return {
        "total_feedbacks": len(records),
        "total_badcases": len(badcases),
        "by_root_cause": dict(by_cause),
        "knowledge_gaps": knowledge_gaps[:20],   # 最多 20 条
        "suggested_actions": actions,
    }