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
        """非流式调用，返回完整回答文本"""
        resp = self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", settings.llm_temperature),
            max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
        )
        # 记录 usage（用于成本统计）
        if getattr(resp, "usage", None):
            logger.info(
                "LLM usage | prompt=%d, completion=%d, total=%d",
                resp.usage.prompt_tokens,
                resp.usage.completion_tokens,
                resp.usage.total_tokens,
            )
        return resp.choices[0].message.content or ""

    def chat_with_usage(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> tuple[str, dict | None]:
        """非流式调用，返回 (answer, usage)。

        usage 格式：
            {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
        如果 DeepSeek 不返回 usage，返回 (answer, None)。
        """
        resp = self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", settings.llm_temperature),
            max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
        )

        answer = resp.choices[0].message.content or ""

        usage = None
        if getattr(resp, "usage", None):
            usage = {
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
                "total_tokens": resp.usage.total_tokens,
            }
            logger.info(
                "LLM usage | prompt=%d, completion=%d, total=%d",
                usage["prompt_tokens"],
                usage["completion_tokens"],
                usage["total_tokens"],
            )
        return answer, usage

    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        """流式调用：逐 token 返回内容片段（Generator）

        用法：
            for chunk in llm.stream_chat(messages):
                print(chunk, end="", flush=True)
        """
        resp = self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=kwargs.get("temperature", settings.llm_temperature),
            max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
            stream=True,
        )
        usage = None
        for chunk in resp:
            # 收集 usage（通常只有最后一个 chunk 带 usage）
            if getattr(chunk, "usage", None):
                usage = chunk.usage

            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content

        # 流式结束后记录 usage
        if usage:
            logger.info(
                "LLM usage (stream) | prompt=%d, completion=%d, total=%d",
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens,
            )
