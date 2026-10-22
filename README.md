# 电商客服 RAG 智能问答系统
在线体验 Demo：http://81.68.194.67
(注：部署于 2核2G 个人测试服务器，首次访问或长时间无访问后，模型加载可能需要等待 10-15 秒，请耐心稍候。点击右上角可切换“业务客服”与“知识维护”视角体验。)

> 基于 **LangChain + ChromaDB + BGE + DeepSeek** 的电商客服 RAG 系统（v1，全栈已跑通）。
>
> 📌 **版本说明**
> - `v1.0`（main 分支 / tag v1.0）：业务原型版本；Vue3+FastAPI 全栈、SSE 流式输出、文档上传现传现用、反馈归因闭环、Reranker 精排、ChromaDB 向量库、公有 LLM API；完整延迟 & 检索评测。
> - `v2.0(WIP)`（feature/v2-enterprise-enhance 分支）：**「检索增强 + 领域微调」双引擎升级**【开发中】
>   - **M2 领域微调（新增核心）**：Qwen2.5 + LoRA/QLoRA/全参三路对比，治理灾难性遗忘，vLLM 部署替换公有 API
>   - **M1 检索增强**：BM25+向量 RRF 混合检索、HyDE、QueryRewrite——修复 `我下单后多久能收到？` 字面匹配 Badcase
>   - **M3 评估升级**：RAGAS 四指标自动化 + 微调双轨评测（量化「领域提升 / 通用保持」）
>   - **M4 向量库**：Milvus 适配器（基于 VectorStore 抽象基类）+ HNSW 调优
>
> **v1**：Vue3 全栈前端 + FastAPI + Streaming 流式输出 + 上传资料（现传现用）+ 业务闭环（反馈归因），Docker 一键部署。

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal) ![Vue3](https://img.shields.io/badge/Vue3-3.x-green) ![LangChain](https://img.shields.io/badge/LangChain-1.x-orange) ![ChromaDB](https://img.shields.io/badge/ChromaDB-1.x-yellow) ![Milvus](https://img.shields.io/badge/Milvus-v2_adapter-lightblue) ![LLaMA--Factory](https://img.shields.io/badge/LLaMA--Factory-Qwen2.5_LoRA-red) ![Docker](https://img.shields.io/badge/Docker-ready-blue)

---

## 💡 项目背景

**痛点**：电商客服每天重复回答大量问题：

- "这个商品支持 7 天无理由退货吗？"
- "快递到不了了，怎么申请补发？"
- "满减活动什么时候结束？"

**传统方案**：客服翻文档、查政策、复述给用户，平均响应 2-3 分钟。

**本项目**：把商品信息、售后政策、物流规则导入知识库，客服输入问题，系统自动检索并生成带**引用来源**的回答。

---

## 📊 项目亮点

> **性能数据**：非流式 P50 4.844s / 流式 TTFT P50 4.196s
> **检索质量**：30 条评测集，Hit@1 = 0.967
> **优化案例**：warm-up 预热 reranker，首次请求 14.77s → 3.5s

- **⚡ Streaming 流式输出**：SSE 协议逐 token 推送，用户看到打字机效果
- **📤 上传资料（现传现用）**：上传新政策 → 系统自动 ingest → 客服立即能问
- **🎯 Reranker 精排 + 引用追溯**：向量召回 + CrossEncoder 精排，附原文片段
- **🔄 业务闭环**：反馈采集 → Badcase 归因 → 知识缺口报告 → 知识迭代
- **🔌 平台适配层**：抽象 `PlatformAdapter`，支持 Webhook 接入京麦/千牛/抖店
- **🖥 全栈实现**：Vue3 + FastAPI + CLI，Docker 一键部署

> 🚧 **v2.0(WIP) 双引擎升级**【feature/v2-enterprise-enhance 分支】
> - **领域微调（新增核心）**：Qwen2.5-1.5B + LoRA/QLoRA/全参三路对比；通用数据 replay 治灾难性遗忘；merge → vLLM 部署替换公有 API
> - **检索增强**：BM25 + 向量 RRF 混合检索、HyDE、QueryRewrite——修复「下单后多久收到」字面重叠 Badcase
> - **评估升级**：RAGAS 四指标自动化（忠实度/相关性/幻觉）+ 微调双轨评测，量化「+X% 领域 / -Y% 通用」
> - **向量库**：Milvus 适配器 + HNSW 参数调优，对齐生产级选型

---

## 📊 性能与评测

### 测试环境

| 项 | 值 |
|---|---|
| CPU | Intel i7-8700，主频 3.20GHz，6 核 12 线程 |
| 内存 | 16GB |
| GPU | NVIDIA GTX 1050 Ti，显存 4GB（**测试时未启用**，BGE 跑 CPU） |
| OS | Windows 10 |
| Python | 3.10.x |
| 测试时间 | 2026-10-14 |
| 网络 | localhost（避免公网波动） |

### 延迟（90 次实测，top_k=2）

| 接口 | P50 | P95 | P99 / Max |
|---|---|---|---|
| 非流式 `/query` | 4.844s | 5.249s | 5.463s |
| 流式 `/query/stream` TTFT | **4.196s** | 4.511s | 4.835s |
| 流式 `/query/stream` Total | 4.822s | 5.414s | 5.770s |

**测量方法**：客户端 `requests` + `time.perf_counter()`，`N_RUNS=30`，3 个问题共 90 次。报 P50/P95/P99。

### 参数调优：top_k 消融实验

| top_k | 非流式 P50 | 流式 TTFT P50 | 边际成本 |
|---|---|---|---|
| 1 | 4.532s | 3.564s | - |
| **2（默认）** | **4.844s** | **4.196s** | +0.63s |
| 3 | 5.849s | 5.483s | +1.29s |

**结论**：top_k 从 1→2 涨 0.63s，从 2→3 涨 1.29s。**边际成本在 2 之后翻倍**，所以默认选 2。

### 延迟拆解

| 阶段 | 耗时 | 说明 |
|---|---|---|
| 检索（embedding + 向量） | ~50ms | 本地 |
| Reranker（CrossEncoder） | ~200ms | 本地 |
| 组装 messages | ~1ms | 本地 |
| **DeepSeek 首 token** | **~3.3s** | **瓶颈** |

**瓶颈在 DeepSeek 首 token 延迟**，非本地代码。

### 已知优化

- ✅ **warm-up 预热 reranker**：首次请求（含模型加载） **14.77s → 3.5s**（-76%）
- ✅ **真流式实现**：`stream=True` + 逐 chunk yield，非"全生成再推"
- ✅ **`X-Accel-Buffering: no`**：防 Nginx 缓冲，保证 SSE 真流式

### 可观测性说明

DeepSeek 侧偶发排队会导致长尾波动——同一配置下，P99 在 5.5s（正常轮）到 14s（抖动轮）之间。生产环境需加超时 + 重试 + 降级模板。

### 检索准确率（30 条人工标注评测集）

**评测集**：30 条，覆盖退货/物流/活动/售后/使用/综合/边界 7 个场景。每条人工标注"答案必须出现的关键词"。

#### 知识库补全前后对比

| 阶段 | 知识库条数 | 无 Reranker Hit@1 | 有 Reranker Hit@1 | 数据来源 |
|---|---|---|---|---|
| 补前 | 10 条 | 0.700 | 0.767 | ⚠️ 手写，JSON 未归档 |
| **补后** | **23 条** | **0.933** | **0.967** | ✅ `archive/2026-10-14_23chunks.json` |
| 提升 | - | **+23.3pp** | **+20pp** | - |

**关键发现**：

- **知识库补全是最大杠杆**（+20pp）——比 Reranker 贡献大 6 倍
- **Reranker 在知识库补全后仍有 +3.3pp**——不是冗余，是"排序修正"
- **Hit@3/Hit@5 = 1.0**——所有题的正确答案都能召回，只是排序不同

#### Reranker A/B 对比（知识库 23 条）

| 指标 | 无 Reranker | 有 Reranker | 提升 |
|---|---|---|---|
| Hit@1 | 0.933 | **0.967** | +3.3pp |
| Hit@3 | 1.000 | 1.000 | - |
| Hit@5 | 1.000 | 1.000 | - |
| MRR | 0.967 | **0.983** | +1.7pp |

**结论**：Reranker 提升的是 **Hit@1 和 MRR**——它把正确的 chunk 从第 2/3 名提到第 1 名。**客服场景里，Hit@1 比 Hit@5 重要**——因为 LLM 只读 top_2。

#### 评测集迭代记录

| 版本 | 条数 | Hit@1 | 迭代原因 | 关键发现 |
|---|---|---|---|---|
| v1 | 10 | 1.0 | 题太简单（关键词直接匹配） | 测不出真实水平 |
| v2 | 30 | 0.900 | 扩到 30 条，加难 case | 3 条错 case，其中 2 条是关键词未覆盖 |
| **v3** | **30** | **0.967** | **修正关键词覆盖** | **只剩 1 条真 RAG 边界** |

#### 唯一错 case 分析

**问题**：`我下单后多久能收到？`

![Reranker 失败 case](./docs/screenshots/reranker_failure_case.png)

**Reranker 后的 top 3**：

| 排名 | chunk | 相关 | 说明 |
|---|---|---|---|
| **[1]** | **"防伪" chunk** | **❌** | 含"现在下单包邮"，与"下单"字面重叠 |
| [2] | "发货时间" chunk | ✅ | 16:30 前/后，当天/次日发货 |
| [3] | "物流时效" chunk | ✅ | 中通 2-5 天 |

**根因**：Reranker 过度关注"下单"字面重叠，忽略了"多久"这个核心意图。

**这是 Reranker 的"字面偏好"** —— 它能纠正语义相似，但对"字面重叠强、语义弱"的 case 会误判。

**改进路径**：

1. **Query Rewriting**：把"多久"改写为"多长时间/发货时间" —— 让 Reranker 更容易匹配
2. **Chunk 去噪**：删掉 CTA 类内容（"现在下单包邮"）—— 减少噪声
3. **Reranker 升级**：从 base 换到 large —— 语义理解更强

### 成本

**数据来源**：25 次真实调用，从 `resp.usage` 读 token 数。

| 项 | 值 |
|---|---|
| 平均 input tokens | 596.8 |
| 平均 output tokens | 71.6 |
| **单次成本** | **¥0.00074** |
| **日均 500 次** | **¥0.37** |
| **月成本（22 天）** | **¥8.14** |

**对比人力**：

- 客服月薪 ¥6000，日均 500 问 → **单次人力成本 ¥0.55**
- AI 单次成本 ¥0.00074 → **降低 99.86%**

**说明**：

- DeepSeek 定价：¥1/百万 input tokens，¥2/百万 output tokens（2026-10）
- `input_tokens` 随检索文档长度变化（578-676），`output_tokens` 随回答长度变化（36-120）

### 可复现

~~~bash
# 延迟测试
python scripts/benchmark_latency.py
# 结果保存到 benchmarks/results/latency.json

# 检索准确率测试
python scripts/benchmark_retrieval.py
python scripts/benchmark_retrieval.py --no-reranker
# 结果保存到 benchmarks/results/retrieval_*.json

# 成本
python scripts/benchmark_cost.py
# 结果保存到 benchmarks/results/cost.json
~~~

---

## 🧪 v2.0：检索增强 + 领域微调双引擎【WIP】

> **定位**：从"RAG 应用"升级为"RAG + LoRA 微调"双引擎客服系统——**RAG 补时效知识，LoRA 内化话术与业务规则，评估闭环驱动持续迭代**。
>
> ✅ **进度**：M1 混合检索已合入 · 🔄 M2 数据构建中 · 📋 M3/M4 待启动（请按实际更新）
>
> 实验脚本位于 `scripts/benchmark_v2*.py` 与 `scripts/finetune/`，实验报告输出到 `docs/v2/`。


### M1 检索增强（修复 v1 已知 Badcase）

- **BM25 关键词检索 + RRF 倒数排序融合**：关键词与语义双路召回互补，修复「我下单后多久能收到」字面重叠误召回
- **HyDE 虚拟文档 / QueryRewrite 口语化改写**：消融实验验证对 Hit@1 的贡献
- **上下文注入策略**：片段去重（相似度 >0.9）、按相关性降序摆放应对 lost-in-the-middle、超长截断策略——可配置 + 消融
- **Prompt 模板工程**：`prompts/` 目录模板版本化；意图分类前置层（factual / meta / complaint / chitchat），不同意图走不同 Prompt——兑现 v1「元问题案例」的改进方向

### M2 领域微调（LLaMA-Factory + Qwen2.5-1.5B）

- **框架**：LLaMA-Factory 0.8.2 + Qwen2.5-0.5B + QLoRA
- **训练数据**：950 条（v1 知识库"扩法 1+3"生成）
- **训练环境**：AutoDL RTX 4090D（¥1.88/时）
- **训练时长**：10 分 41 秒 / **成本 ¥0.35**
- **loss 曲线**：3.9 → 0.9（收敛无过拟合）
- **LoRA 权重**：34MB / 可训练参数 8.8M（1.75%）
- **微调效果**：客服话术 100% 化（`亲~...哦~`）
- **报告**：[docs/v2/finetune_report.md](docs/v2/finetune_report.md)

### M3 评估体系（RAGAS + 双轨评测）

- **RAGAS 自动化**：Faithfulness / Answer Relevancy / Context Precision / Context Recall，跑 30 条评测集，与人工标注 Hit@1 交叉验证
- **微调双轨评测**：
  - **领域集**：自建 100 条客服测试题（含 held-out 知识点）——测能力提升
  - **通用集**：CEval / MMLU 轻量子集 50 条——量化遗忘程度
  - 产出：**「领域 +X% / 通用 -Y%」** 的量化结论

### 📊 M4：向量库切换与 HNSW 参数调优

为了验证架构的扩展性与生产级索引控制能力，M4 阶段引入了 Milvus（Standalone）并针对其底层的 HNSW 索引进行了参数消融实验。

#### 1. 核心结论
- **架构解耦**：通过 `BaseVectorStore` 抽象基类与工厂模式（`build_vector_store()`），实现了业务核心层（`RAGChain`）与底层向量库的**零代码绑定切换**。只需修改 `.env` 配置文件，即可在 ChromaDB 与 Milvus 之间丝滑切换，无需改动任何业务逻辑。
- **HNSW 参数敏感性**：在 33 条极小规模数据集下进行消融实验发现，**HNSW 并非参数越高越好**。
  - **高召回组（M=64）**：由于图过度稠密，在结合 BM25 混合检索时，引入了大量“字面重叠但语义弱”的噪声节点，导致 Reranker 精排被干扰，Hit@1 反降至 0.86。
  - **低延迟组（M=16）**：由于图的连通性不足，部分语义相似文档被漏召回，Hit@1 降至 0.88。
- **最佳实践**：**默认组（M=30, efConstruction=360, ef=64）取得了 Hit@1 = 0.98 的最佳成绩**，表现甚至略优于原有 ChromaDB 的 0.967。这证明了在生产环境中，必须根据具体的数据规模和业务分布，对 HNSW 进行针对性调参，拒绝“拍脑袋”配置。

#### 2. HNSW 参数消融实验数据

| 实验分组 | HNSW 参数 (M / efC / ef) | Hit@1 | Hit@3 | MRR | 业务含义 / 架构分析 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 高召回组 | `64 / 500 / 128` | 0.86 | 1.0 | 0.93 | 图过度稠密，引入字面噪声干扰精排，召回率反降。 |
| **默认组 (最优)** | **`30 / 360 / 64`** | **0.98** | **1.0** | **0.99** | **小数据集下的黄金分割点，达到完美召回与延迟平衡。** |
| 低延迟组 | `16 / 100 / 32` | 0.88 | 1.0 | 0.94 | 图连通性不足，导致部分语义文档漏召回。 |
| 基线对比 | *ChromaDB 默认配置* | *0.967* | *1.0* | *0.983* | *作为对照组，验证 Milvus 精细调参后的反超。* |

> **💡 架构师笔记**：在极小数据集（33 条）上，HNSW 的“高参数”反而成了毒药。因为数据量少时，节点间的语义距离本来就相对较近，过大的 `M` 会让无关节点强行建立连接，导致搜索路径迷失。这也反向印证了：**没有绝对最好的索引参数，只有最适合当前数据分布的参数。**

#### 3. 本地复现指南
1. 启动 Milvus 容器（Docker）。
2. 在 `.env` 中配置 HNSW 参数（如：`MILVUS_HNSW_M=30`）。
3. 执行重建与评测：
   ```bash
   python scripts/ingest.py --rebuild
   python scripts/benchmark_retrieval.py
   ```

### 实验记录

> 💡 **备注**：M4（向量库适配与调优）已于 `2026-10-18` 完成全量评测并结项，数据已填入下表。M1（混合检索）已跑通，M2（微调）目前完成 950 条数据构建与首轮训练。

| 实验模块 | 实验项 | 指标 | v1 基线 | v2 结果 | 结论 / 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **M4: 向量库** | **Milvus vs Chroma 切换** | 业务代码改动量 | - | **0 行** | 验证了 `BaseVectorStore` 工厂模式解耦成功 |
| **M4: 向量库** | **HNSW 参数消融 (高召回)** | Hit@1 / MRR | 0.967 / 0.983 | **0.86 / 0.93** | 参数(M=64)过高导致图过密，引入字面噪声反降精度 |
| **M4: 向量库** | **HNSW 参数消融 (默认最优)** | Hit@1 / MRR | 0.967 / 0.983 | **0.98 / 0.99** | 参数(M=30)最佳，精细调参后反超原生 ChromaDB |
| **M4: 向量库** | **HNSW 参数消融 (低延迟)** | Hit@1 / MRR | 0.967 / 0.983 | **0.88 / 0.94** | 参数(M=16)连通性不足，部分语义文档漏召回 |
| **M1: 检索增强**| **混合检索(BM25+向量 RRF)** | Hit@1 | 0.967 | **0.98** *(参考当前值)* | 成功修复「下单后多久收到」等字面重叠 Badcase |
| **M1: 检索增强**| QueryRewrite 消融 | Hit@1 | 0.967 | *(待填)* | 当前链路已强制开启，单独关闭对照测试中 |
| **M2: 领域微调**| **LoRA 基础训练** | val loss | - | **3.9 → 0.9** | 950 条数据，10分41秒/¥0.35成本，已收敛 |
| **M2: 领域微调**| **LoRA vs QLoRA** | 训练成本 | - | *(待填)* | 三路对比实验排期中 |
| **M3: 评估体系**| RAGAS 四指标 | Faithfulness 等 | - | *(待填)* | 自动化评测脚本已完成，准备跑批 |
| **M2/M3** | Qwen-LoRA 本地 vs DeepSeek API | TTFT / 单次成本 | 4.196s / ¥0.00074 | *(待填)* | 本地 vLLM 部署准备中，目标成本降至 ¥0 |

> 📁 详细报告：[Badcase 修复记录](docs/v2/badcase_fix_report.md) · [RAGAS 评测](docs/v2/ragas_report.md) · [Milvus 压测](docs/v2/milvus_bench.md) · [微调实验](docs/v2/finetune_report.md)

---

## 🖼️ 效果演示

### 流程展示（Vue3 + Element Plus）

![chat demo](./docs/screenshots/chat_demo.gif)

- 回答**逐字出现**（打字机效果）
- 附带 **📚 引用来源**（含相似度）

### 上传资料界面

![upload demo](./docs/screenshots/upload_demo.png)

**示例**：

> **提问**："我买的洗发水用了过敏，能退吗？"
>
> **回答**：可以的。根据《HFP客服知识库》，化妆品类商品如使用后出现过敏反应，可在签收后 15 天内申请退货，需提供医院过敏证明...
>
> **引用来源**：
> - [1] HFP客服知识库.txt（相似度 0.7579）
> - [2] HFP客服知识库.txt（相似度 0.4956）

### 业务闭环演示（Badcase 归因）

![closed loop](./docs/screenshots/closed_loop_demo.png)

### 前端反馈界面

![满意按钮](./docs/screenshots/feedback_buttons.png)

![反馈报告](./docs/screenshots/feedback_report.png)

---

## ✨ 核心功能

### 🎯 RAG 问答

- **多格式文档摄入**：PDF / TXT / Markdown
- **中文语义检索**：`BAAI/bge-small-zh-v1.5` embedding + ChromaDB
- **精排重排序**：`BAAI/bge-reranker-base` CrossEncoder 精排
- **LLM 生成**：DeepSeek Chat 基于检索内容生成，避免幻觉
- **来源引用**：每个回答附带原文片段和相似度，可追溯

### 📤 上传资料（现传现用）

**核心能力**：上传文档 → 系统立即学会 → 用户就能问它。

**工作流程**：

1. 管理员上传新政策文档（TXT / MD / PDF）
2. 系统自动：切块 → embedding → 存入 ChromaDB
3. **重置 RAGChain 单例**（避免 collection 句柄失效）
4. 客服即可基于新政策问答

**电商场景价值**：

| 场景 | 传统方案 | RAG 方案 |
|------|----------|----------|
| 公司出了新政策 | 写文档 → 培训客服 → 客服背下来 | **上传文档 → 系统立即生效** |
| 客服流动 | 新员工培训 3 天才能上岗 | **第一天就能用系统辅助** |

### 🔄 业务闭环（自进化系统）

系统不是单向的"问答管道"，而是带反馈的**自进化系统**。

**闭环流程**：

~~~
用户提问 → RAG 回答 → 反馈采集 → Badcase 归因 → 知识更新 → 效果验证
    ↑                                                        │
    └────────────────────── 迭代循环 ──────────────────────────────┘
~~~

**五个环节**：

| 环节 | 实现 | 代码位置 |
|------|------|---------|
| **感知** | 显式反馈（👍/👎）+ 隐式信号（低置信度自动触发） | `src/rag/feedback/collector.py` |
| **诊断** | 规则引擎归因：知识缺失 / 检索问题 / Prompt 问题 | `src/rag/feedback/triage.py` |
| **治疗** | 自动生成知识缺口报告，指导文档补充 | `src/rag/feedback/knowledge_gap.py` |
| **度量** | 聚合指标：满意率、平均检索分、Badcase 分布 | `src/rag/feedback/metrics.py` |
| **迭代** | 知识运营 → 补充文档 → 重建索引 → 验证 | `scripts/ingest.py` |

**归因规则**：

| 检索分数 | 归因 | 建议动作 |
|---------|------|---------|
| 无检索结果 | `KNOWLEDGE` | 知识运营：补充文档 |
| top_score < 0.5 | `KNOWLEDGE` | 知识覆盖不足，补充文档 |
| 0.5 ≤ top_score < 0.7 | `RETRIEVAL` | 工程优化：调 chunk_size / top_k / Reranker |
| top_score ≥ 0.7 但用户不满意 | `PROMPT` | Prompt 优化 / 换模型 |

**演示**：

~~~bash
python scripts/demo_closed_loop.py
~~~

**输出示例**：

~~~
知识缺口报告
============================================================
总反馈数: 6
Badcase 数: 4

按归因分类:
- knowledge: 3 条 → 知识运营：补充/修订文档
- retrieval: 1 条 → 工程优化：调 chunk_size / top_k / Reranker

知识缺口 TOP 5:
- 「你们家发货要多久？」(top_score=0.123)
- 「能开发票吗？」(top_score=0.089)

业务指标
============================================================
satisfied_rate: 0.333
avg_top_score: 0.456
~~~

### 🔌 平台适配层（对接真实电商平台）

**设计目标**：不替换京麦/千牛，而是作为它们的"AI 增强外挂"，通过官方 OpenAPI 合规接入。

**架构**：

~~~
┌──────────────────────────────────────┐
│        电商平台（京麦 / 千牛 / 抖店）    │
└──────────────┬───────────────────────┘
               │ ① Webhook 推送买家消息
               ▼
┌──────────────────────────────────────┐
│       PlatformAdapter（抽象）         │
│  ├── MockAdapter        ✅ 已实现     │
│  ├── JingmaiAdapter     📋 待接入     │
│  └── QianniuAdapter     📋 待接入     │
└──────────────┬───────────────────────┘
               │ 统一消息模型
               ▼
┌──────────────────────────────────────┐
│    RAGChain（检索 + 重排 + 生成）      │
└──────────────┬───────────────────────┘
               │ ② 调用 sendMsg 回复
               ▼
┌──────────────────────────────────────┐
│  Feedback Loop（归因 + 知识缺口）      │
└──────────────────────────────────────┘
~~~

**当前状态**：

- ✅ Mock 适配器完整可用，可本地验证链路
- 📋 京麦/千牛适配器骨架就绪，拿到 ISV 资质后可快速填充
- 🔒 合规设计：签名验证、幂等去重、Webhook 5 秒响应约束

### ⚡ Streaming 流式输出

- **后端**：`StreamingResponse` 逐 token 推送
- **前端**：`fetch` + `ReadableStream` 逐块解析
- **效果**：首字立即展示

### 💬 三种使用入口

| 入口 | 状态 | 用途 |
|------|------|------|
| **Vue3 Web 界面** | ✅ 推荐 | 客服日常使用 |
| **FastAPI REST 接口** | ✅ 推荐 | 集成到现有客服系统 |
| **CLI 命令行** | ✅ 稳定 | 开发和脚本调用 |

### 🐳 工程化

- **Docker 一键部署**：`docker compose up -d`
- **一键启动脚本**：`start_rag.bat`（Windows）
- **配置外置**：`.env` + Pydantic Settings
- **日志轮转**：RotatingFileHandler
- **全链路自检**：`python scripts/check_all.py`

---

## 🏗️ 系统架构

~~~
┌─────────────────────────────────────────────────────┐
│                  用户浏览器 (Vue3)                   │
│         💬 问答 | 📤 上传资料                        │
└─────────────────┬───────────────────────────────────┘
                  │ HTTP / SSE 流式
                  ▼
┌─────────────────────────────────────────────────────┐
│                Nginx / Vite Proxy                   │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│                FastAPI 后端 (:8000)                 │
│           Routes → Service → RAGChain (单例)        │
│   ├── /query 非流式问答                             │
│   ├── /query/stream 流式问答（SSE）                 │
│   └── /ingest/upload 上传资料 + 重建索引            │
├──────────────┬──────────────┬───────────────────────┤
│ Embedding    │ VectorStore  │ LLM                   │
│ (BGE-zh)     │ (ChromaDB /  │ (DeepSeek /           │
│              │  Milvus·v2)  │  Qwen-LoRA 本地·v2)   │
├──────────────┴──────────────┴───────────────────────┤
│     🔄 Feedback Loop (反馈采集 → 归因 → 知识缺口)    │
├─────────────────────────────────────────────────────┤
│       🔌 Platform Adapter (Mock / 京麦 / 千牛)      │
└─────────────────────────────────────────────────────┘
~~~

> 🚧 v2：LLM 框支持切换为 **Qwen-LoRA 本地模型**（vLLM，经 `LLM` 抽象基类一键切换）；VectorStore 支持 **Milvus**（BM25+RRF 混合检索）。

---

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| **前端** | Vue3 + Element Plus + Axios |
| **后端** | FastAPI + Uvicorn |
| **RAG 框架** | LangChain |
| **向量数据库** | ChromaDB（v1）/ Milvus（v2） |
| **Embedding** | BAAI/bge-small-zh-v1.5 |
| **Reranker** | BAAI/bge-reranker-base |
| **LLM** | DeepSeek Chat |
| **微调** | LLaMA-Factory + Qwen2.5-1.5B-Instruct（LoRA / QLoRA / 全参，v2） |
| **推理部署** | vLLM（OpenAI 兼容 API）/ Ollama GGUF 量化（v2） |
| **流式协议** | SSE（Server-Sent Events） |
| **配置** | Pydantic Settings |
| **部署** | Docker + Compose |

---

## 🚀 快速开始

### 前置条件

- Python 3.10+
- Node.js 18+
- （可选）Docker Desktop

### 方式一：一键启动脚本（Windows）

双击 `start_rag.bat`，自动：

1. 启动 FastAPI 后端（:8000）
2. 启动 Vue3 前端（:5173）
3. 轮询 `/health` 等后端就绪
4. 自动打开浏览器

### 方式二：手动启动

~~~bash
# 1. 克隆
git clone https://github.com/xieyn9988/rag-project.git
cd rag-project

# 如需体验 v2（检索增强 + 微调）：
# git checkout feature/v2-enterprise-enhance

# 2. 虚拟环境
conda create -n chroma_env python=3.10 -y
conda activate chroma_env

# 3. 依赖
pip install -e ".[dev]"

# 4. 配置
cp .env.example .env
# 编辑 .env，填入 DeepSeek API Key

# 5. 摄入数据
python scripts/ingest.py --rebuild

# 6. 后端（CMD 1）
python apps/fastapi_app.py

# 7. 前端（CMD 2）
cd rag-frontend && npm install && npm run dev

# 8. 浏览器
# http://localhost:5173
~~~

### 方式三：Docker 一键部署

~~~bash
cp .env.example .env
docker compose up -d

# 前端：http://localhost
# API 文档：http://localhost:8000/docs
~~~

**注意**：

- **首次 build**：约 10-15 分钟（装 torch + 依赖）
- **首次启动**：容器会 warm-up（加载 BGE + Reranker），约 10-15 秒
- **健康检查**：`curl http://localhost:8000/health` —— 返回 `{"status": "ok", "doc_count": 23}`
- **数据持久化**：`storage/chroma_db` 挂载到宿主机，容器重启不丢索引
- **服务名**：`rag-api`（不是 `api`）

---

## 📖 使用说明

### 客服日常使用（Vue3 界面）

浏览器 `http://localhost:5173`：

- **💬 问答 Tab**：输入问题，回答逐字出现，附带引用来源
- **📤 上传资料 Tab**：拖拽 TXT/MD/PDF，点击上传，系统自动重建索引

### 集成到现有客服系统（API）

> 以下 `curl` 示例不传 `top_k`，用服务端默认值（`config.py` 的 `top_k=2`）。

**非流式接口**：

~~~bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "洗发水过敏能退吗？"}'
~~~

**响应**：

~~~json
{
  "msg_id": "335b4b55-...",
  "question": "洗发水过敏能退吗？",
  "answer": "可以的。根据《HFP客服知识库》...",
  "retrieved": [
    {
      "content": "...",
      "source": "HFP客服知识库.txt",
      "page": null,
      "score": 0.7579
    }
  ]
}
~~~

**流式接口（SSE）**：

~~~bash
curl -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "退货"}'
~~~

**响应流**：

~~~
data: {"type": "start", "msg_id": "0e2f45b6-...", "session_id": "session:0e2f45b6"}

data: {"type": "content", "text": "亲"}

data: {"type": "content", "text": "~"}

data: {"type": "content", "text": "关于"}

...

data: {"type": "references", "references": [{"source": "HFP客服知识库.txt", "page": null, "score": 0.7579}]}

data: {"type": "done", "elapsed_ms": 2060}

data: [DONE]
~~~

**上传资料接口**：

~~~bash
curl -X POST http://localhost:8000/ingest/upload \
  -F "files=@data/text/新政策.md"
~~~

---

## ⚙️ 配置

> **默认值以 `src/rag/config.py` 为准。** 下表只列"可配置项"和"作用"，具体默认值请查阅代码。

| 变量 | 说明 | 建议 |
|------|------|------|
| `RAG_LLM_API_KEY` | **必填**，DeepSeek API Key | 从 [DeepSeek 平台](https://platform.deepseek.com/) 获取 |
| `RAG_LLM_BASE_URL` | DeepSeek API 地址 | 默认官方地址，一般不改 |
| `RAG_LLM_MODEL` | 模型名 | 默认 `deepseek-chat` |
| `RAG_EMBED_MODEL` | Embedding 模型 | 默认 `BAAI/bge-small-zh-v1.5` |
| `RAG_CHUNK_SIZE` | 文本块大小 | 默认 500，改小召回更细，改大上下文更完整 |
| `RAG_CHUNK_OVERLAP` | 块间重叠 | 默认 50，防止语义被切断 |
| `RAG_TOP_K` | 检索文档数 | 默认 2，改大准确率↑但延迟↑ |
| `HF_ENDPOINT` | HuggingFace 镜像 | 国内网络建议 `https://hf-mirror.com` |
| `RAG_LLM_PROVIDER` | LLM 提供方切换（v2） | `deepseek`（默认）/ `qwen_local` |
| `RAG_LLM_LOCAL_BASE_URL` | 本地微调模型 API 地址（v2） | vLLM 默认 `http://localhost:8001/v1` |
| `RAG_RETRIEVAL_MODE` | 检索模式（v2） | `dense`（默认）/ `hybrid`（BM25+向量 RRF） |

**覆盖方式**：在 `.env` 里写 `RAG_XXX=值`，会覆盖 `config.py` 的默认值。

**查看当前生效值**：

~~~bash
curl http://localhost:8000/health
# 返回 model_llm / model_embed / doc_count 等关键配置
~~~

---

## 📝 设计要点

1. **分层架构**：`interface / service / chain / infra` 四层分离
2. **抽象接口**：`Embedder / VectorStore / LLM` 三个 ABC，换供应商不改业务代码
3. **Reranker 精排**：`top_k × 3` 召回 → CrossEncoder 精排 → `top_k`
4. **单例管理**：`RAGChain` 全局复用，避免每次请求重载 BGE 模型
5. **上传后重置单例**：ingest 后 collection 句柄失效，必须重置 RAGChain
6. **反馈闭环**：RAG 质量 70% 取决于知识质量，闭环让"用户不满意"变成"知识补充"输入
7. **归因规则**：200 行规则，准确性高于 AI、成本为零、可解释
8. **平台适配层**：抽象 `PlatformAdapter`，业务代码不耦合平台 API
9. **国内网络优化**：`HF_ENDPOINT=hf-mirror.com` 避免模型下载超时
10. **混合检索**：BM25（关键词）+ 向量（语义）双路召回，RRF 倒数排序融合，互补误伤（v2）
11. **微调防遗忘**：通用数据 replay + 低秩约束 + 双轨评测量化遗忘程度，拒绝"偏科生"模型（v2）

---

## 🎯 技术边界

**不是所有 PDF 都能解析**：

- ✅ 结构化单页 PDF
- ✅ 电子档 PDF（可选中文字）
- ⚠️ 扫描件 PDF → 需 OCR，暂不支持
- ⚠️ 多页切分式宽表 PDF → 暂不支持

**建议**：PDF 请先另存为 Excel/CSV/TXT 后上传。

**平台对接边界**：

- ✅ Mock 适配器本地完整可用
- ⚠️ 京麦/千牛真实接入需要 ISV 资质
- 📋 适配器骨架已就位，拿到资质后可快速填充

### 真实案例：系统遇到"元问题"时的行为

**场景**：用户在对话中看到 AI 回复了一句"我们理解您的心情，服务态度很好的"，接着问：

> 用户："我们理解您的心情，服务态度很好的 --- 这是什么回答"

**系统的回答**：

> 参考文档中没有关于"我们理解您的心情，服务态度很好的"这句话的具体说明或评价，因此无法基于文档判断它属于哪种回答类型或是否合适。
>
> 不过，结合文档 1 中"AI 客服话术需人工复核"的原则，可以明确一点：
>
> - 这类话术属于 **情绪安抚型 / 服务态度表达**，本身不涉及事实、数据或专业建议，通常...

**为什么这个回答是"正确"的**：

| 判断标准 | 系统行为 | 结果 |
|---------|---------|------|
| 是否基于检索内容 | 引用 `HFP客服知识库.txt`（相似度 0.6820） | ✅ 有据可依 |
| 是否产生幻觉 | 没有编造"这句话是我们的话术" | ✅ 忠实文档 |
| 是否承认局限 | "文档中没有关于这句话的具体说明" | ✅ 诚实 |
| 是否可追溯 | 附引用来源和相似度 | ✅ 可 debug |

**这个案例暴露了 RAG 系统的两个本质**：

1. **系统只处理字面问题，不处理真实意图**——用户真实意图可能是"吐槽这句话很假"，但系统把它当"元问题"来回答。**这不是 bug，是 RAG 的边界**。
2. **"答得不准" 不等于 "答错"**——系统**严格遵守"基于文档回答"的约束**，宁可不答、不猜，也不编造。

**未来改进方向**：

- **短期**：Prompt 加"意图识别"约束，遇到元问题先澄清用户真实意图
- **中期**：加意图分类前置层（factual / meta / complaint / chitchat），不同意图走不同 Prompt
- **长期**：加多轮对话记忆，让 LLM 看到"上一轮自己说了什么"，从而理解"这"指的是什么

> ✅ 短期/中期方案已纳入 **v2 M1**（Prompt 模板版本化 + 意图分类前置层）

---

## 🔮 未来规划

- [ ] **真实平台接入**：填实京麦/千牛适配器
- [ ] **多轮对话记忆**：基于 LLM 的历史压缩
- [ ] **多租户隔离**：不同企业独立知识库
- [ ] **Voice RAG**：集成 Whisper
- [ ] **可观测性**：Prometheus + Grafana
- [ ] **灰度 A/B**：优化方案灰度发布

---

## 📄 License

MIT

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain)
- [ChromaDB](https://github.com/chroma-core/chroma)
- [Milvus](https://github.com/milvus-io/milvus)
- [BAAI BGE](https://github.com/FlagOpen/FlagEmbedding)
- [DeepSeek](https://www.deepseek.com/)
- [Qwen2.5](https://github.com/QwenLM/Qwen2.5)
- [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory)
