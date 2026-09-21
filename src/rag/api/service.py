# src/rag/api/service.py
import threading

from typing import Iterator, List, Optional

from rag.config import settings
from rag.ingestion.pipeline import ingest
from rag.logging_config import get_logger
from rag.rag import RAGChain, RAGResponse
from rag.rag.chain import StreamChunk

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

def ingest_uploaded_files(file_paths: List[str]) -> int:
    """
    保存上传的文件后执行摄入。
    
    :param file_paths: 已保存到磁盘的文件路径列表
    :return: 摄入后的文档块总数
    """
    # ingest 会自动扫描 data/ 目录，所以上传的文件应该先放到 data/ 下
    # 这里直接调用 run_ingest（rebuild=True 重建索引）
    return run_ingest(rebuild=True)



def run_query(question: str, top_k: int | None = None) -> RAGResponse:
    """执行非流式问答"""
    chain = get_chain()
    return chain.query(question, top_k=top_k)


def stream_query(question: str, top_k: int | None = None) -> Iterator[StreamChunk]:
    """
    执行流式问答：返回 Generator，逐条 yield StreamChunk
    
    用法（在 routes.py 里）：
        for chunk in service.stream_query(question, top_k=2):
            if chunk.type == "content":
                ...
            elif chunk.type == "references":
                ...
    """
    chain = get_chain()
    return chain.stream_query(question, top_k=top_k)


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