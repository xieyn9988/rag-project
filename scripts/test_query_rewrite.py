# scripts/test_query_rewrite.py
from rag.api.service import get_chain
from rag.retrieval.query_transform import QueryRewriter

chain = get_chain()
rewriter = QueryRewriter(chain._llm)

queries = rewriter.rewrite("我下单后多久能收到？")
print("改写结果：")
for q in queries:
    print(f"  - {q}")