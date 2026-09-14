# src/rag/embedding/local_bge.py
from typing import List

from sentence_transformers import SentenceTransformer

from rag.config import settings
from rag.embedding.base import BaseEmbedder
from rag.logging_config import get_logger

logger = get_logger(__name__)


class LocalBgeEmbedder(BaseEmbedder):
    """基于 sentence-transformers 的本地中文 embedding"""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.embed_model
        logger.info("加载 embedding 模型: %s", self.model_name)
        self._model = SentenceTransformer(self.model_name)
        try:
            self._dim = self._model.get_embedding_dimension()
        except AttributeError:
            self._dim = self._model.get_sentence_embedding_dimension()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # BGE 官方推荐对文档加 "passage:" 前缀
        texts = [f"passage: {t}" for t in texts]
        vecs = self._model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return vecs.tolist()

    def embed_query(self, text: str) -> List[float]:
        # BGE 官方推荐对查询加 "query:" 前缀
        vec = self._model.encode(
            [f"query: {text}"], normalize_embeddings=True, show_progress_bar=False
        )
        return vec[0].tolist()

    @property
    def dimension(self) -> int:
        return self._dim