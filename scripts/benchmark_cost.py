# scripts/benchmark_cost.py
"""统计单次问答的 token 用量和成本（用真实 usage）。"""
import json
from pathlib import Path

from rag.api.service import get_chain

QUESTIONS = [
    "退货流程是什么？",
    "什么时候发货？",
    "快递一般多久能到？",
    "双11活动什么时候？",
    "商品破损了运费谁承担？",
]

N_RUNS = 5

PRICE_INPUT = 1.0 / 1_000_000   # ¥1/百万 input tokens
PRICE_OUTPUT = 2.0 / 1_000_000  # ¥2/百万 output tokens

AGENT_MONTHLY_SALARY = 6000
AGENT_DAILY_QUERIES = 500
WORK_DAYS_PER_MONTH = 22


def main():
    chain = get_chain()
    rows = []

    for q in QUESTIONS:
        for i in range(N_RUNS):
            resp = chain.query(q)
            usage = resp.usage or {}
            rows.append({
                "question": q,
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            })
            print(
                f"  {q[:10]} {i+1}/{N_RUNS}: "
                f"in={usage.get('prompt_tokens')}, "
                f"out={usage.get('completion_tokens')}",
                flush=True,
            )

    n = len(rows)
    avg_in = sum(r["input_tokens"] for r in rows) / n
    avg_out = sum(r["output_tokens"] for r in rows) / n

    cost_per_query = avg_in * PRICE_INPUT + avg_out * PRICE_OUTPUT
    cost_daily = cost_per_query * AGENT_DAILY_QUERIES
    cost_monthly = cost_daily * WORK_DAYS_PER_MONTH
    cost_per_query_human = AGENT_MONTHLY_SALARY / WORK_DAYS_PER_MONTH / AGENT_DAILY_QUERIES

    summary = {
        "n_samples": n,
        "avg_input_tokens": round(avg_in, 1),
        "avg_output_tokens": round(avg_out, 1),
        "cost_per_query_cny": round(cost_per_query, 6),
        "cost_daily_cny": round(cost_daily, 4),
        "cost_monthly_cny": round(cost_monthly, 2),
        "cost_per_query_human_cny": round(cost_per_query_human, 4),
        "cost_reduction_pct": round((1 - cost_per_query / cost_per_query_human) * 100, 2),
        "assumptions": {
            "agent_monthly_salary_cny": AGENT_MONTHLY_SALARY,
            "agent_daily_queries": AGENT_DAILY_QUERIES,
            "work_days_per_month": WORK_DAYS_PER_MONTH,
            "price_input_per_million_cny": 1.0,
            "price_output_per_million_cny": 2.0,
        },
        "data_source": "实测：resp.usage（真实 token）",
    }

    print()
    print("=" * 60)
    print("成本统计")
    print("=" * 60)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    out = Path("benchmarks/results/cost.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"summary": summary, "raw": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n结果已保存: {out}")


if __name__ == "__main__":
    main()