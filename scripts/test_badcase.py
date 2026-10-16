# scripts/test_badcase.py
"""对比 v1（不开 QueryRewrite）vs v2（开 QueryRewrite）。"""
from rag.api.service import get_chain
from rag.config import settings

chain = get_chain()
q = "我下单后多久能收到？"
kws = ["中通", "2-5天", "16:30", "当天发货", "次日发货"]


def check(docs, label):
    print(f"\n=== {label} ===")
    for i, (doc, score) in enumerate(docs[:3], 1):
        hit = any(kw in doc.page_content for kw in kws)
        mark = "✅" if hit else "❌"
        print(f"[{i}] {mark} score={score:.4f}")
        print(f"    {doc.page_content[:100].replace(chr(10), ' ')}")


# 1. 关 QueryRewrite
settings.query_rewrite_enabled = False
check(chain._retrieve(q, top_k=3), "v1 baseline（关 QueryRewrite）")

# 2. 开 QueryRewrite
settings.query_rewrite_enabled = True
check(chain._retrieve(q, top_k=3), "v2 QueryRewrite（开 QueryRewrite）")