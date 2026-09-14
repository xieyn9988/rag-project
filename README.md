# RAG 智能问答系统

基于 **LangChain + ChromaDB + BGE + DeepSeek** 构建的检索增强生成（RAG）系统，支持文档上传、向量检索、重排序、LLM 生成，提供 CLI / Gradio / FastAPI 三种接口，可 Docker 一键部署。

## ✨ 功能特性

- 📄 **多格式文档摄入**：PDF / TXT / Markdown
- 🔍 **中文语义检索**：BGE-small-zh-v1.5 embedding + ChromaDB 向量库
- 🎯 **BGE Reranker 精排**：CrossEncoder 重排序，检索精度显著提升
- 🤖 **DeepSeek LLM 生成**：基于检索内容生成准确回答，避免幻觉
- 💬 **多入口**：CLI 命令行 / Gradio Web 界面 / FastAPI REST 接口
- 🐳 **Docker 一键部署**：`docker compose up -d` 启动
- 🧪 **单元测试 + 全链路自检**：`pytest` + `scripts/check_all.py`

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────┐
│  Interface Layer   CLI / Gradio / FastAPI           │
├─────────────────────────────────────────────────────┤
│  Service Layer     RAGService（单例管理）            │
├─────────────────────────────────────────────────────┤
│  RAG Chain         Retrieve → Rerank → Prompt → LLM │
├──────────────┬──────────────┬───────────────────────┤
│  Embedding   │  VectorStore │  LLM                  │
│  (BGE-zh)    │  (ChromaDB)  │  (DeepSeek)           │
├──────────────┴──────────────┴───────────────────────┤
│  Ingestion Pipeline  Load → Split → Embed → Store   │
├─────────────────────────────────────────────────────┤
│  Config (Pydantic) + Logging                        │
└─────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
rag-project/
├── src/rag/                    # 核心代码
│   ├── config.py               # 配置（Pydantic Settings）
│   ├── logging_config.py       # 统一日志
│   ├── ingestion/              # 文档加载与分割
│   ├── embedding/              # BGE 中文 embedding
│   ├── vectorstore/            # ChromaDB 封装
│   ├── retrieval/              # BGE Reranker
│   ├── llm/                    # DeepSeek 封装
│   ├── rag/                    # RAG 编排
│   └── api/                    # FastAPI 服务
├── apps/                       # 应用入口
│   ├── cli.py                  # 命令行
│   ├── gradio_app.py           # Web 界面
│   └── fastapi_app.py          # API 服务
├── scripts/                    # 运维脚本
│   ├── ingest.py               # 数据摄入
│   ├── smoke_api.py            # API 冒烟测试
│   └── check_all.py            # 全链路自检
├── configs/prompts/            # Prompt 模板
├── tests/                      # 单元测试
├── Dockerfile                  # Docker 镜像
└── docker-compose.yml          # 服务编排
```

## 🚀 快速开始

### 前置条件

- Python 3.10+
- （可选）Docker Desktop

### 本地开发

```bash
# 1. 克隆
git clone https://github.com/xieyn9988/rag-project.git
cd rag-project

# 2. 创建虚拟环境
conda create -n chroma_env python=3.10 -y
conda activate chroma_env

# 3. 安装依赖
pip install -e ".[dev]"

# 4. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
# 获取地址：https://platform.deepseek.com/api_keys

# 5. 把资料放进 data/text/ 或 data/pdfs/
# 6. 摄入数据
python scripts/ingest.py --rebuild

# 7. 启动 Web 界面
python apps/gradio_app.py
# 浏览器打开 http://localhost:7860
```

### Docker 部署

```bash
# 1. 配置 .env
cp .env.example .env

# 2. 启动
docker compose up -d

# 3. 访问
# API 文档：http://localhost:8000/docs
# Web 界面：http://localhost:7860
```

## 📖 使用说明

### CLI 问答

```bash
python apps/cli.py -q "什么是 RAG？" --show-refs
```

### Web 界面

浏览器打开 `http://localhost:7860`，支持：
- `💬 问答`：输入问题，获得回答和引用
- `📤 上传资料`：上传 TXT/MD/PDF，自动解析并重建索引

### REST API

```bash
# 健康检查
curl http://localhost:8000/health

# 问答
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是 RAG？", "top_k": 3}'

# 摄入数据
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"rebuild": true}'
```

## ⚙️ 配置

所有配置通过 `.env` 文件或环境变量（前缀 `RAG_`）管理：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RAG_LLM_API_KEY` | - | DeepSeek API Key |
| `RAG_LLM_BASE_URL` | `https://api.deepseek.com/v1` | LLM 服务地址 |
| `RAG_LLM_MODEL` | `deepseek-chat` | 模型名 |
| `RAG_EMBED_MODEL` | `BAAI/bge-small-zh-v1.5` | Embedding 模型 |
| `RAG_CHUNK_SIZE` | `500` | 文本块大小 |
| `RAG_TOP_K` | `3` | 检索文档数 |

## 🧪 测试

```bash
# 单元测试
pytest tests/unit -v

# 全链路自检
python scripts/check_all.py

# API 冒烟测试
python scripts/smoke_api.py
```

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| RAG 框架 | LangChain |
| 向量数据库 | ChromaDB |
| Embedding | BAAI/bge-small-zh-v1.5 |
| Reranker | BAAI/bge-reranker-base |
| LLM | DeepSeek Chat |
| Web 界面 | Gradio |
| API | FastAPI + Uvicorn |
| 配置 | Pydantic Settings |
| 测试 | pytest |
| 部署 | Docker + Docker Compose |

## 📝 设计要点

- **分层架构**：interface / service / chain / infra 四层分离
- **抽象接口**：Embedder / VectorStore / LLM 三个 ABC，方便换供应商
- **配置外置**：`.env` + Pydantic Settings，敏感信息不进代码
- **单例管理**：RAGChain 全局复用，避免每次请求重载模型
- **重排序**：向量召回 `top_k × 3`，CrossEncoder 精排取 `top_k`
- **一致性**：ingest 后自动重置 chain，避免 collection 句柄失效

## 📄 License

MIT

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain)
- [ChromaDB](https://github.com/chroma-core/chroma)
- [BAAI BGE](https://github.com/FlagOpen/FlagEmbedding)
- [DeepSeek](https://www.deepseek.com/)
