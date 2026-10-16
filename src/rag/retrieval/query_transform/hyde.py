from typing import List
from langchain_core.language_models import BaseChatModel

class HyDEGenerator:
    """HyDE：假设文档嵌入，生成虚拟回答文档，再做向量检索"""
    def __init__(self, llm:BaseChatModel):
        self.llm = llm
        self.prompt = """
根据用户问题，写一段简短的回答文本（模拟知识库里面的文档段落），不要分点，直接写段落。
问题：{query}
"""

    async def generate_hypothetical_doc(self, query:str) -> str:
        resp = await self.llm.ainvoke(self.prompt.format(query=query))
        return resp.content.strip()
