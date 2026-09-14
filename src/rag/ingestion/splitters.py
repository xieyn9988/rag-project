# src/rag/ingestion/splitters.py
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.config import settings
from rag.logging_config import get_logger

logger = get_logger(__name__)


def split_documents(
    documents: List[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[Document]:
    """把文档切分为文本块"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.chunk_size,
        chunk_overlap=chunk_overlap or settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    logger.info("分割完成，共 %d 个文本块", len(chunks))
    return chunks