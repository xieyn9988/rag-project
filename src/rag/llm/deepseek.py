# src/rag/llm/deepseek.py
from typing import Dict, Iterator, List

from openai import OpenAI

from rag.config import settings
from rag.llm.base import BaseLLM
from rag.logging_config import get_logger

logger = get_logger(__name__)


class DeepSeekLLM(BaseLLM):
    def __init__(self):
        if not settings.llm_api_key:
            raise ValueError("未配置 RAG_LLM_API_KEY，请检查 .env")
        self._client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=60.0,
        )
        self._model = settings.llm_model
        logger.info("DeepSeekLLM 就绪: %s", self._model)

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """非流式调用（保持原有行为）"""
        resp = self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", settings.llm_temperature),
            max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
        )
        return resp.choices[0].message.content or ""

    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        """
        流式调用：逐 token 返回内容片段（Generator）
        用法：
            for chunk in llm.stream_chat(messages):
                print(chunk, end="", flush=True)
        """
        resp = self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", settings.llm_temperature),
            max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
            stream=True,  # ⚠️ 关键：开启流式
        )
        for chunk in resp:
            # 兼容 OpenAI SDK 不同版本
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content