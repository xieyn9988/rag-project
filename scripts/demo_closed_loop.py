# scripts/demo_closed_loop.py
"""完整业务闭环演示

流程：
  模拟买家咨询 → RAG 回答 → 自动判低置信度 / 模拟用户反馈
  → 归因分析 → 生成知识缺口报告
"""
import uuid

from rag.feedback import (
    collect_explicit,
    collect_low_confidence,
    compute_metrics,
    generate_report,
    load_all,
)
from rag.logging_config import setup_logging
from rag.platform import build_adapter, OutgoingMessage
from rag.rag import RAGChain

setup_logging()

adapter = build_adapter("mock", shop_id="demo_shop")
chain = RAGChain()

# 模拟 4 类场景
scenarios = [
    ("什么是 RAG？", True),          # 知识库有 → 用户满意
    ("AI 的能力边界是什么？", True),   # 知识库有 → 用户满意
    ("你们家发货要多久？", False),     # 知识库没有 → 用户不满意
    ("能开发票吗？", False),          # 知识库没有 → 用户不满意
]

print("=" * 70)
print("电商智能客服 · 业务闭环演示")
print("=" * 70)

for content, user_satisfied in scenarios:
    # 1. 平台接收消息
    incoming = adapter.parse_webhook({"buyer_id": "buyer_001", "content": content})
    print(f"\n👤 买家: {content}")

    # 2. RAG 回答
    response = chain.query(incoming.content, top_k=2)
    print(f"🤖 客服: {response.answer[:120]}...")

    # 3. 组装出站消息
    reply = OutgoingMessage(
        session_id=incoming.session_id,
        msg_id=incoming.msg_id,
        question=incoming.content,
        content=response.answer,
        references=[
            {"score": s, "snippet": d.page_content[:80]}
            for d, s in response.retrieved
        ],
        rerank_scores=[s for _, s in response.retrieved],
    )
    adapter.send_reply(reply)

    # 4. 反馈采集
    scores = [s for _, s in response.retrieved]
    snippets = [d.page_content[:100] for d, _ in response.retrieved]

    # 4.1 自动判低置信度
    low_conf_fb = collect_low_confidence(
        session_id=incoming.session_id,
        msg_id=incoming.msg_id,
        question=incoming.content,
        answer=response.answer,
        rerank_scores=scores,
        retrieved_snippets=snippets,
    )
    # 4.2 模拟用户显式反馈
    collect_explicit(
        session_id=incoming.session_id,
        msg_id=incoming.msg_id,
        question=incoming.content,
        answer=response.answer,
        satisfied=user_satisfied,
        rerank_scores=scores,
        retrieved_snippets=snippets,
    )
    if low_conf_fb:
        print(f"⚠️  系统识别为低置信度，已自动记录")

# 5. 生成报告
print("\n" + "=" * 70)
print("📊 知识缺口报告")
print("=" * 70)

records = load_all()
report = generate_report(records)

print(f"\n总反馈数: {report['total_feedbacks']}")
print(f"Badcase 数: {report['total_badcases']}")
print(f"\n按归因分类:")
for cause, count in report["by_root_cause"].items():
    print(f"  - {cause}: {count} 条")

print(f"\n建议动作:")
for action in report["suggested_actions"]:
    print(f"  → {action}")

print(f"\n知识缺口 TOP 5:")
for gap in report["knowledge_gaps"][:5]:
    print(f"  - 「{gap['question']}」(top_score={gap['top_score']:.3f})")

# 6. 指标
print("\n" + "=" * 70)
print("📈 业务指标")
print("=" * 70)
metrics = compute_metrics(records)
for k, v in metrics.items():
    print(f"  {k}: {v}")