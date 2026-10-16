"""RRF（Reciprocal Rank Fusion）倒数排序融合。

把"向量召回"和"BM25 召回"的结果融合——互补误伤。
"""
from typing import List, Tuple

from langchain_core.documents import Document


def rrf_fusion(
    results_list: List[List[Tuple[Document, float]]],
    k: int = 60,
    top_k: int = 5,
) -> List[Tuple[Document, float]]:
    """RRF 融合多路召回。

    Args:
        results_list: 多路召回结果，每路是 [(Document, score), ...]
        k: RRF 平滑参数（论文默认 60）
        top_k: 返回前 top_k

    Returns:
        融合后的 [(Document, rrf_score), ...]
    """
    # doc_id → rrf_score
    doc_scores: dict = {}
    doc_map: dict = {}

    for results in results_list:
        for rank, (doc, _score) in enumerate(results, start=1):
            key = doc.page_content  # 用"内容"当 key（简单）
            doc_map[key] = doc
            doc_scores[key] = doc_scores.get(key, 0.0) + 1.0 / (k + rank)

    # 排序
    sorted_items = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [(doc_map[key], score) for key, score in sorted_items]