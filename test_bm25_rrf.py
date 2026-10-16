from rank_bm25 import BM25Okapi

def reciprocal_rank_fusion(results_list, k=60):
    """RRF 融合多路检索结果"""
    from collections import defaultdict
    score_map = defaultdict(float)
    for results in results_list:
        for rank, doc in enumerate(results):
            key = doc["content"]
            score_map[key] += 1.0 / (k + rank + 1)
    # 按分数倒序排序
    sorted_items = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
    # 还原完整文档，去重
    output = []
    seen = set()
    for content, _ in sorted_items:
        for doc in sum(results_list, []):
            if doc["content"] == content and content not in seen:
                output.append(doc)
                seen.add(content)
                break
    return output

# 1. 知识库文档
chunks = [
    {"content":"支持7天无理由退货，商品不影响二次销售即可申请。","source":"售后政策.md"},
    {"content":"补发申请需要联系客服，提供订单号，3个工作日内处理。","source":"物流售后.md"},
    {"content":"满减活动截止到本月底，优惠券不能叠加使用。","source":"活动规则.md"},
]

# 2. 构建BM25索引
tokenized_corpus = [doc["content"].lower().split() for doc in chunks]
bm25 = BM25Okapi(tokenized_corpus)

# 3. 查询
query = "怎么申请补发"
tokenized_query = query.lower().split()
bm25_scores = bm25.get_scores(tokenized_query)

# 取出top2 BM25结果
top_n = 2
bm25_top_idx = sorted(range(len(bm25_scores)), key=lambda i:bm25_scores[i], reverse=True)[:top_n]
res_bm25 = [chunks[i] for i in bm25_top_idx]

print("==== BM25检索结果 ====")
for item in res_bm25:
    print(item)

# 模拟向量检索返回结果（后面对接向量库时替换成真实向量检索结果）
res_vector = [
    {"content":"补发申请需要联系客服，提供订单号，3个工作日内处理。","source":"物流售后.md"},
    {"content":"支持7天无理由退货，商品不影响二次销售即可申请。","source":"售后政策.md"},
]

# RRF融合两路结果
fusion_result = reciprocal_rank_fusion([res_bm25, res_vector])
print("\n==== RRF融合结果 ====")
for item in fusion_result:
    print(item)
