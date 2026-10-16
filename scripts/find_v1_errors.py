# scripts/find_v1_errors.py
"""用 LLM 当裁判，找 v1 答错的 case。"""
import json
from rag.api.service import get_chain
from rag.config import settings

chain = get_chain()
settings.query_rewrite_enabled = False   # 关 v2

with open("benchmarks/eval_set.jsonl", encoding="utf-8") as f:
    items = [json.loads(line) for line in f if line.strip()]

JUDGE_PROMPT = """你是评估专家。判断"答案"是否"正确回答了""问题"。

问题：{question}
知识库关键词（正确答案应包含）：{keywords}
答案：{answer}

判断标准：
- 答案**包含了关键词对应的信息** → 1
- 答案**答非所问 / 答错 / 不知道** → 0

只输出一个数字：1 或 0。"""


def judge(question, keywords, answer):
    prompt = JUDGE_PROMPT.format(
        question=question,
        keywords=", ".join(keywords),
        answer=answer,
    )
    resp = chain._llm.chat([{"role": "user", "content": prompt}])
    return 1 if "1" in resp.strip()[:5] else 0


errors = []
for item in items:
    q = item["question"]
    kws = item["relevant_keywords"]
    resp = chain.query(q, top_k=2)
    score = judge(q, kws, resp.answer)

    if score == 0:
        errors.append(item)
        print(f"❌ [{item['id']}] {q}")
        print(f"   答案：{resp.answer[:100]}...")
        print()

print(f"\nv1 答错: {len(errors)}/{len(items)}")