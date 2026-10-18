# src/rag/vectorstore/factory.py
from rag.config import settings
from rag.vectorstore.base import BaseVectorStore
from rag.vectorstore.chroma_store import ChromaStore
from rag.vectorstore.milvus_store import MilvusStore
from rag.logging_config import get_logger

logger = get_logger(__name__)

def build_vector_store() -> BaseVectorStore:
    """
    向量库工厂：根据配置动态实例化对应的 VectorStore。
    业务层（如 RAGChain）无需关心底层到底是 Chroma 还是 Milvus。
    """
    # 假设你在 config.py 中定义了 vector_store_type，默认 'chroma'
    store_type = getattr(settings, "vector_store_type", "chroma").lower()

    if store_type == "milvus":
        logger.info("工厂构建: 使用 Milvus 向量库 (URI: %s)", settings.milvus_uri)
        return MilvusStore(
            uri=settings.milvus_uri,
            collection_name=settings.collection_name,
            dim=512, # 这里的维度最好也从 settings 里读
        )
        
    elif store_type == "chroma":
        logger.info("工厂构建: 使用 ChromaDB 向量库 (Path: %s)", settings.chroma_dir)
        return ChromaStore(
            persist_dir=str(settings.resolve(settings.chroma_dir)),
            collection_name=settings.collection_name,
        )
        
    else:
        raise ValueError(f"不支持的向量库类型: {store_type}")