# scripts/check_kb.py
"""检查清理后的知识库：召回是否只剩 HFP 客服知识库。"""
from rag.api.service import get_chain

chain = get_chain()

for q in ["退货", "物流", "活动", "发票", "售后", "发货"]:
    print(f"=== {q} ===")
    docs = chain._store.search(chain._embedder.embed_query(q), top_k=3)
    for doc, score in docs:
        source = doc.metadata.get("source", "?")
        content = doc.page_content[:80].replace("\n", " ")
        print(f"  [{score:.3f}] {source}")
        print(f"    {content}")
    print()