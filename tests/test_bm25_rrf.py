import sys
from pathlib import Path
# 将项目根目录加入python路径
sys.path.append(str(Path(__file__).parent.parent))

"""
单元测试：BM25Retriever + reciprocal_rank_fusion
"""
from src.rag.retrieval import BM25Retriever, reciprocal_rank_fusion

TEST_CHUNKS = [
    {"content": "支持7天无理由退货，商品不影响二次销售即可申请。", "source": "售后政策.md"},
    {"content": "补发申请需要联系客服，提供订单号，3个工作日内处理。", "source": "物流售后.md"},
    {"content": "满减活动截止到本月底，优惠券不能叠加使用。", "source": "活动规则.md"},
    {"content": "发货时间：16:30前下单当天发货，之后次日发出。", "source": "物流时效.md"},
]


def test_bm25_build_and_retrieve():
    """测试构建索引 + 基础检索"""
    bm25 = BM25Retriever()
    bm25.build_index(TEST_CHUNKS)

    # 查询补发，应该命中第二条
    res = bm25.retrieve("怎么申请补发", top_n=2)
    assert len(res) == 2
    assert "补发申请需要联系客服" in res[0]["content"]


def test_bm25_top_n_limit():
    """测试top_n返回数量限制"""
    bm25 = BM25Retriever()
    bm25.build_index(TEST_CHUNKS)
    res = bm25.retrieve("下单", top_n=1)
    assert len(res) == 1


def test_bm25_empty_query():
    """空查询，返回结果不为报错"""
    bm25 = BM25Retriever()
    bm25.build_index(TEST_CHUNKS)
    res = bm25.retrieve("", top_n=2)
    assert isinstance(res, list)


def test_rrf_fusion_merge_two_lists():
    """RRF融合两路不同顺序结果"""
    # 第一路BM25顺序：docA, docB
    res1 = [
        {"content": "docA", "source": "a.md"},
        {"content": "docB", "source": "b.md"},
    ]
    # 第二路向量检索顺序：docB, docA
    res2 = [
        {"content": "docB", "source": "b.md"},
        {"content": "docA", "source": "a.md"},
    ]
    fused = reciprocal_rank_fusion([res1, res2])
    assert len(fused) == 2
    # 两者排名接近，顺序可接受，只要两个文档都存在
    contents = [x["content"] for x in fused]
    assert "docA" in contents
    assert "docB" in contents


def test_rrf_duplicate_deduplicate():
    """RRF对重复chunk做去重"""
    res1 = [{"content": "same_doc", "source": "s1.md"}]
    res2 = [{"content": "same_doc", "source": "s1.md"}]
    fused = reciprocal_rank_fusion([res1, res2])
    assert len(fused) == 1


def test_rrf_badcase_simulate():
    """模拟v1原始badcase：我下单后多久能收到？
    BM25命中字面“下单”的噪声文档；向量召回命中时效文档；RRF融合把正确文档提升
    """
    # 噪声文档：字面含“下单”，但和多久到货无关
    noise_doc = {"content": "现在下单包邮活动", "source": "promo.md"}
    good_doc = {"content": "发货时间：16:30前下单当天发货，之后次日发出。", "source": "物流时效.md"}

    res_bm25 = [noise_doc, good_doc]
    res_vector = [good_doc, noise_doc]

    fused = reciprocal_rank_fusion([res_bm25, res_vector])
    # 融合后正确文档应该排在第一位
    assert fused[0]["content"] == good_doc["content"]
