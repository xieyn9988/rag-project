# src/rag/feedback/metrics.py
"""评估指标计算"""
from typing import Dict, List


def compute_metrics(records: List[dict]) -> Dict:
    """从反馈记录聚合业务指标"""
    total = len(records)
    if total == 0:
        return {"total": 0}

    satisfied = sum(1 for r in records if r["feedback_type"] == "satisfied")
    unsatisfied = sum(1 for r in records if r["feedback_type"] == "unsatisfied")
    low_conf = sum(1 for r in records if r["feedback_type"] == "low_conf")

    all_scores = [
        (r.get("rerank_scores") or [0])[0]
        for r in records if r.get("rerank_scores")
    ]
    avg_top_score = sum(all_scores) / len(all_scores) if all_scores else 0.0

    return {
        "total": total,
        "satisfied": satisfied,
        "unsatisfied": unsatisfied,
        "low_confidence": low_conf,
        "satisfied_rate": round(satisfied / total, 3),
        "avg_top_score": round(avg_top_score, 3),
    }