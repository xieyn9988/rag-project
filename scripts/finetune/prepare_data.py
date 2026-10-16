# scripts/finetune/prepare_data.py
"""从 v1 知识库生成微调数据（扩法 1+3）。

扩法 1：prompt 生成 8-10 个问法（不是 3-5 个）
扩法 3：跑 3 轮 + 去重

输出：
- data/finetune/sft_data.jsonl（训练集）
- data/finetune/sft_data_val.jsonl（验证集）
"""
import json
import random
import time
from pathlib import Path

from rag.api.service import get_chain

chain = get_chain()

OUT = Path("data/finetune/sft_data.jsonl")
OUT.parent.mkdir(parents=True, exist_ok=True)


# 读 v1 知识库
with open("data/text/HFP客服知识库.txt", encoding="utf-8") as f:
    knowledge = f.read()


# 扩法 1：prompt 生成 8-10 个问法
GEN_PROMPT = """你是电商客服知识库助手。根据以下"知识片段"，生成 **8-10 个**"用户可能问的问题" + "客服标准回答"。

知识片段：
{knowledge}

要求：
1. 问题要"口语化"（像真实用户），**不同问法**（不要重复）
2. 回答要"专业 + 友好"（像客服），**基于知识片段**
3. 每条"问题-回答"一行 JSON：{{"question": "...", "answer": "..."}}
4. 只输出 JSON 行，不要解释
"""


# 通用数据（防遗忘）
GENERAL_DATA = [
    {"instruction": "1+1 等于几？", "input": "", "output": "1+1=2。"},
    {"instruction": "介绍一下你自己。", "input": "", "output": "我是一个 AI 助手，可以回答问题。"},
    {"instruction": "什么是机器学习？", "input": "", "output": "机器学习是 AI 的分支，让计算机从数据中学习规律。"},
    {"instruction": "中国的首都是哪里？", "input": "", "output": "中国的首都是北京。"},
    {"instruction": "水的化学式是什么？", "input": "", "output": "水的化学式是 H2O。"},
    {"instruction": "太阳从哪边升起？", "input": "", "output": "太阳从东边升起。"},
    {"instruction": "一年有多少天？", "input": "", "output": "平年 365 天，闰年 366 天。"},
    {"instruction": "怎么煮鸡蛋？", "input": "", "output": "水开后放鸡蛋，煮 5-8 分钟即可。"},
    {"instruction": "Python 是什么？", "input": "", "output": "Python 是一种编程语言。"},
    {"instruction": "怎么学习编程？", "input": "", "output": "从基础语法开始，多写代码，多实践。"},
]


def main():
    print(f"知识库长度: {len(knowledge)} 字符")

    # 用 300 字切块
    chunks = [knowledge[i:i+300] for i in range(0, len(knowledge), 300)]
    print(f"分 {len(chunks)} 块")

    all_sft = []

    # 扩法 3：跑 3 轮
    for round_i in range(3):
        print(f"\n=== 第 {round_i+1}/3 轮 ===")
        for i, chunk in enumerate(chunks, 1):
            try:
                resp = chain._llm.chat([
                    {"role": "user", "content": GEN_PROMPT.format(knowledge=chunk)},
                ])
                for line in resp.splitlines():
                    line = line.strip()
                    if not line or not line.startswith("{"):
                        continue
                    try:
                        item = json.loads(line)
                        if "question" in item and "answer" in item:
                            all_sft.append({
                                "instruction": item["question"],
                                "input": "",
                                "output": item["answer"],
                            })
                    except json.JSONDecodeError:
                        continue
            except Exception as e:
                print(f"  失败: {e}")
            time.sleep(0.3)

        print(f"  第 {round_i+1} 轮累计: {len(all_sft)} 条")

    print(f"\n生成原始: {len(all_sft)} 条")

    # 去重（按 instruction）
    seen = set()
    unique_sft = []
    for item in all_sft:
        key = item["instruction"]
        if key not in seen:
            seen.add(key)
            unique_sft.append(item)

    print(f"去重后: {len(unique_sft)} 条")

    # 混 15% 通用数据
    n_general = max(10, int(len(unique_sft) * 0.15 / 0.85))
    general = random.sample(GENERAL_DATA * 20, min(n_general, len(GENERAL_DATA) * 20))
    all_data = unique_sft + general
    random.shuffle(all_data)

    print(f"混入通用: {len(general)} 条")
    print(f"合计: {len(all_data)} 条")

    # 90/10 划分
    n = len(all_data)
    n_val = max(5, int(n * 0.1))
    train = all_data[:-n_val]
    val = all_data[-n_val:]

    with open(OUT, "w", encoding="utf-8") as f:
        for item in train:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    val_out = OUT.parent / "sft_data_val.jsonl"
    with open(val_out, "w", encoding="utf-8") as f:
        for item in val:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n训练集: {len(train)} 条 → {OUT}")
    print(f"验证集: {len(val)} 条 → {val_out}")


if __name__ == "__main__":
    main()