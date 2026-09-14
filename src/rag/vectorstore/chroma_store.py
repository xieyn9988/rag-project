# src/rag/vectorstore/chroma_store.py
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_core.documents import Document

from rag.logging_config import get_logger
from rag.vectorstore.base import BaseVectorStore

logger = get_logger(__name__)


class ChromaStore(BaseVectorStore):
    def __init__(self, persist_dir: str, collection_name: str):
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # 显式指定余弦距离
        )
        logger.info(
            "ChromaStore 就绪: %s/%s (现有 %d 条)",
            persist_dir, collection_name, self._collection.count(),
        )

    def add(self, documents: List[Document], embeddings: List[List[float]]) -> None:
        if not documents:
            return
        ids = [
            f"doc_{abs(hash((d.page_content, d.metadata.get('source', ''))))}"
            for d in documents
        ]
        self._collection.upsert(
            ids=ids,
            documents=[d.page_content for d in documents],
            metadatas=[d.metadata for d in documents],
            embeddings=embeddings,
        )
        logger.info("写入/更新 %d 条", len(documents))

    def search(
        self, query_embedding: List[float], top_k: int, where: Optional[dict] = None
    ) -> List[tuple[Document, float]]:
        res = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )
        docs, dists, metas = res["documents"][0], res["distances"][0], res["metadatas"][0]
        out = []
        for text, dist, meta in zip(docs, dists, metas):
            similarity = 1.0 - dist  # cosine 距离 → 相似度
            out.append((Document(page_content=text, metadata=meta or {}), similarity))
        return out

    def delete_by_source(self, source: str) -> int:
        before = self._collection.count()
        self._collection.delete(where={"source": source})
        after = self._collection.count()
        return before - after

    def count(self) -> int:
        return self._collection.count()

    def reset(self) -> None:
        name = self._collection.name
        self._client.delete_collection(name)
        self._collection = self._client.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )
        logger.warning("集合 %s 已重置", name)