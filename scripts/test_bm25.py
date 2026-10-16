# scripts/test_bm25.py
"""测试 BM25 检索。"""
from rag.api.service import get_chain
from rag.retrieval.bm25_retriever import BM25Retriever

chain = get_chain()

# 1. 从 ChromaDB 拿所有文档
if hasattr(chain._store, "get_all_documents"):
    all_docs = chain._store.get_all_documents()
else:
    print("⚠️ get_all_documents 不存在")
    # fallback：用 search 拿
    q_emb = chain._embedder.embed_query("退货")
    all_docs = [doc for doc, _ in chain._store.search(q_emb, top_k=50)]

print(f"共 {len(all_docs)} 篇文档")

# 2. 建 BM25
bm25 = BM25Retriever(all_docs)

# 3. 搜"我下单后多久能收到？"
query = "我下单后多久能收到？"
results = bm25.search(query, top_k=3)
print(f"\n=== BM25 top 3: {query} ===")
for i, (doc, score) in enumerate(results, 1):
    print(f"[{i}] score={score:.4f}")
    print(f"    {doc.page_content[:120].replace(chr(10), ' ')}")
    print()