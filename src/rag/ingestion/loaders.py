# src/rag/ingestion/loaders.py
from pathlib import Path
from typing import List

from langchain_core.documents import Document

from rag.logging_config import get_logger

logger = get_logger(__name__)


def _load_pdf(file_path: Path) -> List[Document]:
    """加载 PDF（优先 langchain-docling，回退 PyPDFium2，最后 PyPDF）"""
    try:
        from langchain_docling import DoclingLoader

        return DoclingLoader(str(file_path)).load()
    except ImportError:
        logger.warning("langchain-docling 未安装，回退到 PyPDFium2")
    except Exception as e:
        logger.warning("Docling 加载失败 %s: %s，回退 PyPDFium2", file_path.name, e)

    try:
        from langchain_community.document_loaders import PyPDFium2Loader

        return PyPDFium2Loader(str(file_path)).load()
    except ImportError:
        logger.warning("PyPDFium2 未安装，回退到 PyPDF")

    from langchain_community.document_loaders import PyPDFLoader  # type: ignore

    return PyPDFLoader(str(file_path)).load()


def _load_text(file_path: Path) -> List[Document]:
    """加载 TXT（自己实现，不依赖 langchain-community）"""
    text = file_path.read_text(encoding="utf-8")
    return [Document(page_content=text, metadata={"source": str(file_path)})]


def load_documents(data_dir: Path) -> List[Document]:
    """加载 data_dir 下的 PDF 与 TXT 文件"""
    all_docs: List[Document] = []

    pdf_dir = data_dir / "pdfs"
    if pdf_dir.exists():
        for f in sorted(pdf_dir.glob("*.pdf")):
            try:
                docs = _load_pdf(f)
                all_docs.extend(docs)
                logger.info("已加载 PDF: %s (%d 页)", f.name, len(docs))
            except Exception as e:
                logger.exception("加载 PDF 失败 %s: %s", f.name, e)

    text_dir = data_dir / "text"
    if text_dir.exists():
        for f in sorted(text_dir.glob("*.txt")):
            try:
                docs = _load_text(f)
                all_docs.extend(docs)
                logger.info("已加载 TXT: %s", f.name)
            except Exception as e:
                logger.exception("加载 TXT 失败 %s: %s", f.name, e)

    logger.info("共加载 %d 个文档片段", len(all_docs))
    return all_docs