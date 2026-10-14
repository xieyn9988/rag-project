"""
检查 README / .env.example 里的配置值和 config.py 是否一致。
用法：python scripts/check_config_consistency.py
"""
import re
from pathlib import Path

from rag.config import settings

ROOT = Path(__file__).resolve().parents[1]

# 要检查的字段：{字段名: (config.py 里的属性名, README 里的变量名)}
CHECKS = {
    "top_k": "RAG_TOP_K",
    "chunk_size": "RAG_CHUNK_SIZE",
    "chunk_overlap": "RAG_CHUNK_OVERLAP",
    "llm_model": "RAG_LLM_MODEL",
    "embed_model": "RAG_EMBED_MODEL",
}

def check_readme() -> list:
    """README 现在不写默认值了，只检查 .env.example"""
    return []

def check_env_example() -> list:
    """检查 .env.example 的注释值是否和 config.py 一致"""
    issues = []
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    for attr, env_name in CHECKS.items():
        # 匹配 "# RAG_XXX=值" 或 "RAG_XXX=值"
        m = re.search(rf"#?\s*{env_name}=(\S+)", text)
        if not m:
            continue
        env_value = m.group(1).strip()
        code_value = str(getattr(settings, attr))
        if env_value != code_value:
            issues.append(
                f"❌ {env_name}: .env.example={env_value}, config.py={code_value}"
            )
        else:
            print(f"✅ {env_name}={code_value} 一致")
    return issues

def main():
    print("=" * 50)
    print("配置一致性检查")
    print("=" * 50)

    issues = []
    issues += check_readme()
    issues += check_env_example()

    print()
    if issues:
        print(f"发现 {len(issues)} 处不一致：")
        for i in issues:
            print(f"  {i}")
        raise SystemExit(1)
    print("🎉 所有配置一致")


if __name__ == "__main__":
    main()