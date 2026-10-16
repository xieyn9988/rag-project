# scripts/test_badcase_e2e.py
"""端到端对比：v1（关 QR）vs v2（开 QR）的"最终答案"。"""
from rag.api.service import get_chain
from rag.config import settings

chain = get_chain()
q = "我下单后多久能收到？"

# 1. 关 QueryRewrite
settings.query_rewrite_enabled = False
resp_v1 = chain.query(q, top_k=2)
print("=" * 60)
print("【v1 baseline（关 QueryRewrite）】")
print("=" * 60)
print(f"答案：\n{resp_v1.answer}\n")
print("引用：")
for i, (doc, score) in enumerate(resp_v1.retrieved, 1):
    print(f"  [{i}] score={score:.4f}")
    print(f"      {doc.page_content[:80].replace(chr(10), ' ')}")
print()

# 2. 开 QueryRewrite
settings.query_rewrite_enabled = True
resp_v2 = chain.query(q, top_k=2)
print("=" * 60)
print("【v2 QueryRewrite（开 QueryRewrite）】")
print("=" * 60)
print(f"答案：\n{resp_v2.answer}\n")
print("引用：")
for i, (doc, score) in enumerate(resp_v2.retrieved, 1):
    print(f"  [{i}] score={score:.4f}")
    print(f"      {doc.page_content[:80].replace(chr(10), ' ')}")