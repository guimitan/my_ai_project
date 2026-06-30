"""
RAG 链单元测试（使用 mock 避免真实 API 调用）
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from langchain_core.documents import Document

from app.core.rag_chain import RAGChain


class TestRAGChainPrompt:
    """RAG 链提示模板测试"""

    @pytest.fixture
    def mock_rag_chain(self):
        """创建一个模拟的 RAGChain，跳过真实初始化"""
        with patch('app.core.rag_chain.RAGChain._initialize_llm', return_value=None):
            with patch('app.core.rag_chain.RAGChain._create_prompt'):
                chain = RAGChain.__new__(RAGChain)
                chain.vector_db = MagicMock()
                chain.use_hybrid_retrieval = False
                chain.hybrid_retriever = None
                chain.use_reranker = False
                chain.reranker = None
                chain.llm = None
                return chain

    def test_prompt_format(self):
        """测试提示模板格式"""
        chain = RAGChain.__new__(RAGChain)
        chain.prompt = chain._create_prompt()

        formatted = chain.prompt.format(
            context="测试上下文",
            question="测试问题",
            history="用户: 你好\n助手: 你好"
        )
        assert "测试上下文" in formatted
        assert "测试问题" in formatted
        assert "用户: 你好" in formatted

    def test_retrieve_context_vector_only(self, mock_rag_chain):
        """测试纯向量检索"""
        mock_docs = [
            Document(page_content="测试文档1", metadata={"id": "1"}),
            Document(page_content="测试文档2", metadata={"id": "2"}),
        ]
        mock_rag_chain.vector_db.similarity_search.return_value = mock_docs

        results = mock_rag_chain.retrieve_context("测试查询", k=2)
        assert len(results) == 2
        mock_rag_chain.vector_db.similarity_search.assert_called_once()

    def test_retrieve_context_with_k(self, mock_rag_chain):
        """测试检索 k 参数"""
        mock_docs = [Document(page_content=f"文档{i}", metadata={}) for i in range(10)]
        mock_rag_chain.vector_db.similarity_search.return_value = mock_docs

        results = mock_rag_chain.retrieve_context("测试查询", k=3)
        assert len(results) == 3

    def test_query_returns_dict(self, mock_rag_chain):
        """测试 query 方法返回正确格式"""
        mock_docs = [Document(page_content="相关文档内容", metadata={"filename": "test.txt"})]
        mock_rag_chain.vector_db.similarity_search.return_value = mock_docs

        with patch.object(mock_rag_chain, 'generate_answer', return_value="这是一个测试答案"):
            result = mock_rag_chain.query("测试问题", k=3)

            assert isinstance(result, dict)
            assert 'answer' in result
            assert 'sources' in result
            assert 'context_count' in result
            assert result['answer'] == "这是一个测试答案"
            assert result['context_count'] == 1

    def test_query_formats_history(self, mock_rag_chain):
        """测试对话历史格式化"""
        history = [
            {"role": "user", "content": "第一个问题"},
            {"role": "assistant", "content": "第一个回答"},
        ]

        mock_docs = [Document(page_content="测试", metadata={})]
        mock_rag_chain.vector_db.similarity_search.return_value = mock_docs

        with patch.object(mock_rag_chain, 'generate_answer') as mock_gen:
            mock_gen.return_value = "答案"
            mock_rag_chain.query("第二个问题", k=3, history=history)

            # 验证 generate_answer 被调用时传入了格式化的历史
            call_args = mock_gen.call_args
            history_arg = call_args[0][2]  # 第三个位置参数
            assert "第一个问题" in history_arg

    def test_query_truncates_long_history(self, mock_rag_chain):
        """测试长对话历史截断（最近10轮=20条消息）"""
        history = []
        for i in range(30):  # 30轮对话 = 60条消息
            history.append({"role": "user", "content": f"问题{i}"})
            history.append({"role": "assistant", "content": f"回答{i}"})

        mock_docs = [Document(page_content="测试", metadata={})]
        mock_rag_chain.vector_db.similarity_search.return_value = mock_docs

        with patch.object(mock_rag_chain, 'generate_answer') as mock_gen:
            mock_gen.return_value = "答案"
            mock_rag_chain.query("最新问题", k=3, history=history)

            call_args = mock_gen.call_args
            history_arg = call_args[0][2]
            # 只有最近 10 轮（20 条消息）
            assert "问题0" not in history_arg  # 最早的应该被截断
            assert "问题29" in history_arg     # 最新的应该保留

    def test_query_error_handling(self, mock_rag_chain):
        """测试查询异常处理"""
        mock_rag_chain.vector_db.similarity_search.side_effect = Exception("数据库连接失败")

        result = mock_rag_chain.query("测试问题")
        assert 'answer' in result
        assert "查询处理失败" in result['answer']
        assert result['context_count'] == 0

    def test_mock_response_format(self, mock_rag_chain):
        """测试模拟响应格式"""
        response = mock_rag_chain._mock_response("什么是AI？", "人工智能是...")

        assert "什么是AI？" in response or "人工智能是" in response
        assert isinstance(response, str)
        assert len(response) > 0
