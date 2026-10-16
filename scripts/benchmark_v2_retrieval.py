# scripts/benchmark_v2_retrieval.py
"""对比：纯向量 vs 纯 BM25 vs RRF 融合 vs RRF+Reranker。"""
import json
from pathlib import Path

from rag.api.service import get_chain
from rag.retrieval.bm25_retriever import BM25Retriever
from rag.retrieval.rrf_fusion import rrf_fusion

chain = get_chain()

with open("benchmarks/eval_set.jsonl", encoding="utf-8") as f:
    items = [json.loads(line) for line in f if line.strip()]

all_docs = chain._store.get_all_documents()
bm25 = BM25Retriever(all_docs)


def hit_at_k(docs, keywords, k):
    for doc, _ in docs[:k]:
        if any(kw in doc.page_content for kw in keywords):
            return 1
    return 0


def raw_dense_search(q, top_k=10):
    """纯向量召回，不走 Reranker。"""
    q_emb = chain._embedder.embed_query(q)
    return chain._store.search(q_emb, top_k=top_k)


def rerank(q, docs, top_k=5):
    """对 docs 做 Reranker 精排。"""
    if chain._reranker is None:
        from rag.retrieval import BgeReranker
        chain._reranker = BgeReranker()
    return chain._reranker.rerank(q, docs, top_k=top_k)


modes = ["dense_rerank", "bm25", "rrf", "rrf_rerank"]

for mode in modes:
    hits = []
    for item in items:
        q = item["question"]
        kws = item["relevant_keywords"]

        if mode == "dense_rerank":
            # v1 基线：向量召回 + Reranker
            results = chain._retrieve(q, top_k=5)
        elif mode == "bm25":
            results = bm25.search(q, top_k=5)
        elif mode == "rrf":
            # 原始向量 + BM25 + RRF
            dense_raw = raw_dense_search(q, top_k=10)
            sparse = bm25.search(q, top_k=10)
            results = rrf_fusion([dense_raw, sparse], top_k=5)
        elif mode == "query_rewrite":
        # 开 QueryRewrite
            results = chain._retrieve(q, top_k=5)   # chain 内部会 QueryRewrite
        else:  # rrf_rerank
            # 原始向量 + BM25 + RRF + Reranker
            dense_raw = raw_dense_search(q, top_k=10)
            sparse = bm25.search(q, top_k=10)
            fused = rrf_fusion([dense_raw, sparse], top_k=15)
            results = rerank(q, fused, top_k=5)

        hits.append(hit_at_k(results, kws, 1))

    print(f"{mode:15s} hit@1 = {sum(hits)/len(hits):.4f}")