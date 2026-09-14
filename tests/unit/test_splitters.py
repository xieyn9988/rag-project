from langchain_core.documents import Document

from rag.ingestion.splitters import split_documents


def test_split_basic():
    docs = [Document(page_content="A" * 1200, metadata={"source": "x"})]
    chunks = split_documents(docs, chunk_size=500, chunk_overlap=50)
    assert len(chunks) >= 2
    assert all(len(c.page_content) <= 500 for c in chunks)