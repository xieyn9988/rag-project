from pathlib import Path

from rag.config import settings


def test_settings_loaded():
    assert settings.llm_model == "deepseek-chat"
    assert settings.chunk_size == 500
    assert isinstance(settings.chroma_dir, Path)


def test_resolve_relative():
    p = settings.resolve(Path("storage/chroma_db"))
    assert p.is_absolute()
    assert p.name == "chroma_db"