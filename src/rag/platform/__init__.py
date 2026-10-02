# src/rag/platform/__init__.py
from rag.platform.base import PlatformAdapter
from rag.platform.mock_adapter import MockAdapter
from rag.platform.models import (
    IncomingMessage, OutgoingMessage, Platform, ReplyResult,
)


def build_adapter(platform: str = "mock", **kwargs) -> PlatformAdapter:
    if platform == "mock":
        return MockAdapter(**kwargs)
    raise ValueError(f"未知平台: {platform}")


__all__ = [
    "PlatformAdapter", "MockAdapter",
    "IncomingMessage", "OutgoingMessage", "Platform", "ReplyResult",
    "build_adapter",
]