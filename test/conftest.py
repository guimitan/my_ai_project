"""
Pytest 共享 fixtures 和配置
"""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

# 确保项目根目录在 Python 路径中
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def mock_dashscope_api():
    """自动 mock DashScope API 调用，避免测试时需要真实 API Key"""
    with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-api-key-for-testing"}):
        yield


@pytest.fixture
def sample_documents():
    """创建示例 LangChain Document 列表"""
    docs = [
        Document(
            page_content="人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
            metadata={"source": "doc1.txt", "filename": "ai_intro.txt"}
        ),
        Document(
            page_content="机器学习是人工智能的子领域，通过数据和经验自动改进算法。深度学习使用多层神经网络。",
            metadata={"source": "doc2.txt", "filename": "ml_intro.txt"}
        ),
        Document(
            page_content="自然语言处理（NLP）是AI的重要应用领域，包括文本分类、情感分析、机器翻译等任务。",
            metadata={"source": "doc3.txt", "filename": "nlp_intro.txt"}
        ),
        Document(
            page_content="RAG（检索增强生成）结合了信息检索和文本生成技术，提高大语言模型回答的准确性。",
            metadata={"source": "doc4.txt", "filename": "rag_intro.txt"}
        ),
        Document(
            page_content="ChromaDB是一个开源的向量数据库，专为LLM应用设计，支持高效的语义搜索。",
            metadata={"source": "doc5.txt", "filename": "chroma_intro.txt"}
        ),
    ]
    return docs


@pytest.fixture
def sample_query():
    """示例查询文本"""
    return "什么是人工智能？"


@pytest.fixture
def sample_history():
    """示例对话历史"""
    return [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
    ]
