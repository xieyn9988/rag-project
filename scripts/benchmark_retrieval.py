# scripts/benchmark_retrieval.py
"""
测检索准确率：Hit@k 和 MRR。
用法：
    python scripts/benchmark_retrieval.py                # 有 reranker
    python scripts/benchmark_retrieval.py --no-reranker  # 禁用 reranker
"""
import argparse
import json
from pathlib import Path

from rag.api.service import get_chain


def is_relevant(text: str, keywords: list[str]) -> bool:
    return any(kw in text for kw in keywords)


def hit_at_k(docs, keywords, k):
    for doc, _ in docs[:k]:
        if is_relevant(doc.page_content, keywords):
            return 1
    return 0


def mrr(docs, keywords):
    for i, (doc, _) in enumerate(docs, start=1):
        if is_relevant(doc.page_content, keywords):
            return 1.0 / i
    return 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-reranker", action="store_true", help="禁用 reranker")
    parser.add_argument("--eval", default="benchmarks/eval_set.jsonl")
    parser.add_argument("--out", default=None)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    chain = get_chain()

    if args.no_reranker:
        from rag.rag.chain import RAGChain
        chain = RAGChain(use_reranker=False)   # 独立实例
        print("⚠️ 已禁用 Reranker（独立实例）")
    else:
        chain = get_chain()
        print("✅ 使用 Reranker")        

    with open(args.eval, encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]

    print(f"评测集: {len(items)} 条")

    results = []
    for item in items:
        docs = chain._retrieve(item["question"], top_k=args.top_k)
        kws = item["relevant_keywords"]
        results.append({
            "id": item["id"],
            "question": item["question"],
            "category": item.get("category"),
            "hit@1": hit_at_k(docs, kws, 1),
            "hit@3": hit_at_k(docs, kws, 3),
            "hit@5": hit_at_k(docs, kws, 5),
            "mrr": mrr(docs, kws),
        })

    n = len(results)
    summary = {
        "n": n,
        "use_reranker": not args.no_reranker,
        "hit@1": sum(r["hit@1"] for r in results) / n,
        "hit@3": sum(r["hit@3"] for r in results) / n,
        "hit@5": sum(r["hit@5"] for r in results) / n,
        "mrr": sum(r["mrr"] for r in results) / n,
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))

    out = args.out or (
        "benchmarks/results/retrieval_no_rerank.json"
        if args.no_reranker
        else "benchmarks/results/retrieval_with_rerank.json"
    )
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(
        json.dumps({"summary": summary, "raw": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"结果已保存: {out}")


if __name__ == "__main__":
    main()