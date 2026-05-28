"""
混合检索与重排序 - 使用示例

本文件展示如何使用新的混合检索和重排序功能
注意：这不是测试脚本，仅作为代码参考示例
"""

# ============================================================
# 示例1: 基本使用 - 自动启用所有高级功能
# ============================================================
def example_basic_usage():
    """最基本的用法，自动启用混合检索和重排序"""
    from app.core.rag_chain import RAGChain
    
    # 创建RAG链（默认启用混合检索+重排序）
    rag = RAGChain()
    
    # 查询
    result = rag.query("RAG系统使用的是什么向量数据库？", k=5)
    
    print(f"答案: {result['answer']}")
    print(f"来源数量: {result['context_count']}")


# ============================================================
# 示例2: 自定义检索策略
# ============================================================
def example_custom_strategy():
    """自定义检索和重排序策略"""
    from app.core.rag_chain import RAGChain
    
    # 策略1: 只用混合检索，不重排序（速度较快）
    rag1 = RAGChain(
        use_hybrid_retrieval=True,
        use_reranker=False
    )
    
    # 策略2: 只用重排序，不用混合检索
    rag2 = RAGChain(
        use_hybrid_retrieval=False,
        use_reranker=True,
        reranker_type="heuristic"  # 使用启发式重排序
    )
    
    # 策略3: 回退到纯向量检索（最简单）
    rag3 = RAGChain(
        use_hybrid_retrieval=False,
        use_reranker=False
    )


# ============================================================
# 示例3: 调整检索权重
# ============================================================
def example_adjust_weights():
    """调整向量检索和BM25的权重"""
    from app.core.rag_chain import RAGChain
    
    rag = RAGChain()
    
    # 更重视语义匹配
    result1 = rag.query(
        "如何优化模型性能？",
        k=5,
        vector_weight=0.9,  # 向量权重90%
        bm25_weight=0.1     # BM25权重10%
    )
    
    # 更重视关键词匹配
    result2 = rag.query(
        "ChromaDB 配置参数",
        k=5,
        vector_weight=0.5,  # 向量权重50%
        bm25_weight=0.5     # BM25权重50%
    )


# ============================================================
# 示例4: 单独使用混合检索器
# ============================================================
def example_hybrid_retriever_only():
    """直接使用混合检索器（不经过RAG链）"""
    from app.core.hybrid_retriever import HybridRetriever
    from app.core.vector_db import VectorDatabase
    
    # 初始化
    vector_db = VectorDatabase()
    vector_db.initialize()
    
    hybrid = HybridRetriever(vector_db)
    
    # 检索文档
    docs = hybrid.retrieve(
        query="文本分割策略",
        k=10,
        vector_weight=0.7,
        bm25_weight=0.3
    )
    
    # 查看结果
    for i, doc in enumerate(docs, 1):
        print(f"\n文档 {i}:")
        print(f"内容预览: {doc.page_content[:100]}...")
        print(f"元数据: {doc.metadata}")


# ============================================================
# 示例5: 单独使用重排序器
# ============================================================
def example_reranker_only():
    """直接使用重排序器"""
    from app.core.reranker import CrossEncoderReranker
    from langchain_core.documents import Document
    
    # 初始化重排序器
    reranker = CrossEncoderReranker()
    
    # 准备待重排序的文档
    query = "如何处理PDF文档？"
    documents = [
        Document(page_content="PDF是一种常用的文档格式...", metadata={}),
        Document(page_content="图片处理需要使用OCR技术...", metadata={}),
        Document(page_content="PDF文档可以通过PyPDF2库解析...", metadata={}),
    ]
    
    # 重排序
    ranked_docs = reranker.rerank(query, documents, top_k=2)
    
    # 查看结果
    for i, doc in enumerate(ranked_docs, 1):
        print(f"\n排名 {i}:")
        print(f"内容: {doc.page_content}")
        print(f"分数: {doc.metadata.get('reranker_score', 'N/A')}")


# ============================================================
# 示例6: 刷新BM25索引
# ============================================================
def example_refresh_index():
    """当向量数据库更新后，刷新BM25索引"""
    from app.core.hybrid_retriever import HybridRetriever
    from app.core.vector_db import VectorDatabase
    
    vector_db = VectorDatabase()
    vector_db.initialize()
    
    hybrid = HybridRetriever(vector_db)
    
    # 添加新文档后，刷新索引
    hybrid.refresh_index()
    
    print("✅ BM25索引已刷新")


# ============================================================
# 示例7: 在Web UI中使用
# ============================================================
def example_webui_integration():
    """在Streamlit Web UI中集成混合检索"""
    import streamlit as st
    from app.core.rag_chain import RAGChain
    
    # 侧边栏配置
    st.sidebar.header("检索配置")
    use_hybrid = st.sidebar.checkbox("启用混合检索", value=True)
    use_reranker = st.sidebar.checkbox("启用重排序", value=True)
    
    # 创建RAG链
    rag = RAGChain(
        use_hybrid_retrieval=use_hybrid,
        use_reranker=use_reranker
    )
    
    # 用户输入
    question = st.text_input("请输入问题")
    
    if question:
        with st.spinner("正在检索和生成答案..."):
            result = rag.query(question, k=5)
            
        st.write("### 答案")
        st.write(result['answer'])
        
        st.write("### 来源")
        for source in result['sources']:
            st.json(source)


# ============================================================
# 示例8: 批量评估不同策略
# ============================================================
def example_evaluate_strategies():
    """评估不同检索策略的效果"""
    from app.core.rag_chain import RAGChain
    from app.evaluation.retrieval_evaluator import RetrievalEvaluator
    from app.evaluation.dataset_manager import TestDatasetManager
    
    # 加载测试数据集
    dataset_mgr = TestDatasetManager()
    test_cases = dataset_mgr.get_all_test_cases()
    
    # 评估策略1: 纯向量检索
    rag1 = RAGChain(use_hybrid_retrieval=False, use_reranker=False)
    evaluator1 = RetrievalEvaluator(rag1)
    result1 = evaluator1.evaluate_batch(test_cases, k=5, verbose=False)
    
    # 评估策略2: 混合检索
    rag2 = RAGChain(use_hybrid_retrieval=True, use_reranker=False)
    evaluator2 = RetrievalEvaluator(rag2)
    result2 = evaluator2.evaluate_batch(test_cases, k=5, verbose=False)
    
    # 评估策略3: 混合检索 + 重排序
    rag3 = RAGChain(use_hybrid_retrieval=True, use_reranker=True)
    evaluator3 = RetrievalEvaluator(rag3)
    result3 = evaluator3.evaluate_batch(test_cases, k=5, verbose=False)
    
    # 对比结果
    print("=" * 60)
    print("检索策略对比")
    print("=" * 60)
    print(f"{'策略':<20} {'Precision':<12} {'Recall':<12} {'MRR':<12}")
    print("-" * 60)
    
    metrics1 = result1['aggregate_metrics']
    metrics2 = result2['aggregate_metrics']
    metrics3 = result3['aggregate_metrics']
    
    print(f"{'纯向量检索':<20} {metrics1['avg_precision']:<12.3f} {metrics1['avg_recall']:<12.3f} {metrics1['avg_mrr']:<12.3f}")
    print(f"{'混合检索':<20} {metrics2['avg_precision']:<12.3f} {metrics2['avg_recall']:<12.3f} {metrics2['avg_mrr']:<12.3f}")
    print(f"{'混合+重排序':<20} {metrics3['avg_precision']:<12.3f} {metrics3['avg_recall']:<12.3f} {metrics3['avg_mrr']:<12.3f}")


# ============================================================
# 主函数 - 展示所有示例
# ============================================================
if __name__ == "__main__":
    print("混合检索与重排序 - 使用示例")
    print("=" * 60)
    print("\n本文件包含8个使用示例，展示了不同的使用场景")
    print("您可以根据需要选择适合的示例进行参考\n")
    
    print("可用示例:")
    print("1. example_basic_usage()         - 基本使用")
    print("2. example_custom_strategy()     - 自定义策略")
    print("3. example_adjust_weights()      - 调整权重")
    print("4. example_hybrid_retriever_only() - 单独使用混合检索器")
    print("5. example_reranker_only()       - 单独使用重排序器")
    print("6. example_refresh_index()       - 刷新BM25索引")
    print("7. example_webui_integration()   - Web UI集成")
    print("8. example_evaluate_strategies() - 批量评估策略")
    
    print("\n💡 提示: 取消注释下面的代码来运行示例")
    
    # 运行基本示例
    # example_basic_usage()
