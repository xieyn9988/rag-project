# scripts/smoke_api.py
"""冒烟测试：对本地 API 发三个请求"""
import httpx

BASE = "http://localhost:8000"


def main():
    # 1. health
    print("=== GET /health ===")
    try:
        r = httpx.get(f"{BASE}/health", timeout=10)
        print(r.status_code, r.json())
    except Exception as e:
        print(f"[ERROR] health: {type(e).__name__}: {e}")

    # 2. query
    print("\n=== POST /query ===")
    try:
        r = httpx.post(
            f"{BASE}/query",
            json={"question": "什么是 RAG？", "top_k": 2},
            timeout=120,
        )
        data = r.json()
        print("status:", r.status_code)
        print("answer:", data["answer"][:200], "...")
        print("retrieved:")
        for i, d in enumerate(data["retrieved"]):
            print(f"  [{i+1}] score={d['score']:.4f} | {d['content'][:60]}...")
    except httpx.ReadTimeout:
        print("[ERROR] 请求超时（120s），LLM 或网络问题")
    except Exception as e:
        print(f"[ERROR] query: {type(e).__name__}: {e}")

    # 3. ingest
    print("\n=== POST /ingest (rebuild) ===")
    try:
        r = httpx.post(f"{BASE}/ingest", json={"rebuild": True}, timeout=300)
        print(r.status_code, r.json())
    except Exception as e:
        print(f"[ERROR] ingest: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()