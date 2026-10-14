# scripts/diagnose_errors.py
"""诊断评测结果：哪些是知识库缺失，哪些是排序问题。"""
import json
from pathlib import Path

# 读有 Reranker 的结果
with_rerank = json.load(
    open("benchmarks/results/retrieval_with_rerank.json", encoding="utf-8")
)

print("=" * 60)
print("hit@5=0（知识库无答案）")
print("=" * 60)
for r in with_rerank["raw"]:
    if r["hit@5"] == 0:
        print(f"  [{r['id']:2d}] {r['question']}  ({r['category']})")

print()
print("=" * 60)
print("hit@1=0 但 hit@5=1（排序问题，Reranker 没救回来）")
print("=" * 60)
for r in with_rerank["raw"]:
    if r["hit@1"] == 0 and r["hit@5"] == 1:
        print(f"  [{r['id']:2d}] {r['question']}  ({r['category']})")

print()
print("=" * 60)
print("hit@1=0 全部")
print("=" * 60)
for r in with_rerank["raw"]:
    if r["hit@1"] == 0:
        print(f"  [{r['id']:2d}] {r['question']}  hit@3={r['hit@3']}  hit@5={r['hit@5']}")