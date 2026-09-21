# src/rag/api/routes.py
import json
import os
import shutil
import time
from pathlib import Path
from typing import List          # ⚠️ 关键：加这一行，否则 List 会报 NameError

from fastapi import APIRouter, File, HTTPException, UploadFile
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
    UploadResponse,
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


# ==================== 上传资料 ====================

@router.post("/ingest/upload", response_model=UploadResponse, tags=["data"])
async def ingest_upload_endpoint(files: List[UploadFile] = File(...)):
    """
    上传资料：接收 TXT / MD / PDF，保存到 data/ 目录，然后重建索引。
    """
    start = time.time()
    data_dir = settings.resolve(settings.data_dir)

    uploaded_names: List[str] = []
    skipped_names: List[str] = []

    for file in files:
        suffix = Path(file.filename).suffix.lower()

        if suffix == ".pdf":
            target_dir = data_dir / "pdfs"
        elif suffix in (".txt", ".md"):
            target_dir = data_dir / "text"
        else:
            skipped_names.append(file.filename)
            continue

        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / file.filename

        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        uploaded_names.append(file.filename)
        logger.info(f"上传文件: {file.filename} → {target_path}")

    try:
        total = service.ingest_uploaded_files([])
    except Exception as e:
        logger.exception("上传后摄入失败")
        raise HTTPException(status_code=500, detail=f"摄入失败: {str(e)}")

    elapsed_ms = int((time.time() - start) * 1000)
    logger.info(
        f"上传完成: {len(uploaded_names)} 个文件, "
        f"共 {total} 个文本块, {elapsed_ms}ms"
    )

    return UploadResponse(
        total=total,
        uploaded=uploaded_names,
        skipped=skipped_names,
        elapsed_ms=elapsed_ms,
    )