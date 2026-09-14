# src/rag/logging_config.py
import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """统一日志格式，替换项目中的 print"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # 降噪：这些库日志太多，压到 WARNING
    for noisy in ("httpx", "urllib3", "chromadb", "sentence_transformers"):
        logging.getLogger(noisy).setLevel("WARNING")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)