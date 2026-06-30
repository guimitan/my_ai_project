"""
混合检索器单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

from app.core.hybrid_retriever import BM25Retriever, HybridRetriever


class TestBM25Retriever:
    """BM25 检索器测试"""

    def test_build_index(self, sample_documents):
        """测试构建 BM25 索引"""
        retriever = BM25Retriever()
        retriever.build_index(sample_documents)
        assert retriever.bm25 is not None
        assert len(retriever.documents) == len(sample_documents)
        assert len(retriever.doc_mapping) == len(sample_documents)

    def test_search_returns_results(self, sample_documents):
        """测试 BM25 搜索返回结果"""
        retriever = BM25Retriever()
        retriever.build_index(sample_documents)
        results = retriever.search("人工智能", k=3)
        assert len(results) > 0
        assert len(results) <= 3
        for doc, score in results:
            assert isinstance(doc, Document)
            assert isinstance(score, float)
            assert score > 0

    def test_search_empty_index_raises(self):
        """测试空索引搜索抛出异常"""
        retriever = BM25Retriever()
        with pytest.raises(ValueError, match="BM25索引未构建"):
            retriever.search("测试查询")

    def test_search_results_sorted_by_score(self, sample_documents):
        """测试搜索结果按分数降序排列"""
        retriever = BM25Retriever()
        retriever.build_index(sample_documents)
        results = retriever.search("人工智能", k=5)
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True), "结果应按分数降序排列"

    def test_search_relevant_docs_rank_higher(self, sample_documents):
        """测试相关文档排名更高"""
        retriever = BM25Retriever()
        retriever.build_index(sample_documents)
        results = retriever.search("机器学习 深度学习", k=5)
        if len(results) >= 2:
            # "机器学习"文档应排在最前
            top_content = results[0][0].page_content
            assert "机器学习" in top_content or "深度学习" in top_content


class TestHybridRetrieverMerge:
    """混合检索结果合并测试"""

    def test_merge_results_no_overlap(self):
        """测试无重叠结果的合并"""
        doc1 = Document(page_content="文档A内容", metadata={"id": "1"})
        doc2 = Document(page_content="文档B内容", metadata={"id": "2"})

        vector_results = [(doc1, 0.9)]
        bm25_results = [(doc2, 0.8)]

        # 需要初始化 retriever 来调用 _merge_results
        retriever = HybridRetriever.__new__(HybridRetriever)
        merged = retriever._merge_results(vector_results, bm25_results)

        assert len(merged) == 2
        assert "文档A内容" in merged
        assert "文档B内容" in merged
        assert merged["文档A内容"]["vector_score"] == 0.9
        assert merged["文档A内容"]["bm25_score"] == 0.0
        assert merged["文档B内容"]["vector_score"] == 0.0
        assert merged["文档B内容"]["bm25_score"] == 0.8

    def test_merge_results_with_overlap(self):
        """测试有重叠结果的合并（取最高分）"""
        doc = Document(page_content="重叠文档内容", metadata={"id": "1"})

        vector_results = [(doc, 0.9)]
        bm25_results = [(doc, 0.6)]

        retriever = HybridRetriever.__new__(HybridRetriever)
        merged = retriever._merge_results(vector_results, bm25_results)

        assert len(merged) == 1
        assert merged["重叠文档内容"]["vector_score"] == 0.9
        assert merged["重叠文档内容"]["bm25_score"] == 0.6

    def test_rank_fusion_weights(self):
        """测试加权融合排序"""
        doc1 = Document(page_content="高向量分文档", metadata={"id": "1"})
        doc2 = Document(page_content="高BM25分文档", metadata={"id": "2"})

        merged = {
            "高向量分文档": {
                "document": doc1, "vector_score": 0.9, "bm25_score": 0.1
            },
            "高BM25分文档": {
                "document": doc2, "vector_score": 0.1, "bm25_score": 0.9
            },
        }

        retriever = HybridRetriever.__new__(HybridRetriever)

        # 向量权重高时，doc1 应排第一
        result_vector = retriever._rank_fusion(merged, vector_weight=0.9, bm25_weight=0.1, top_k=2)
        assert result_vector[0].page_content == "高向量分文档"

        # BM25 权重高时，doc2 应排第一
        result_bm25 = retriever._rank_fusion(merged, vector_weight=0.1, bm25_weight=0.9, top_k=2)
        assert result_bm25[0].page_content == "高BM25分文档"

    def test_rank_fusion_normalization(self):
        """测试分数归一化"""
        doc = Document(page_content="测试文档", metadata={"id": "1"})
        merged = {
            "测试文档": {
                "document": doc, "vector_score": 5.0, "bm25_score": 3.0
            },
        }

        retriever = HybridRetriever.__new__(HybridRetriever)
        result = retriever._rank_fusion(merged, vector_weight=0.5, bm25_weight=0.5, top_k=1)

        assert len(result) == 1
        # 两个分数归一化后都应该是 1.0（各自最大值）
        assert result[0].page_content == "测试文档"
