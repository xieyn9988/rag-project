# src/rag/vectorstore/milvus_store.py
from typing import List, Optional
import uuid

from pymilvus import (
    connections,
    utility,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
)
from langchain_core.documents import Document

from rag.logging_config import get_logger
from rag.vectorstore.base import BaseVectorStore

logger = get_logger(__name__)


class MilvusStore(BaseVectorStore):
    def __init__(
        self, 
        uri: str, 
        collection_name: str, 
        dim: int = 512, # BGE-small-zh-v1.5 的维度通常是 512
        hnsw_m: int = 30,
        hnsw_ef_construction: int = 360,
        hnsw_ef_search: int = 64
    ):
        self.collection_name = collection_name
        self.hnsw_ef_search = hnsw_ef_search
        
        # 1. 连接 Milvus
        connections.connect("default", uri=uri)
        
        # 2. 检查集合是否存在，不存在则创建 Schema
        if not utility.has_collection(collection_name):
            fields = [
                # 主键：让 Milvus 自动生成，或者我们用 UUID
                FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=1024),
                # 如果需要存更多 metadata，可以用 JSON 字段 (Milvus 2.4+ 支持)
            ]
            schema = CollectionSchema(fields, description="RAG Knowledge Base")
            self._collection = Collection(name=collection_name, schema=schema)
            logger.info("Milvus 集合 %s 创建成功", collection_name)
        else:
            self._collection = Collection(name=collection_name)
            logger.info("Milvus 集合 %s 已存在", collection_name)

        # 3. 建 HNSW 索引并加载
        if not self._collection.has_index():
            index_params = {
                "index_type": "HNSW",
                "metric_type": "COSINE",  # 对齐 Chroma 的 cosine
                "params": {
                    "M": hnsw_m,
                    "efConstruction": hnsw_ef_construction
                }
            }
            self._collection.create_index(field_name="vector", index_params=index_params)
            logger.info(f"Milvus HNSW 索引创建成功: M={hnsw_m}, efConstruction={hnsw_ef_construction}")
        
        self._collection.load()

    def add(self, documents: List[Document], embeddings: List[List[float]]) -> None:
        if not documents:
            return
        
        # 构造数据格式，对齐 pymilvus 的 insert
        pks = [str(uuid.uuid4()) for _ in documents]
        texts = [d.page_content for d in documents]
        sources = [d.metadata.get("source", "unknown") for d in documents]
        
        # 确保向量是 float 类型 (防止报错 required argument is not a float)
        vectors = [[float(x) for x in vec] for vec in embeddings]
        
        data = [pks, vectors, texts, sources]
        
        # 批量插入
        self._collection.insert(data)
        self._collection.flush() # 确保数据落盘，可以被立刻检索
        logger.info("写入/更新 %d 条", len(documents))

    def search(
        self, query_embedding: List[float], top_k: int, where: Optional[dict] = None
    ) -> List[tuple[Document, float]]:
        # 注意：这里暂不实现复杂的 where 过滤，如果有需要可以转成 Milvus 的 expr
        
        search_params = {
            "metric_type": "COSINE",
            "params": {"ef": self.hnsw_ef_search}
        }
        
        # 向量必须是 float
        query_vec = [[float(x) for x in query_embedding]]
        
        results = self._collection.search(
            data=query_vec,
            anns_field="vector",
            param=search_params,
            limit=top_k,
            output_fields=["text", "source"] # 需要返回的字段
        )
        
        out = []
        for hits in results:
            for hit in hits:
                # Milvus 的 COSINE 距离范围是 [-1, 1] (实际上通常大于0)，
                # LangChain/Chroma 的 cosine 距离是 1 - similarity
                # 所以 Milvus 的 distance 其实就代表了某种距离，如果 metric 是 COSINE，距离越小越相似。
                # 为了和 Chroma (1.0 - dist) 保持一致，相似度我们直接用 1 - 距离
                # (注：pymilvus 返回的 COSINE 距离实际上就是 1 - cosine_similarity)
                similarity = 1.0 - hit.distance
                
                doc = Document(
                    page_content=hit.entity.get("text"),
                    metadata={"source": hit.entity.get("source")}
                )
                out.append((doc, similarity))
        return out

    def delete_by_source(self, source: str) -> int:
        # 先查一下有多少条
        expr = f'source == "{source}"'
        try:
            res = self._collection.query(expr=expr, output_fields=["pk"])
            count = len(res)
            if count > 0:
                self._collection.delete(expr=expr)
                self._collection.flush()
                logger.info(f"已删除 source={source} 的 {count} 条数据")
            return count
        except Exception as e:
            logger.error(f"删除失败: {e}")
            return 0

    def count(self) -> int:
        # 由于 Milvus 的 num_entities 可能会因为未 flush 而不准
        # 可以 flush 后再取，或者直接通过 query 计数
        self._collection.flush()
        return self._collection.num_entities

    def reset(self) -> None:
        utility.drop_collection(self.collection_name)
        logger.warning("集合 %s 已重置", self.collection_name)
        
        # 重新初始化
        fields = [
            FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=512),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=1024),
        ]
        schema = CollectionSchema(fields, description="RAG Knowledge Base")
        self._collection = Collection(name=self.collection_name, schema=schema)
        
        index_params = {
            "index_type": "HNSW",
            "metric_type": "COSINE",
            "params": {"M": 30, "efConstruction": 360}
        }
        self._collection.create_index(field_name="vector", index_params=index_params)
        self._collection.load()

    def get_all_documents(self) -> list:
        """获取所有文档（用于 BM25 索引）。"""
        self._collection.flush()
        # 查询所有数据
        res = self._collection.query(
            expr="pk != ''", # 绕过必须写 expr 的限制
            output_fields=["text", "source"],
            limit=16384 # 假设你的数据量不会超过这个数
        )
        docs = []
        for item in res:
            docs.append(Document(
                page_content=item.get("text"),
                metadata={"source": item.get("source", "")}
            ))
        return docs