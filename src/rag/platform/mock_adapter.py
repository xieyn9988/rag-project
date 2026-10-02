# src/rag/platform/mock_adapter.py
import time
import uuid
from typing import Any, Dict

from rag.logging_config import get_logger
from rag.platform.base import PlatformAdapter
from rag.platform.models import (
    IncomingMessage, OutgoingMessage, Platform, ReplyResult,
)

logger = get_logger(__name__)


class MockAdapter(PlatformAdapter):
    def __init__(self, shop_id: str = "mock_shop_001"):
        self._shop_id = shop_id
        self._sent_replies: list = []

    @property
    def platform_name(self) -> str:
        return "mock"

    def verify_signature(self, raw_request: Dict[str, Any]) -> bool:
        return True

    def parse_webhook(self, raw_request: Dict[str, Any]) -> IncomingMessage:
        buyer_id = raw_request.get("buyer_id", "anonymous")
        return IncomingMessage(
            platform=Platform.MOCK,
            shop_id=self._shop_id,
            buyer_id=buyer_id,
            session_id=raw_request.get("session_id", f"mock:{buyer_id}"),
            msg_id=raw_request.get("msg_id", str(uuid.uuid4())),
            content=raw_request.get("content", ""),
            timestamp=int(time.time() * 1000),
            raw=raw_request,
        )

    def send_reply(self, msg: OutgoingMessage) -> ReplyResult:
        logger.info("[MOCK 回复] session=%s\n%s", msg.session_id, msg.content[:200])
        self._sent_replies.append(msg)
        return ReplyResult(success=True, platform_msg_id=str(uuid.uuid4()))

    @property
    def sent_replies(self):
        return self._sent_replies