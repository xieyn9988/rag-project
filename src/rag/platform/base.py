# src/rag/platform/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict

from rag.platform.models import IncomingMessage, OutgoingMessage, ReplyResult


class PlatformAdapter(ABC):
    @property
    @abstractmethod
    def platform_name(self) -> str: ...

    @abstractmethod
    def verify_signature(self, raw_request: Dict[str, Any]) -> bool: ...

    @abstractmethod
    def parse_webhook(self, raw_request: Dict[str, Any]) -> IncomingMessage: ...

    @abstractmethod
    def send_reply(self, msg: OutgoingMessage) -> ReplyResult: ...

    def get_session_id(self, msg: IncomingMessage) -> str:
        return f"{msg.platform.value}:{msg.shop_id}:{msg.buyer_id}"