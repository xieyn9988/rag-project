# src/rag/api/app.py
from fastapi import FastAPI

from rag.api.routes import router
from rag.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="RAG API",
    description="基于 LangChain + ChromaDB + BGE + DeepSeek 的检索增强生成服务",
    version="0.1.0",
)

app.include_router(router)


@app.on_event("startup")
def _startup():
    logger.info("RAG API 启动完成")