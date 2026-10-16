"""混合检索：BM25（关键词）+ 向量（语义）双路召回 → RRF 倒数排序融合 → 送 Reranker。"""
from __future__ import annotations
from src.rag.retrieval.bm25_retriever import BM25Retriever

RRF_K = 60  # 经典默认值，可进 config


def rrf_fuse(ranked_a: list[tuple[str, str, float]],
             ranked_b: list[tuple[str, str, float]],
             top_k: int = 6) -> list[tuple[str, str, float]]:
    """RRF: score(d) = Σ 1/(k + rank)。两路都有的 chunk 天然排前——
    这正是修复『字面重叠但语义弱』误召回的机制：防伪 chunk 只在语义路高分，
    发货 chunk 在 BM25 路也高分，融合后被顶上去。"""
    pool: dict[str, float] = {}
    for ranked in (ranked_a, ranked_b):
        for rank, (cid, text, _) in enumerate(ranked):
            pool[cid] = pool.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
    id2text = {cid: t for _, t in [(cid, t) for ranked in (ranked_a, ranked_b) for cid, t, _ in ranked]}
    fused = sorted(pool.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [(cid, id2text[cid], s) for cid, s in fused]


class HybridRetriever:
    def __init__(self, dense_retriever, bm25: BM25Retriever):
        self.dense = dense_retriever   # 你现有的向量召回（ChromaDB），返回同构三元组
        self.bm25 = bm25

    def retrieve(self, query: str, top_k: int = 6):
        dense_hits = self.dense.retrieve(query, top_k=top_k)
        bm25_hits = self.bm25.retrieve(query, top_k=top_k)
        return rrf_fuse(bm25_hits, dense_hits, top_k=top_k)
