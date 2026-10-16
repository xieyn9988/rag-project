# scripts/check_eval_v2.py
"""看 v2 评估的 R=0 case。"""
import json

with open("benchmarks/results/eval_v2.json", encoding="utf-8") as f:
    d = json.load(f)

print("=" * 60)
print("summary")
print("=" * 60)
print(json.dumps(d["summary"], indent=2, ensure_ascii=False))

print()
print("=" * 60)
print("R=0 的 case（答非所问）")
print("=" * 60)
for r in d["raw"]:
    if r["r"] == 0:
        # 从评测集里找这个问题
        with open("benchmarks/eval_set.jsonl", encoding="utf-8") as f:
            items = [json.loads(line) for line in f if line.strip()]
        item = next((i for i in items if i["id"] == r["id"]), None)
        q = item["question"] if item else "?"
        print(f"[{r['id']:2d}] {q}  →  F={r['f']} R={r['r']}")

print()
print("=" * 60)
print("F=0 的 case（幻觉）")
print("=" * 60)
for r in d["raw"]:
    if r["f"] == 0:
        print(f"[{r['id']:2d}] F={r['f']} R={r['r']}")