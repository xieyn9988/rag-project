# scripts/check_eval.py
"""看评测集里的 `relevant_keywords`。"""
import json

with open("benchmarks/eval_set.jsonl", encoding="utf-8") as f:
    items = [json.loads(line) for line in f if line.strip()]

print(f"共 {len(items)} 条\n")

for item in items:
    print(f"[{item['id']:2d}] {item['question'][:25]:25s} | kws={item['relevant_keywords']}")