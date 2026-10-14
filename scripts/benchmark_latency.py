# scripts/benchmark_latency.py
"""
测首字延迟(TTFT)和完整响应时间。
用法：
    python scripts/benchmark_latency.py
"""

import json
import time
from pathlib import Path

import requests

BASE = "http://localhost:8000"
N_RUNS = 30
TOP_K = None  # None 表示用服务端默认值

QUESTIONS = [
    "退货",
    "快递到不了了怎么申请补发？",
    "满减活动什么时候结束？",
]


def build_body(question: str) -> dict:
    """构造请求体：TOP_K 为 None 时不传 top_k，让服务端用默认值。"""
    body = {"question": question}
    if TOP_K is not None:
        body["top_k"] = TOP_K
    return body


def pct(data: list, p: float) -> float:
    data = sorted(data)
    idx = min(int(len(data) * p), len(data) - 1)
    return data[idx]


def measure_non_stream(question: str) -> float:
    """测非流式：返回耗时（秒）"""
    t0 = time.perf_counter()
    r = requests.post(
        f"{BASE}/query",
        json=build_body(question),
        timeout=120,
    )
    r.raise_for_status()
    return time.perf_counter() - t0


def measure_stream(question: str) -> tuple[float | None, float]:
    """测流式：返回 (TTFT, total)"""
    t0 = time.perf_counter()
    ttft = None

    with requests.post(
        f"{BASE}/query/stream",
        json=build_body(question),  # ← 只改这一行
        stream=True,
        timeout=120,
    ) as r:
        r.raise_for_status()
        for raw in r.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8", errors="ignore")
            if not line.startswith("data: "):
                continue
            payload = line[6:].strip()
            if payload == "[DONE]":
                break
            try:
                evt = json.loads(payload)
            except json.JSONDecodeError:
                continue
            # 兼容多种字段名
            if ttft is None and (evt.get("type") == "content"):
                ttft = time.perf_counter() - t0

    return ttft, time.perf_counter() - t0


def main():
    print("=" * 60)
    print("1. 非流式 /query 延迟")
    print("=" * 60)

    non_stream_times = []
    for q in QUESTIONS:
        for i in range(N_RUNS):
            try:
                dt = measure_non_stream(q)
                non_stream_times.append(dt)
                if (i + 1) % 5 == 0:
                    print(f"  {q} {i + 1}/{N_RUNS}: {dt:.2f}s", flush=True)
            except Exception as e:
                print(f"  [失败] {q}: {e}")

    if non_stream_times:
        print(f"\n非流式延迟:")
        print(f"  P50: {pct(non_stream_times, 0.50):.3f}s")
        print(f"  P95: {pct(non_stream_times, 0.95):.3f}s")
        print(f"  P99: {pct(non_stream_times, 0.99):.3f}s")

    print()
    print("=" * 60)
    print("2. 流式 /query/stream 延迟")
    print("=" * 60)

    ttfts, totals = [], []
    for q in QUESTIONS:
        for i in range(N_RUNS):
            try:
                ttft, total = measure_stream(q)
                totals.append(total)
                if ttft is not None:
                    ttfts.append(ttft)
                if (i + 1) % 5 == 0:
                    ttft_str = f"{ttft:.2f}s" if ttft else "N/A"
                    print(
                        f"  {q} {i + 1}/{N_RUNS}: TTFT={ttft_str} Total={total:.2f}s",
                        flush=True,
                    )
            except Exception as e:
                print(f"  [失败] {q}: {e}")

    summary = {
        "n_runs_per_question": N_RUNS,
        "n_questions": len(QUESTIONS),
        "non_stream": {
            "P50_s": pct(non_stream_times, 0.50) if non_stream_times else None,
            "P95_s": pct(non_stream_times, 0.95) if non_stream_times else None,
            "P99_s": pct(non_stream_times, 0.99) if non_stream_times else None,
        },
        "stream": {
            "TTFT_P50_s": pct(ttfts, 0.50) if ttfts else None,
            "TTFT_P95_s": pct(ttfts, 0.95) if ttfts else None,
            "TTFT_max_s": round(max(ttfts), 3) if ttfts else None,  # ← 新增
            "Total_P50_s": pct(totals, 0.50) if totals else None,
            "Total_P95_s": pct(totals, 0.95) if totals else None,
            "Total_max_s": round(max(totals), 3) if totals else None,
        },
    }

    print()
    print("=" * 60)
    print("汇总")
    print("=" * 60)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    out = Path("benchmarks/results/latency.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "summary": summary,
                "raw": {
                    "non_stream_times": non_stream_times,
                    "stream_ttfts": ttfts,
                    "stream_totals": totals,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n结果已保存: {out}")


if __name__ == "__main__":
    main()
