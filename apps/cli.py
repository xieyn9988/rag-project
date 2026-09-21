# apps/cli.py
import os

# ⚠️ 必须在导入任何 rag 模块之前设置
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import argparse
import sys

from rag.logging_config import setup_logging
from rag.rag import RAGChain


def main():
    parser = argparse.ArgumentParser(description="RAG 命令行问答")
    parser.add_argument("-q", "--question", required=True, help="要问的问题")
    parser.add_argument("-k", "--top-k", type=int, default=None, help="检索文档数")
    parser.add_argument("--show-refs", action="store_true", help="显示引用")
    args = parser.parse_args()

    setup_logging()
    try:
        chain = RAGChain()
        resp = chain.query(args.question, top_k=args.top_k)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    print("\n=== 回答 ===")
    print(resp.answer)

    if args.show_refs:
        print("\n=== 引用 ===")
        for i, (d, s) in enumerate(resp.retrieved):
            print(f"[{i+1}] sim={s:.4f} | {d.page_content[:80]}...")


if __name__ == "__main__":
    main()