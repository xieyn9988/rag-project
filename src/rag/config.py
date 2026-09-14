# src/rag/config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置，从 .env 和环境变量加载（前缀 RAG_）"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RAG_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 项目路径
    project_root: Path = Path(__file__).resolve().parents[2]

    # LLM
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1000

    # Embedding
    embed_model: str = "BAAI/bge-small-zh-v1.5"

    # 分块
    chunk_size: int = 500
    chunk_overlap: int = 50

    # 检索
    top_k: int = 3

    # 存储
    chroma_dir: Path = Path("storage/chroma_db")
    collection_name: str = "rag_docs"

    # 数据目录
    data_dir: Path = Path("data")

    def resolve(self, p: Path) -> Path:
        """把相对路径解析为项目根下的绝对路径"""
        return p if p.is_absolute() else (self.project_root / p)


settings = Settings()