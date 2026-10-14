# scripts/diagnose_sorting.py
"""看排序问题的 case，召回了什么，Reranker 排了什么。"""
from rag.rag.chain import RAGChain

CASES = [
    ("每天都要用吗？", ["建议使用频率", "新手/初次使用"]),
    ("商品支持7天无理由退货吗？", ["7天无理由退货"]),
]


def preview(text: str, n: int = 100) -> str:
    return text[:n].replace("\n", " ")


def main():
    for question, kws in CASES:
        print("=" * 70)
        print(f"问题: {question}")
        print(f"关键词: {kws}")
        print("=" * 70)

        # 无 Reranker
        chain_no = RAGChain(use_reranker=False)
        docs_no = chain_no._retrieve(question, top_k=5)
        print("\n无 Reranker top 5:")
        for i, (doc, score) in enumerate(docs_no, 1):
            hit = any(kw in doc.page_content for kw in kws)
            mark = "✅" if hit else "  "
            print(f"  [{i}] {mark} score={score:.3f}  {preview(doc.page_content, 80)}")

        # 有 Reranker
        chain_yes = RAGChain(use_reranker=True)
        docs_yes = chain_yes._retrieve(question, top_k=5)
        print("\n有 Reranker top 5:")
        for i, (doc, score) in enumerate(docs_yes, 1):
            hit = any(kw in doc.page_content for kw in kws)
            mark = "✅" if hit else "  "
            print(f"  [{i}] {mark} score={score:.3f}  {preview(doc.page_content, 80)}")

        print()


if __name__ == "__main__":
    main()