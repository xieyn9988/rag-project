# apps/fastapi_app.py
"""启动 FastAPI 服务：uvicorn apps.fastapi_app:app --reload

或者直接：python apps/fastapi_app.py
"""
import os
# ⚠️ 必须在导入 rag 模块之前设置，否则 HuggingFace 模型仍会走官方源
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from rag.api.app import app  # noqa: F401

import logging
import uvicorn

from rag.api.app import app
from rag.api.service import get_chain

logger = logging.getLogger("warmup")

# 🆕 启动时预热 RAGChain（加载 BGE + Reranker）
# apps/fastapi_app.py
@app.on_event("startup")
def warmup():
    """启动时预热：加载 BGE + Reranker，避免首次请求冷启动。"""
    logger.info("warmup 开始...")
    try:
        from rag.api.service import get_chain
        chain = get_chain()
        # 触发一次假检索，让 reranker 也加载
        chain._retrieve("预热", top_k=1)
        logger.info("warmup 完成（含 reranker）")
    except Exception as e:
        logger.exception("warmup 失败: %s", e)


if __name__ == "__main__":
    uvicorn.run(
        "rag.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )