# src/rag/llm/base.py
from abc import ABC, abstractmethod
from typing import Dict, List


class BaseLLM(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str: ...