# src/rag/api/schemas.py
from typing import List, Optional

from pydantic import BaseModel, Field


# ==================== 问答 ====================

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    top_k: int | None = Field(None, ge=1, le=20, description="检索文档数，默认用 settings.top_k")


class RetrievedDoc(BaseModel):
    """完整检索结果（含正文，用于调试/展开）"""
    content: str = Field(..., description="文档内容")
    score: float = Field(..., description="重排序分数，越大越相关")
    source: str | None = Field(None, description="文档来源")
    metadata: dict = Field(default_factory=dict)


class Reference(BaseModel):
    """精简引用（只含来源 + 页码 + 得分，用于业务展示）"""
    source: str = Field(..., description="文档来源（文件名）")
    page: Optional[int] = Field(None, description="页码（PDF 有）")
    score: Optional[float] = Field(None, description="相关性得分")


class QueryResponse(BaseModel):
    question: str
    answer: str
    retrieved: List[RetrievedDoc] = Field(default_factory=list, description="完整检索结果")
    references: List[Reference] = Field(default_factory=list, description="精简引用来源")
    elapsed_ms: int = Field(..., description="耗时（毫秒）")


# ==================== 摄入 ====================

class IngestRequest(BaseModel):
    rebuild: bool = Field(False, description="是否清空后重建")


class IngestResponse(BaseModel):
    total: int = Field(..., description="摄入后的文档总数")


# ==================== 系统 ====================

class HealthResponse(BaseModel):
    status: str
    doc_count: int
    model_llm: str
    model_embed: str