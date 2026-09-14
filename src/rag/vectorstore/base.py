# src/rag/vectorstore/base.py
from abc import ABC, abstractmethod
from typing import List, Optional

from langchain_core.documents import Document


class BaseVectorStore(ABC):
    @abstractmethod
    def add(self, documents: List[Document], embeddings: List[List[float]]) -> None: ...

    @abstractmethod
    def search(
        self, query_embedding: List[float], top_k: int, where: Optional[dict] = None
    ) -> List[tuple[Document, float]]:
        """返回 (文档, 相似度分数) 列表，分数越大越相似"""

    @abstractmethod
    def delete_by_source(self, source: str) -> int: ...

    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def reset(self) -> None: ...