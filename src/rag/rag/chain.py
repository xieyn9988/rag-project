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
#from rag.vectorstore.factory import build_vector_store

from rag.retrieval.query_transform import QueryRewriter
from rag.retrieval.bm25_retriever import BM25Retriever
from rag.retrieval.rrf_fusion import rrf_fusion

from rag.vectorstore import build_vector_store


logger = get_logger(__name__)


@dataclass
class RAGResponse:
    """非流式响应"""

    question: str
    answer: str
    retrieved: List[Tuple[Document, float]]
    usage: dict | None = None   # ← 新增


@dataclass
class StreamChunk:
    """
    流式响应片段：
    - type='content' 时，text 是回答片段
    - type='references' 时，references 是引用列表
    """

    type: str  # 'content' | 'references'
    text: str = ""  # 内容片段
    references: List[dict] | None = None  # 引用列表


class RAGChain:
    def __init__(self, use_reranker: bool = True):
        self._embedder = build_embedder()
        #self._store = ChromaStore(
        #    str(settings.resolve(settings.chroma_dir)),
        #    settings.collection_name,
        #)
        self._store = build_vector_store()
        self._llm = build_llm()
        self._prompt = self._load_prompt()
        self._reranker: BgeReranker | None = None
        self._use_reranker = use_reranker
        self._store_count = self._store.count()  # ← 新增：记录当前 chunk 数

    def _ensure_store_fresh(self):
        """检查 collection 是否变了（count 对比），变了就重建 store。
        注意：这个函数处理"count 变化"（比如 ingest 加了文档），
        不处理"collection 不存在"—— 那是 _retrieve 里 try/except 兜底的。
        """
        try:
            current_count = self._store.count()
        except Exception as e:
            # store 异常（collection 不存在、磁盘问题等）
            #logger.warning("Store 异常 (%s)，重建 ChromaStore", e)    
            logger.warning("Store 异常 (%s)，触发工厂重建", e)         
            #self._store = ChromaStore(
            #    str(settings.resolve(settings.chroma_dir)),
            #    settings.collection_name,
            #)
            self._store = build_vector_store()
            self._store_count = self._store.count()
            return

        if current_count != self._store_count:
            logger.info(
                "Collection 变更 (%d → %d)，重建 store",
                self._store_count,
                current_count,
            )
            self._store = build_vector_store()
            #self._store = ChromaStore(                
                #str(settings.resolve(settings.chroma_dir)),
                #settings.collection_name,
            #)
            self._store_count = current_count

    @staticmethod
    def _load_prompt() -> dict:
        p = settings.project_root / "configs" / "prompts" / "rag_qa.yaml"
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    # ==================== 内部工具 ====================

    def _retrieve(self, question: str, top_k: int) -> List[Tuple[Document, float]]:
        """检索 + 重排序，返回 top_k 条 (doc, score)"""
        self._ensure_store_fresh()  # ← 每次检索前检查

         # 1. QueryRewrite（如果启用）
        from rag.config import settings
        if getattr(settings, "query_rewrite_enabled", False):
            logger.info("【v2】QueryRewrite 启用")          
            
            rewriter = QueryRewriter(self._llm)
            rewritten = rewriter.rewrite(question)
            logger.info("【v2】改写结果: %s", rewritten)
            # rewritten = [question] + 2 个变体
            queries = [question] + rewritten[:2]

            # 2. 对每个变体做"原始向量召回 + BM25 召回"
            all_docs = self._store.get_all_documents()
            bm25 = BM25Retriever(all_docs)

            all_dense = []
            all_sparse = []
            for q in queries:
                q_emb = self._embedder.embed_query(q)
                all_dense.extend(self._store.search(q_emb, top_k=top_k * 3))
                all_sparse.extend(bm25.search(q, top_k=top_k * 3))

            # 3. RRF 融合
            candidates = rrf_fusion([all_dense, all_sparse], top_k=top_k * 3)

            # 4. Reranker 精排
            if not self._use_reranker:
                return candidates[:top_k]
            if self._reranker is None:
                self._reranker = BgeReranker()
            rerank_query = rewritten[0] if rewritten else question
            logger.info("【v2】Reranker 用 query: %s", rerank_query)
            return self._reranker.rerank(rerank_query, candidates, top_k=top_k)

        # 旧逻辑（v1）
        q_emb = self._embedder.embed_query(question)

        try:
            candidates = self._store.search(q_emb, top_k=top_k * 3)
        except Exception as e:
            # collection 不存在或损坏 → 重建后重试一次
            logger.warning("检索失败 (%s)，重建 store 后重试", e)
            self._store = build_vector_store()
            #self._store = ChromaStore(
            #    str(settings.resolve(settings.chroma_dir)),
            #    settings.collection_name,
            #)
            self._store_count = self._store.count()
            candidates = self._store.search(q_emb, top_k=top_k * 3)

        if not self._use_reranker:
            return candidates[:top_k]

        if self._reranker is None:
            self._reranker = BgeReranker()        
        return self._reranker.rerank(question, candidates, top_k=top_k)

    def _build_messages(
        self, question: str, hits: List[Tuple[Document, float]]
    ) -> List[dict]:
        """把检索结果 + 问题组装成 LLM messages"""
        context = "\n\n".join(
            f"[文档 {i + 1} | 相似度 {score:.4f}]\n{doc.page_content}"
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
        answer, usage = self._llm.chat_with_usage(messages)   # ← 新方法
        return RAGResponse(question=question, answer=answer, retrieved=hits, usage=usage)

    def stream_query(
        self, question: str, top_k: int | None = None
    ) -> Iterator[StreamChunk]:
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
