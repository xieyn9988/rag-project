"""BM25 关键词检索器。

与向量检索互补——向量看语义，BM25 看字面。
用于修复"我下单后多久能收到？"的"下单"字面重叠 Badcase。
"""
from typing import List, Tuple

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from rag.logging_config import get_logger

logger = get_logger(__name__)


class BM25Retriever:
    """BM25 关键词检索。"""

    def __init__(self, docs: List[Document]):
        self._docs = docs
        # 中文按字切分（简单版；可换 jieba）
        self._corpus = [list(d.page_content) for d in docs]
        self._bm25 = BM25Okapi(self._corpus)
        logger.info("BM25Retriever 就绪: %d 篇文档", len(docs))

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Document, float]]:
        """返回 top_k 条 (Document, score)。"""
        tokenized = list(query)
        scores = self._bm25.get_scores(tokenized)
        top_idx = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]
        return [(self._docs[i], float(scores[i])) for i in top_idx]