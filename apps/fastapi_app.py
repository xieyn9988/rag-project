# apps/fastapi_app.py
"""启动 FastAPI 服务：uvicorn apps.fastapi_app:app --reload

或者直接：python apps/fastapi_app.py
"""
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