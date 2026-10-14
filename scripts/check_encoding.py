# scripts/check_encoding.py
"""检查文件编码。"""
from pathlib import Path

for filename in ["docker-compose.yml", "Dockerfile", ".dockerignore"]:
    p = Path(filename)
    if not p.exists():
        print(f"=== {filename} 不存在 ===")
        continue

    data = p.read_bytes()[:200]
    print(f"=== {filename} ===")
    print(f"  前 32 字节: {data[:32].hex()}")
    for enc in ["utf-8", "gbk", "utf-16"]:
        try:
            text = data.decode(enc)
            print(f"  {enc}: {text[:80]!r}")
        except Exception as e:
            print(f"  {enc}: 失败 - {type(e).__name__}")
    print()