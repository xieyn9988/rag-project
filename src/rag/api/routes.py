# src/rag/api/routes.py
import json
import os
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from rag.api import service
from rag.api.schemas import (
    HealthResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    Reference,
    RetrievedDoc,
)
from rag.config import settings
from rag.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ==================== 系统 ====================

@router.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    """健康检查：返回服务状态和当前向量库条目数"""
    return HealthResponse(
        status="ok",
        doc_count=service.doc_count(),
        model_llm=settings.llm_model,
        model_embed=settings.embed_model,
    )


# ==================== 数据 ====================

@router.post("/ingest", response_model=IngestResponse, tags=["data"])
def ingest_endpoint(req: IngestRequest):
    """数据摄入：加载 data/ 下的 PDF/TXT，编码后写入 ChromaDB"""
    try:
        total = service.run_ingest(rebuild=req.rebuild)
        return IngestResponse(total=total)
    except Exception as e:
        logger.exception("ingest 失败")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== RAG 问答 ====================

@router.post("/query", response_model=QueryResponse, tags=["rag"])
def query_endpoint(req: QueryRequest):
    """RAG 问答（非流式）：检索 + 重排序 + LLM 生成"""
    start = time.time()

    try:
        resp = service.run_query(req.question, top_k=req.top_k)
    except Exception as e:
        logger.exception("query 失败")
        raise HTTPException(status_code=500, detail=str(e))

    elapsed_ms = int((time.time() - start) * 1000)

    # 完整检索结果（含正文，用于调试和前端展开）
    docs = [
        RetrievedDoc(
            content=d.page_content,
            score=float(s),
            source=d.metadata.get("source"),
            metadata=d.metadata,
        )
        for d, s in resp.retrieved
    ]

    # 精简引用（只含文件名 + 页码 + 得分，用于业务展示）
    references = [
        Reference(
            source=os.path.basename(d.metadata.get("source", "unknown")),
            page=d.metadata.get("page"),
            score=float(s),
        )
        for d, s in resp.retrieved
    ]

    logger.info(
        f"Query: '{req.question[:30]}' → {elapsed_ms}ms, "
        f"{len(references)} references"
    )

    return QueryResponse(
        question=resp.question,
        answer=resp.answer,
        retrieved=docs,
        references=references,
        elapsed_ms=elapsed_ms,
    )


@router.post("/query/stream", tags=["rag"])
def query_stream_endpoint(req: QueryRequest):
    """
    RAG 问答（流式）：SSE 协议，逐 token 返回内容 + 最后的引用列表。

    返回格式（SSE）：
        data: {"type": "content", "text": "亲~"}
        data: {"type": "content", "text": "关于退货..."}
        data: {"type": "references", "references": [{"source": "...", "score": 0.95}]}
        data: [DONE]
    """
    start = time.time()

    def event_generator():
        try:
            for chunk in service.stream_query(req.question, top_k=req.top_k):
                if chunk.type == "content":
                    payload = {"type": "content", "text": chunk.text}
                elif chunk.type == "references":
                    payload = {"type": "references", "references": chunk.references}
                else:
                    continue

                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            # 结束标记
            yield "data: [DONE]\n\n"

            elapsed_ms = int((time.time() - start) * 1000)
            logger.info(
                f"StreamQuery: '{req.question[:30]}' → {elapsed_ms}ms (完成)"
            )

        except Exception as e:
            logger.exception("stream query 失败")
            error_payload = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 告诉 Nginx 不要缓冲
            "Connection": "keep-alive",
        },
    )