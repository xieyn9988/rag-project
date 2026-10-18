from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType
import numpy as np

# 1. 连接 Milvus
connections.connect("default", host="localhost", port="19530")
print("连接成功！Milvus 版本：", utility.get_server_version())

# 清理可能残留的旧集合（防止之前建错的卡住）
if utility.has_collection("quick_test"):
    utility.drop_collection("quick_test")

# 2. 定义 Collection
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=8)
]
schema = CollectionSchema(fields, description="test_collection")
collection = Collection(name="quick_test", schema=schema)

# 3. 插入数据（使用 float32 数组）
query_vec = np.array([[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]], dtype=np.float32)
collection.insert([query_vec])
print("数据插入成功！总条数：", collection.num_entities)

# 4. 建索引并加载（必须先做这一步，才能搜索）
index_params = {"index_type": "AUTOINDEX", "metric_type": "L2", "params": {}}
collection.create_index(field_name="vector", index_params=index_params)
collection.load()
print("索引创建并加载成功！")

# 5. 执行搜索（变量定义好之后，再调 search）
search_params = {"metric_type": "L2", "params": {}}
results = collection.search(
    data=query_vec,
    anns_field="vector",
    param=search_params,
    limit=1
)
print(f"搜索成功！找到 {len(results[0])} 条结果，距离为 {results[0][0].distance}")

# 6. 清理
collection.drop()
print("测试完成，已清理测试数据。")