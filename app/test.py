from app.components.vetor_store import load_vector_store

# 1. 加载向量数据库
db = load_vector_store()

# 2. 从数据库创建一个检索器
retriever = db.as_retriever(search_kwargs={'k': 2})

# 3. 定义一个你想测试的问题
query = "如何治疗痴呆症患者的激越和情绪爆发？"

# 4. 直接调用检索器
retrieved_docs = retriever.invoke(query)

# 5. 打印检索结果
print(f"--- 针对问题 '{query}' 检索到的文档 ---")
for doc in retrieved_docs:
    print(doc.page_content)
    print(f"来源: {doc.metadata.get('source', 'N/A')}")
    print("-" * 20)