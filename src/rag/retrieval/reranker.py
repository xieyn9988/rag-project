# src/rag/retrieval/reranker.py
from typing import List, Tuple

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from rag.logging_config import get_logger

logger = get_logger(__name__)


class BgeReranker:
    """BGE CrossEncoder 重排序器"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        logger.info("加载 reranker 模型: %s", model_name)
        self._model = CrossEncoder(model_name)
        self._model_name = model_name

    def rerank(
        self,
        query: str,
        hits: List[Tuple[Document, float]],
        top_k: int,
    ) -> List[Tuple[Document, float]]:
        """
        对候选 hits 精排，返回 top_k。

        参数:
            query: 用户查询
            hits: 向量召回结果 [(Document, similarity), ...]
            top_k: 精排后保留数量

        返回:
            [(Document, rerank_score), ...]  按分数降序
        """
        if not hits:
            return []

        pairs = [(query, doc.page_content) for doc, _ in hits]
        scores = self._model.predict(pairs)
        ranked = sorted(zip(hits, scores), key=lambda x: -x[1])[:top_k]
        return [(doc, float(score)) for (doc, _), score in ranked]