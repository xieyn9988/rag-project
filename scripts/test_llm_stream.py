# scripts/test_llm_stream.py
from rag.logging_config import setup_logging
setup_logging()

from rag.llm import build_llm

print("=== 直接测试 DeepSeekLLM.stream_chat ===")
llm = build_llm()
count = 0
for chunk in llm.stream_chat([{"role": "user", "content": "用一句话说什么是 RAG"}]):
    print(f"[{count}] {chunk!r}")
    count += 1
    if count >= 20:
        print("... (只显示前 20 个 chunk)")
        break
print(f"\n共收到 {count} 个 chunk")