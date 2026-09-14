# src/rag/api/routes.py
from fastapi import APIRouter, HTTPException

from rag.api import service
from rag.api.schemas import (
    HealthResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    RetrievedDoc,
)
from rag.config import settings
from rag.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    """健康检查：返回服务状态和当前向量库条目数"""
    return HealthResponse(
        status="ok",
        doc_count=service.doc_count(),
        model_llm=settings.llm_model,
        model_embed=settings.embed_model,
    )


@router.post("/ingest", response_model=IngestResponse, tags=["data"])
def ingest_endpoint(req: IngestRequest):
    """数据摄入：加载 data/ 下的 PDF/TXT，编码后写入 ChromaDB"""
    try:
        total = service.run_ingest(rebuild=req.rebuild)
        return IngestResponse(total=total)
    except Exception as e:
        logger.exception("ingest 失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryResponse, tags=["rag"])
def query_endpoint(req: QueryRequest):
    """RAG 问答：检索 + 重排序 + LLM 生成"""
    try:
        resp = service.run_query(req.question, top_k=req.top_k)
    except Exception as e:
        logger.exception("query 失败")
        raise HTTPException(status_code=500, detail=str(e))

    docs = [
        RetrievedDoc(
            content=d.page_content,
            score=float(s),
            source=d.metadata.get("source"),
            metadata=d.metadata,
        )
        for d, s in resp.retrieved
    ]
    return QueryResponse(question=resp.question, answer=resp.answer, retrieved=docs)