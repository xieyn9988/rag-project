# src/rag/embedding/base.py
from abc import ABC, abstractmethod
from typing import List


class BaseEmbedder(ABC):
    """Embedding 抽象接口，方便后续换供应商"""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量编码文档"""

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """编码查询"""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度"""