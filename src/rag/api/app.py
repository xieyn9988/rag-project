# src/rag/api/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag.api.routes import router
from rag.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

# ⚠️ 先创建 app 实例
app = FastAPI(
    title="电商客服 RAG 智能问答系统",
    description="基于 LangChain + ChromaDB + BGE + DeepSeek 的检索增强生成服务",
    version="1.0.0",
)

# ⚠️ 再添加中间件（此时 app 已存在）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⚠️ 最后注册路由
app.include_router(router)


@app.on_event("startup")
def _startup():
    logger.info("RAG API 启动完成")
    logger.info("API 文档：http://localhost:8000/docs")