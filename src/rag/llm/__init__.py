from rag.llm.base import BaseLLM
from rag.llm.deepseek import DeepSeekLLM


def build_llm(name: str = "deepseek") -> BaseLLM:
    if name == "deepseek":
        return DeepSeekLLM()
    raise ValueError(f"Unknown LLM: {name}")


__all__ = ["BaseLLM", "build_llm"]