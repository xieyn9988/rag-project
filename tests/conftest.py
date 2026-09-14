# tests/conftest.py
import pytest

from rag.logging_config import setup_logging


@pytest.fixture(autouse=True)
def _log():
    setup_logging("WARNING")