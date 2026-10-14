# scripts/check_rerank_diff.py
"""对比无/有 Reranker 的召回内容，看 Reranker 把哪些 chunk 换了位置。"""
from rag.rag.chain import RAGChain

QUESTIONS = [
    "什么时候发货？",
    "16:30之后下单什么时候发货？",
]


def preview(text: str, n: int = 100) -> str:
    """取前 n 字符，把换行替换成空格。"""
    return text[:n].replace("\n", " ")


def show(chain, label: str):
    print(f"\n{'=' * 60}")
    print(f"{label}")
    print(f"{'=' * 60}")
    for q in QUESTIONS:
        print(f"\n=== {q} ===")
        docs = chain._retrieve(q, top_k=3)
        for i, (doc, score) in enumerate(docs, 1):
            print(f"  [{i}] score={score:.3f}")
            print(f"      {preview(doc.page_content, 120)}")


def main():
    # 无 Reranker
    chain_no = RAGChain(use_reranker=False)
    show(chain_no, "无 Reranker")

    # 有 Reranker
    chain_yes = RAGChain(use_reranker=True)
    show(chain_yes, "有 Reranker")


if __name__ == "__main__":
    main()