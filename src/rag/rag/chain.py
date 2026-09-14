# src/rag/rag/chain.py
from dataclasses import dataclass
from typing import List

import yaml

from rag.config import settings
from rag.embedding import build_embedder
from rag.llm import build_llm
from rag.logging_config import get_logger
from rag.retrieval import BgeReranker
from rag.vectorstore import ChromaStore

logger = get_logger(__name__)


@dataclass
class RAGResponse:
    question: str
    answer: str
    retrieved: List[tuple]


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

    def query(self, question: str, top_k: int | None = None) -> RAGResponse:
        top_k = top_k or settings.top_k
        q_emb = self._embedder.embed_query(question)

        candidates = self._store.search(q_emb, top_k=top_k * 3)

        if self._reranker is None:
            self._reranker = BgeReranker()
        hits = self._reranker.rerank(question, candidates, top_k=top_k)

        context = "\n\n".join(
            f"[文档 {i+1} | 相似度 {score:.4f}]\n{doc.page_content}"
            for i, (doc, score) in enumerate(hits)
        )

        user_msg = self._prompt["user_template"].format(
            context=context, question=question
        )
        answer = self._llm.chat([
            {"role": "system", "content": self._prompt["system"]},
            {"role": "user", "content": user_msg},
        ])
        return RAGResponse(question=question, answer=answer, retrieved=hits)