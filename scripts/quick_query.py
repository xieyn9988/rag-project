# scripts/quick_query.py
import time
import requests

t0 = time.time()
r = requests.post(
    "http://localhost:8000/query",
    json={"question": "退货"},
    timeout=60,
)
elapsed = time.time() - t0
print(f"{elapsed:.2f}s", r.status_code)
print(r.text[:600])