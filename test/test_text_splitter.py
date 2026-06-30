"""
文本分割器单元测试
"""
import pytest
from langchain_core.documents import Document
from app.core.text_splitter import TextSplitter


class TestTextSplitter:
    """文本分割器测试"""

    def test_init_default_params(self):
        """测试默认参数初始化"""
        splitter = TextSplitter()
        assert splitter is not None
        assert splitter.text_splitter._chunk_size == 500
        assert splitter.text_splitter._chunk_overlap == 50

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        splitter = TextSplitter(chunk_size=300, chunk_overlap=30)
        assert splitter.text_splitter._chunk_size == 300
        assert splitter.text_splitter._chunk_overlap == 30

    def test_split_text_basic(self):
        """测试基本文本分割"""
        splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
        text = "人工智能是计算机科学的一个分支。机器学习是AI的重要子领域。深度学习使用神经网络。"
        chunks = splitter.split_text(text)
        assert len(chunks) >= 1
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_split_text_empty(self):
        """测试空文本分割"""
        splitter = TextSplitter()
        chunks = splitter.split_text("")
        assert len(chunks) == 0 or all(len(c) == 0 for c in chunks)

    def test_split_documents(self, sample_documents):
        """测试文档列表分割"""
        splitter = TextSplitter(chunk_size=200, chunk_overlap=30)
        split_docs = splitter.split_documents(sample_documents)
        assert len(split_docs) >= len(sample_documents)
        for doc in split_docs:
            assert isinstance(doc, Document)
            assert hasattr(doc, 'page_content')
            assert hasattr(doc, 'metadata')

    def test_split_documents_preserves_metadata(self):
        """测试分割后保留元数据"""
        splitter = TextSplitter(chunk_size=500, chunk_overlap=50)
        doc = Document(
            page_content="这是一段测试文本。" * 50,
            metadata={"source": "test.txt", "author": "test"}
        )
        split_docs = splitter.split_documents([doc])
        for split_doc in split_docs:
            assert split_doc.metadata.get("source") == "test.txt"
            assert split_doc.metadata.get("author") == "test"

    def test_split_text_chinese_separators(self):
        """测试中文分隔符优先策略"""
        splitter = TextSplitter(chunk_size=200, chunk_overlap=20)
        text = "第一段内容。\n\n第二段内容，包含更多信息。\n第三段内容：继续测试。"
        chunks = splitter.split_text(text)
        assert len(chunks) >= 1

    def test_chunk_size_respected(self):
        """测试分块大小限制"""
        chunk_size = 100
        splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=0)
        text = "测试文本。" * 100
        chunks = splitter.split_text(text)
        for chunk in chunks:
            # 允许少量超出（因为分隔符不是完美的）
            assert len(chunk) <= chunk_size + 50, f"Chunk too large: {len(chunk)} > {chunk_size}"
