# scripts/test_stream.py
import httpx

print("=== POST /query/stream ===")
with httpx.stream(
    "POST",
    "http://localhost:8000/query/stream",
    json={"question": "什么是 RAG", "top_k": 2},
    timeout=180,
) as r:
    for line in r.iter_lines():
        if line.strip():
            print(line)