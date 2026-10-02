# src/rag/llm/base.py
from abc import ABC, abstractmethod
from typing import Dict, Iterator, List


class BaseLLM(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """非流式对话，返回完整回答文本"""

    @abstractmethod
    def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        """流式对话，逐 token yield 文本片段

        用法：
            for chunk in llm.stream_chat(messages):
                print(chunk, end="", flush=True)
        """