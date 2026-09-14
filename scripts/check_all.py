# scripts/check_all.py
"""一键自检：检查 RAG 项目各层是否正常"""
import os
import sys
import subprocess
from pathlib import Path

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"


def check(name, func):
    """执行一个检查项，打印结果"""
    try:
        ok, detail = func()
        mark = PASS if ok else FAIL
        print(f"{mark} {name}")
        if detail:
            print(f"       {detail}")
        return ok
    except Exception as e:
        print(f"{FAIL} {name}")
        print(f"       {type(e).__name__}: {e}")
        return False


def check_python_env():
    """检查 Python 环境"""
    exe = sys.executable
    ok = "envs\\chroma_env" in exe or "envs/chroma_env" in exe
    return ok, exe


def check_rag_import():
    """检查 rag 包可导入"""
    import rag
    return True, rag.__file__


def check_config():
    """检查配置加载"""
    from rag.config import settings
    ok = settings.llm_api_key.startswith("sk-")
    return ok, f"api_key={settings.llm_api_key[:8]}..."


def check_ingestion():
    """检查文档加载"""
    from rag.config import settings
    from rag.ingestion import load_documents
    docs = load_documents(settings.resolve(settings.data_dir))
    return len(docs) > 0, f"loaded {len(docs)} docs"


def check_embedder():
    """检查 embedding"""
    from rag.embedding import build_embedder
    e = build_embedder()
    v = e.embed_query("test")
    return len(v) == e.dimension, f"dim={e.dimension}"


def check_llm():
    """检查 LLM"""
    from rag.llm import build_llm
    llm = build_llm()
    ans = llm.chat([{"role": "user", "content": "回复'OK'"}])
    return len(ans) > 0, ans[:50]


def check_api_health():
    """检查 API /health"""
    import httpx
    try:
        r = httpx.get("http://localhost:8000/health", timeout=5)
        data = r.json()
        return data.get("status") == "ok", data
    except Exception:
        return False, "API not reachable (可能没启动)"


def check_docker_container():
    """检查 Docker 容器状态"""
    r = subprocess.run(
        ["docker", "compose", "ps", "--format", "json"],
        capture_output=True, text=True,
        encoding="utf-8", errors="ignore",     # ← 新增这两行
        cwd=Path(__file__).parent.parent
    )

    if not r.stdout.strip():
        return False, "没有容器在跑"
    import json
    # 每行一个 JSON 对象
    lines = [l for l in r.stdout.strip().split("\n") if l]
    for line in lines:
        data = json.loads(line)
        if data.get("Service") == "rag-api":
            status = data.get("Status", "")
            healthy = "healthy" in status.lower()
            return healthy, status
    return False, "未找到 rag-api 容器"


def main():
    print("=" * 60)
    print("RAG 项目全链路自检")
    print("=" * 60)
    print()

    results = []
    results.append(check("1. Python 环境", check_python_env))
    results.append(check("2. rag 包导入", check_rag_import))
    results.append(check("3. 配置加载", check_config))
    results.append(check("4. 文档加载", check_ingestion))
    results.append(check("5. Embedding 模型", check_embedder))
    results.append(check("6. LLM 调用", check_llm))
    results.append(check("7. API /health", check_api_health))
    results.append(check("8. Docker 容器", check_docker_container))

    print()
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"结果: {passed}/{total} 通过")
    print("=" * 60)

    if passed < total:
        print("\n未通过的项，看上面 [FAIL] 行")


if __name__ == "__main__":
    main()