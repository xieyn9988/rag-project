"""QueryRewrite：把口语化 query 改写成"检索友好"的形式。"""
from typing import List

from rag.llm.base import BaseLLM
from rag.logging_config import get_logger

logger = get_logger(__name__)


REWRITE_PROMPT = """你是一个查询改写助手。用户输入一个口语化的客服问题，
你把它改写成 3 个"检索友好"的查询，用于在知识库中检索。

改写原则：
1. 保留核心意图（多久、能不能、怎么办）
2. 拆出关键词（时间、条件、流程）
3. 用"知识库可能出现的词"（而不是口语）

用户问题：{query}

输出 3 个查询，每行一个，不要编号，不要解释。"""


class QueryRewriter:
    """QueryRewrite：口语化 query → 检索友好 query。"""

    def __init__(self, llm: BaseLLM):
        self.llm = llm
        self.prompt = REWRITE_PROMPT

    def rewrite(self, query: str) -> List[str]:
        """同步改写，返回 3 个变体。"""
        try:
            answer = self.llm.chat([
                {"role": "user", "content": self.prompt.format(query=query)},
            ])
            lines = [line.strip() for line in answer.splitlines() if line.strip()]
            return lines[:3] if lines else [query]
        except Exception as e:
            logger.warning("QueryRewrite 失败 (%s)，返回原 query", e)
            return [query]