# apps/gradio_app.py
import shutil
from pathlib import Path

import gradio as gr

from rag.config import settings
from rag.ingestion.pipeline import ingest
from rag.logging_config import setup_logging
from rag.rag import RAGChain

setup_logging()
DATA_DIR = settings.resolve(settings.data_dir)

# 全局 chain，上传资料后需要重建
chain = RAGChain()


def reload_chain():
    """重新创建 RAGChain，让新的 collection 生效"""
    global chain
    chain = RAGChain()


def answer(question: str, top_k: int):
    if not question or not question.strip():
        return "请输入问题", ""
    try:
        resp = chain.query(question, top_k=top_k)
    except Exception as e:
        return f"[ERROR] {e}", ""
    refs_md = "\n\n".join(
        f"**[{i+1}]** 相似度 `{s:.4f}`\n\n{d.page_content}"
        for i, (d, s) in enumerate(resp.retrieved)
    )
    return resp.answer, refs_md


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


with gr.Blocks(title="RAG 智能问答") as demo:
    gr.Markdown("# 🧠 RAG 智能问答系统")
    gr.Markdown("基于 **LangChain + ChromaDB + BGE + DeepSeek**")

    with gr.Tabs():
        with gr.Tab("💬 问答"):
            with gr.Row():
                with gr.Column(scale=3):
                    q = gr.Textbox(label="问题", lines=3, placeholder="输入你想问的问题...")
                    k = gr.Slider(1, 10, value=3, step=1, label="检索文档数")
                    with gr.Row():
                        btn = gr.Button("提交", variant="primary")
                        clr = gr.Button("清空")
                with gr.Column(scale=4):
                    ans = gr.Markdown(label="回答")
                    refs = gr.Markdown(label="引用")
            btn.click(answer, [q, k], [ans, refs])
            q.submit(answer, [q, k], [ans, refs])
            clr.click(lambda: ("", "", ""), None, [q, ans, refs])

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


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)