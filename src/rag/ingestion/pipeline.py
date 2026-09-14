# src/rag/ingestion/pipeline.py
from pathlib import Path

from rag.config import settings
from rag.embedding import build_embedder
from rag.ingestion.loaders import load_documents
from rag.ingestion.splitters import split_documents
from rag.logging_config import get_logger
from rag.vectorstore import ChromaStore

logger = get_logger(__name__)


def ingest(data_dir: Path | None = None, rebuild: bool = False) -> int:
    """完整摄入流程：加载 → 分割 → 编码 → 写入"""
    data_dir = data_dir or settings.resolve(settings.data_dir)

    embedder = build_embedder()
    store = ChromaStore(
        persist_dir=str(settings.resolve(settings.chroma_dir)),
        collection_name=settings.collection_name,
    )

    if rebuild:
        logger.warning("rebuild=True，清空现有集合")
        store.reset()

    docs = load_documents(data_dir)
    if not docs:
        logger.warning("未找到任何文档，退出")
        return 0

    chunks = split_documents(docs)
    texts = [c.page_content for c in chunks]
    embeddings = embedder.embed_documents(texts)
    store.add(chunks, embeddings)

    logger.info("摄入完成，总计 %d 条", store.count())
    return store.count()