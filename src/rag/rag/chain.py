# src/rag/rag/chain.py
from dataclasses import dataclass
from typing import Iterator, List, Tuple

import yaml
from langchain_core.documents import Document

from rag.config import settings
from rag.embedding import build_embedder
from rag.llm import build_llm
from rag.logging_config import get_logger
from rag.retrieval import BgeReranker
from rag.vectorstore import ChromaStore

logger = get_logger(__name__)


@dataclass
class RAGResponse:
    """非流式响应"""
    question: str
    answer: str
    retrieved: List[Tuple[Document, float]]


@dataclass
class StreamChunk:
    """
    流式响应片段：
    - type='content' 时，text 是回答片段
    - type='references' 时，references 是引用列表
    """
    type: str                            # 'content' | 'references'
    text: str = ""                       # 内容片段
    references: List[dict] | None = None # 引用列表


class RAGChain:
    def __init__(self):
        self._embedder = build_embedder()
        self._store = ChromaStore(
            str(settings.resolve(settings.chroma_dir)),
            settings.collection_name,
        )
        self._llm = build_llm()
        self._prompt = self._load_prompt()
        self._reranker: BgeReranker | None = None

    @staticmethod
    def _load_prompt() -> dict:
        p = settings.project_root / "configs" / "prompts" / "rag_qa.yaml"
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    # ==================== 内部工具 ====================

    def _retrieve(self, question: str, top_k: int) -> List[Tuple[Document, float]]:
        """检索 + 重排序，返回 top_k 条 (doc, score)"""
        q_emb = self._embedder.embed_query(question)
        candidates = self._store.search(q_emb, top_k=top_k * 3)

        if self._reranker is None:
            self._reranker = BgeReranker()
        return self._reranker.rerank(question, candidates, top_k=top_k)

    def _build_messages(self, question: str, hits: List[Tuple[Document, float]]) -> List[dict]:
        """把检索结果 + 问题组装成 LLM messages"""
        context = "\n\n".join(
            f"[文档 {i+1} | 相似度 {score:.4f}]\n{doc.page_content}"
            for i, (doc, score) in enumerate(hits)
        )
        user_msg = self._prompt["user_template"].format(
            context=context, question=question
        )
        return [
            {"role": "system", "content": self._prompt["system"]},
            {"role": "user", "content": user_msg},
        ]

    @staticmethod
    def _format_references(hits: List[Tuple[Document, float]]) -> List[dict]:
        """把 hits 转成引用列表（含文件名 + 相似度）"""
        import os
        return [
            {
                "source": os.path.basename(doc.metadata.get("source", "unknown")),
                "page": doc.metadata.get("page"),
                "score": float(score),
            }
            for doc, score in hits
        ]

    # ==================== 对外接口 ====================

    def query(self, question: str, top_k: int | None = None) -> RAGResponse:
        """非流式查询（原方法保持不变）"""
        top_k = top_k or settings.top_k
        hits = self._retrieve(question, top_k)
        messages = self._build_messages(question, hits)
        answer = self._llm.chat(messages)
        return RAGResponse(question=question, answer=answer, retrieved=hits)

    def stream_query(self, question: str, top_k: int | None = None) -> Iterator[StreamChunk]:
        """
        流式查询：先检索，再逐 token yield 回答，最后 yield 引用列表。

        用法：
            for chunk in chain.stream_query("退货", top_k=2):
                if chunk.type == "content":
                    print(chunk.text, end="", flush=True)
                elif chunk.type == "references":
                    print("\\n引用：", chunk.references)
        """
        top_k = top_k or settings.top_k

        # 1. 检索 + 重排序
        hits = self._retrieve(question, top_k)
        logger.info("stream_query 检索完成: %d 条文档", len(hits))

        # 2. 组装 messages
        messages = self._build_messages(question, hits)

        # 3. 流式生成
        for text in self._llm.stream_chat(messages):
            yield StreamChunk(type="content", text=text)

        # 4. 最后 yield 引用
        yield StreamChunk(
            type="references",
            references=self._format_references(hits),
        )