# scripts/check_sft.py
"""看 SFT 数据前 5 条。"""
import json

print("=" * 60)
print("sft_data.jsonl 前 5 条")
print("=" * 60)
with open("data/finetune/sft_data.jsonl", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= 5:
            break
        if not line.strip():
            continue
        item = json.loads(line)
        print(f"\n--- 第 {i+1} 条 ---")
        print(f"问: {item['instruction']}")
        print(f"答: {item['output'][:150]}")