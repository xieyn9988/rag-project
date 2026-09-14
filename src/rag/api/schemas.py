# src/rag/api/schemas.py
from typing import List

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    top_k: int | None = Field(None, ge=1, le=20, description="检索文档数，默认用 settings.top_k")


class RetrievedDoc(BaseModel):
    content: str = Field(..., description="文档内容")
    score: float = Field(..., description="重排序分数，越大越相关")
    source: str | None = Field(None, description="文档来源")
    metadata: dict = Field(default_factory=dict)


class QueryResponse(BaseModel):
    question: str
    answer: str
    retrieved: List[RetrievedDoc]


class IngestRequest(BaseModel):
    rebuild: bool = Field(False, description="是否清空后重建")


class IngestResponse(BaseModel):
    total: int = Field(..., description="摄入后的文档总数")


class HealthResponse(BaseModel):
    status: str
    doc_count: int
    model_llm: str
    model_embed: str