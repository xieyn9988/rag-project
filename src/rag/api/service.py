# src/rag/api/service.py
import threading
from typing import Optional

from rag.config import settings
from rag.ingestion.pipeline import ingest
from rag.logging_config import get_logger
from rag.rag import RAGChain, RAGResponse

logger = get_logger(__name__)

_chain: Optional[RAGChain] = None
_lock = threading.Lock()


def get_chain() -> RAGChain:
    """懒加载单例 RAGChain"""
    global _chain
    if _chain is None:
        with _lock:
            if _chain is None:
                logger.info("初始化 RAGChain（首次请求）")
                _chain = RAGChain()
    return _chain


def reset_chain() -> None:
    """强制下次请求重建 RAGChain（用于 ingest 后刷新 collection 句柄）"""
    global _chain
    with _lock:
        if _chain is not None:
            logger.info("重置 RAGChain 单例")
        _chain = None


def run_ingest(rebuild: bool = False) -> int:
    """执行数据摄入；ingest 后必须重置 chain"""
    try:
        total = ingest(rebuild=rebuild)
    finally:
        # 无论成功失败，都让下次 query 重建 chain
        reset_chain()
    return total


def run_query(question: str, top_k: int | None = None) -> RAGResponse:
    """执行问答"""
    chain = get_chain()
    return chain.query(question, top_k=top_k)


def doc_count() -> int:
    """当前向量库条目数（每次新建 store，避免缓存问题）"""
    try:
        from rag.vectorstore import ChromaStore

        store = ChromaStore(
            str(settings.resolve(settings.chroma_dir)),
            settings.collection_name,
        )
        return store.count()
    except Exception as e:
        logger.exception("查询 doc_count 失败: %s", e)
        return -1