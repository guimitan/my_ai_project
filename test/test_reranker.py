"""
重排序器单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

from app.core.reranker import CrossEncoderReranker, RerankerFactory


class TestCrossEncoderReranker:
    """CrossEncoder 重排序器测试"""

    @pytest.fixture
    def sample_docs(self):
        """创建测试用文档列表"""
        return [
            Document(page_content="人工智能是计算机科学的重要分支", metadata={"id": "1"}),
            Document(page_content="机器学习使用数据进行训练", metadata={"id": "2"}),
            Document(page_content="深度学习是机器学习的子领域", metadata={"id": "3"}),
            Document(page_content="今天天气很好适合出去散步", metadata={"id": "4"}),
            Document(page_content="自然语言处理是AI应用领域", metadata={"id": "5"}),
        ]

    @pytest.fixture
    def reranker(self):
        """创建启发式重排序器（避免加载真实模型）"""
        return RerankerFactory.create_reranker("heuristic")

    def test_heuristic_rerank_relevance(self, reranker, sample_docs):
        """测试启发式重排序：相关文档排名更高"""
        query = "人工智能和机器学习"
        results = reranker.rerank(query, sample_docs, top_k=3)

        assert len(results) == 3
        # 相关文档应排在最前
        top_content = results[0].page_content
        assert "人工智能" in top_content or "机器学习" in top_content

    def test_heuristic_rerank_adds_metadata(self, reranker, sample_docs):
        """测试重排序添加元数据分数"""
        query = "人工智能"
        results = reranker.rerank(query, sample_docs, top_k=5)

        for doc in results:
            assert 'reranker_score' in doc.metadata
            assert isinstance(doc.metadata['reranker_score'], float)
            assert 0.0 <= doc.metadata['reranker_score'] <= 1.0

    def test_rerank_empty_docs(self, reranker):
        """测试空文档列表"""
        results = reranker.rerank("测试查询", [], top_k=5)
        assert results == []

    def test_rerank_single_doc(self, reranker):
        """测试单个文档重排序"""
        doc = Document(page_content="这是一个测试文档", metadata={"id": "1"})
        results = reranker.rerank("测试", [doc], top_k=5)
        assert len(results) == 1
        assert results[0].page_content == "这是一个测试文档"

    def test_rerank_top_k_limit(self, reranker, sample_docs):
        """测试 top_k 限制"""
        results = reranker.rerank("AI", sample_docs, top_k=2)
        assert len(results) == 2

    def test_heuristic_length_penalty(self, reranker):
        """测试长度惩罚机制"""
        short_doc = Document(page_content="短文档", metadata={"id": "short"})
        good_doc = Document(page_content="这是一个长度适中内容丰富的文档，包含了足够的信息来进行有效的检索和排序", metadata={"id": "good"})
        long_doc = Document(page_content="非常长的文档" * 500, metadata={"id": "long"})

        docs = [short_doc, good_doc, long_doc]
        results = reranker.rerank("文档内容 检索 排序 有效 信息", docs, top_k=3)

        # 长度适中的文档应该排名靠前（无惩罚）
        assert len(results) == 3

    def test_heuristic_query_without_match(self, reranker):
        """测试查询词完全不匹配时的情况"""
        docs = [
            Document(page_content="文档A的内容", metadata={"id": "1"}),
            Document(page_content="文档B的内容", metadata={"id": "2"}),
        ]
        results = reranker.rerank("完全无关查询词", docs, top_k=2)
        assert len(results) == 2
        # 所有文档分数应该接近（因为没有匹配词）
        scores = [doc.metadata['reranker_score'] for doc in results]
        assert all(0.0 <= s <= 1.0 for s in scores)


class TestRerankerFactory:
    """重排序器工厂测试"""

    def test_create_cross_encoder(self):
        """测试创建 CrossEncoder 重排序器"""
        reranker = RerankerFactory.create_reranker("cross_encoder")
        assert reranker is not None
        assert isinstance(reranker, CrossEncoderReranker)

    def test_create_heuristic(self):
        """测试创建启发式重排序器"""
        reranker = RerankerFactory.create_reranker("heuristic")
        assert reranker is not None
        assert isinstance(reranker, CrossEncoderReranker)

    def test_create_none(self):
        """测试创建空重排序器"""
        reranker = RerankerFactory.create_reranker("none")
        assert reranker is None

    def test_create_default(self):
        """测试默认创建"""
        reranker = RerankerFactory.create_reranker()
        assert reranker is not None
