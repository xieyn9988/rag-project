# scripts/ingest.py
import argparse

from rag.ingestion.pipeline import ingest
from rag.logging_config import setup_logging


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="清空后重建")
    args = parser.parse_args()
    setup_logging()
    n = ingest(rebuild=args.rebuild)
    print(f"Done. Total docs: {n}")


if __name__ == "__main__":
    main()