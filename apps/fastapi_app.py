# apps/fastapi_app.py
"""启动 FastAPI 服务：uvicorn apps.fastapi_app:app --reload

或者直接：python apps/fastapi_app.py
"""
import os

import uvicorn
from rag.api.app import app  # noqa: F401

# ⚠️ 必须在导入 rag 模块之前设置，否则 HuggingFace 模型仍会走官方源
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import uvicorn

from rag.api.app import app  # noqa: F401  让 uvicorn 能找到 app

if __name__ == "__main__":
    uvicorn.run(
        "rag.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )



# 🆕 启动时预热 RAGChain（加载 BGE + Reranker）
@app.on_event("startup")
def warmup():
    import logging
    logger = logging.getLogger("warmup")
    logger.info("预热 RAGChain（加载 BGE + Reranker）...")
    try:
        from rag.api.service import get_chain
        get_chain()
        logger.info("预热完成")
    except Exception as e:
        logger.exception("预热失败: %s", e)


if __name__ == "__main__":
    uvicorn.run(
        "rag.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )