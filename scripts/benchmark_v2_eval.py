# scripts/benchmark_v2_eval.py
"""自写 RAG 评估（RAGAS 替代）——用 DeepSeek 当裁判。

指标：
- Faithfulness：答案是否"忠于"检索文档
- Answer Relevancy：答案是否"回应"问题

用法：
    python scripts/benchmark_v2_eval.py
"""
import json
import time
from pathlib import Path

from rag.api.service import get_chain

chain = get_chain()

with open("benchmarks/eval_set.jsonl", encoding="utf-8") as f:
    items = [json.loads(line) for line in f if line.strip()]


# ==================== Prompt ====================

FAITHFULNESS_PROMPT = """你是评估专家。判断"答案"是否"忠于""检索文档"。

检索文档：
{context}

答案：
{answer}

判断标准：
- 答案中的**每个事实**都能在检索文档里找到 → 忠实
- 答案里**编造**了文档没有的内容 → 不忠实

**只输出一个数字：1（忠实）或 0（不忠实）。不要输出任何其他内容。**"""


RELEVANCY_PROMPT = """你是评估专家。判断"答案"是否"回应了""问题"。

问题：{question}
答案：{answer}

判断标准：
- 答案**直接回应**了问题 → 1
- 答案**答非所问** / **绕开问题** / **说不知道** → 0

**只输出一个数字：1 或 0。不要输出任何其他内容。**"""


# ==================== 判定 ====================

def ask_llm(prompt: str) -> int:
    """用 DeepSeek 判定，返回 0 或 1。"""
    answer = chain._llm.chat([{"role": "user", "content": prompt}])
    return 1 if "1" in answer.strip()[:5] else 0


# ==================== 主流程 ====================

def main():
    faithful_scores = []
    relevant_scores = []

    print(f"评测集: {len(items)} 条")
    print()

    for item in items:
        q = item["question"]
        resp = chain.query(q)

        context = "\n\n".join(doc.page_content for doc, _ in resp.retrieved)

        # Faithfulness
        f = ask_llm(FAITHFULNESS_PROMPT.format(context=context, answer=resp.answer))
        faithful_scores.append(f)

        # Answer Relevancy
        r = ask_llm(RELEVANCY_PROMPT.format(question=q, answer=resp.answer))
        relevant_scores.append(r)

        print(f"[{item['id']:2d}] F={f} R={r} | {q[:30]}")

        time.sleep(0.3)

    n = len(items)
    summary = {
        "n": n,
        "faithfulness": round(sum(faithful_scores) / n, 4),
        "answer_relevancy": round(sum(relevant_scores) / n, 4),
    }

    print()
    print("=" * 60)
    print("自写评估结果")
    print("=" * 60)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    out = Path("benchmarks/results/eval_v2.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"summary": summary, "raw": [
            {"id": it["id"], "f": f, "r": r}
            for it, f, r in zip(items, faithful_scores, relevant_scores)
        ]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n结果已保存: {out}")


if __name__ == "__main__":
    main()