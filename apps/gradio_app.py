# apps/gradio_app.py
import gradio as gr

from rag.logging_config import setup_logging
from rag.rag import RAGChain

setup_logging()
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


with gr.Blocks(title="RAG 智能问答") as demo:
    gr.Markdown("# 🧠 RAG 智能问答系统")
    gr.Markdown("基于 **LangChain + ChromaDB + BGE + DeepSeek**")

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


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)