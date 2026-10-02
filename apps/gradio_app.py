# apps/gradio_app.py

import os

# ⚠️ 必须在导入 rag 之前设置，否则模型仍会走官方源
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import shutil
from pathlib import Path

import gradio as gr

from rag.config import settings
from rag.ingestion.pipeline import ingest
from rag.logging_config import setup_logging
from rag.rag import RAGChain

from uuid import uuid4

from rag.feedback import collect_explicit, generate_report, load_all

setup_logging()
DATA_DIR = settings.resolve(settings.data_dir)

# 全局 chain，上传资料后需要重建
chain = RAGChain()
# 保存上一轮回答，用于反馈（msg_id / question / answer / scores / snippets）
_last_response: dict = {}


def reload_chain():
    """重新创建 RAGChain，让新的 collection 生效"""
    global chain
    chain = RAGChain()


def answer(question: str, top_k: int):
    """执行问答，并保存上下文供反馈使用"""
    if not question or not question.strip():
        return "请输入问题", "", ""

    try:
        resp = chain.query(question, top_k=top_k)
    except Exception as e:
        return f"[ERROR] {e}", "", ""

    # 保存上一轮问答上下文
    msg_id = str(uuid4())
    scores = [s for _, s in resp.retrieved]
    snippets = [d.page_content[:100] for d, _ in resp.retrieved]

    _last_response.clear()
    _last_response.update({
        "msg_id": msg_id,
        "question": question,
        "answer": resp.answer,
        "scores": scores,
        "snippets": snippets,
    })

    refs_md = "\n\n".join(
        f"**[{i+1}]** 相似度 `{s:.4f}`\n\n{d.page_content}"
        for i, (d, s) in enumerate(resp.retrieved)
    )
    return resp.answer, refs_md, msg_id


def feedback(satisfied: bool):
    """用户点击👍/👎时调用"""
    if not _last_response:
        return "⚠️ 还没有可反馈的问答"

    collect_explicit(
        session_id="gradio_session",
        msg_id=_last_response["msg_id"],
        question=_last_response["question"],
        answer=_last_response["answer"],
        satisfied=satisfied,
        rerank_scores=_last_response["scores"],
        retrieved_snippets=_last_response["snippets"],
    )
    return f"已记录：{'满意 ✅' if satisfied else '不满意 ❌'}"


def show_report():
    """生成 Badcase 归因 + 知识缺口报告"""
    report = generate_report(load_all())
    lines = [
        f"总反馈数: {report['total_feedbacks']}",
        f"Badcase 数: {report['total_badcases']}",
        "",
        "按归因分类:",
    ]
    for cause, count in report.get("by_root_cause", {}).items():
        lines.append(f"  - {cause}: {count} 条")

    lines.append("")
    lines.append("建议动作:")
    for a in report.get("suggested_actions", []):
        lines.append(f"  → {a}")

    lines.append("")
    lines.append("知识缺口 TOP 10:")
    for gap in report.get("knowledge_gaps", [])[:10]:
        lines.append(f"  - 「{gap['question']}」(score={gap['top_score']:.3f})")

    return "\n".join(lines)


def upload_and_ingest(files):
    """保存上传的文件并重建索引"""
    if not files:
        return "未选择文件"

    saved = []
    for f in files:
        src = Path(f.name)
        suffix = src.suffix.lower()
        if suffix == ".pdf":
            target_dir = DATA_DIR / "pdfs"
        elif suffix in (".txt", ".md"):
            target_dir = DATA_DIR / "text"
        else:
            saved.append(f"[跳过] {src.name}：不支持的类型 {suffix}")
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        dst = target_dir / src.name
        shutil.copy(f.name, dst)
        saved.append(f"[OK] {src.name} → {dst.relative_to(DATA_DIR.parent)}")

    try:
        n = ingest(rebuild=True)
        reload_chain()
        saved.append("")
        saved.append(f"✓ 已重建索引，当前共 {n} 个文本块")
    except Exception as e:
        saved.append(f"[ERROR] 摄入失败: {e}")
    return "\n".join(saved)


with gr.Blocks(title="电商客服 RAG 智能问答系统") as demo:
    gr.Markdown("# 🛒 电商客服 RAG 智能问答系统")
    gr.Markdown("输入客户问题，系统会自动检索政策文档并生成回答。")

    with gr.Tabs():
        # ========== Tab 1: 问答（含反馈按钮） ==========
        with gr.Tab("💬 问答"):
            with gr.Row():
                with gr.Column(scale=3):
                    q = gr.Textbox(label="问题", lines=3, placeholder="输入你想问的问题...")
                    k = gr.Slider(1, 10, value=3, step=1, label="检索文档数")
                    with gr.Row():
                        btn = gr.Button("提交", variant="primary")
                        clr = gr.Button("清空")
                    with gr.Row():
                        good_btn = gr.Button("👍 满意")
                        bad_btn = gr.Button("👎 不满意")
                    fb_output = gr.Textbox(label="反馈状态", lines=1)
                with gr.Column(scale=4):
                    ans = gr.Markdown(label="回答")
                    refs = gr.Markdown(label="引用")

            msg_id_state = gr.State("")

            def on_submit(question, k):
                a, r, mid = answer(question, k)
                return a, r, mid

            # 事件绑定
            btn.click(on_submit, [q, k], [ans, refs, msg_id_state])
            q.submit(on_submit, [q, k], [ans, refs, msg_id_state])
            clr.click(lambda: ("", "", "", ""), None, [q, ans, refs, fb_output])
            good_btn.click(lambda: feedback(True), None, fb_output)
            bad_btn.click(lambda: feedback(False), None, fb_output)

        # ========== Tab 2: 上传资料 ==========
        with gr.Tab("📤 上传资料"):
            gr.Markdown("上传 TXT / MD / PDF，系统会自动保存并重建索引。")
            file_input = gr.File(
                label="选择文件（可多选）",
                file_count="multiple",
                file_types=[".txt", ".md", ".pdf"],
            )
            upload_btn = gr.Button("上传并重建索引", variant="primary")
            upload_output = gr.Textbox(label="处理结果", lines=10)
            upload_btn.click(upload_and_ingest, file_input, upload_output)

        # ========== Tab 3: 反馈报告（🆕） ==========
        with gr.Tab("📊 反馈报告"):
            gr.Markdown("Badcase 归因 + 知识缺口报告（每点一次刷新）")
            refresh_btn = gr.Button("刷新报告", variant="primary")
            report_output = gr.Textbox(label="报告", lines=20)
            refresh_btn.click(show_report, None, report_output)
            

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)