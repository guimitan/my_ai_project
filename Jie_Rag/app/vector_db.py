"""
向量数据库 - 使用ChromaDB存储和检索向量
"""
from typing import List, Optional
try:
    # LangChain 0.2+ / 1.x 的新导入路径
    from langchain_chroma import Chroma
except ImportError:
    # 旧版本的导入路径
    from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
import sys
sys.path.append('..')
from config.settings import CHROMA_DB_PATH, COLLECTION_NAME
from app.embedding import EmbeddingModel


class LangChainEmbeddings(Embeddings):
    """LangChain embeddings适配器，包装阿里嵌入模型"""
    
    def __init__(self, embedding_model: EmbeddingModel):
        """
        初始化适配器
        
        Args:
            embedding_model: 阿里嵌入模型实例
        """
        self.embedding_model = embedding_model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        嵌入文档列表
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        return self.embedding_model.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """
        嵌入查询文本
        
        Args:
            text: 查询文本
            
        Returns:
            嵌入向量
        """
        return self.embedding_model.embed_query(text)


class VectorDatabase:
    """向量数据库封装类"""
    
    def __init__(self, persist_directory: str = CHROMA_DB_PATH, 
                 collection_name: str = COLLECTION_NAME):
        """
        初始化向量数据库
        
        Args:
            persist_directory: 数据库持久化目录
            collection_name: 集合名称
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.vectorstore = None
    
    def initialize(self):
        """初始化或加载向量数据库"""
        try:
            # 创建LangChain兼容的embeddings对象
            embedding_model = EmbeddingModel()
            lc_embeddings = LangChainEmbeddings(embedding_model)
            
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=lc_embeddings,
                persist_directory=self.persist_directory
            )
        except Exception as e:
            raise Exception(f"初始化向量数据库失败: {str(e)}")
    
    def add_documents(self, documents: List[Document]):
        """
        添加文档到向量数据库
        
        Args:
            documents: 文档列表
        """
        if self.vectorstore is None:
            self.initialize()
        
        try:
            self.vectorstore.add_documents(documents)

        except Exception as e:
            raise Exception(f"添加文档到向量数据库失败: {str(e)}")
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """
        相似性搜索
        
        Args:
            query: 查询文本
            k: 返回的最相似文档数量
            
        Returns:
            相似文档列表
        """
        if self.vectorstore is None:
            self.initialize()
        
        try:
            results = self.vectorstore.similarity_search(query, k=k)
            return results
        except Exception as e:
            raise Exception(f"相似性搜索失败: {str(e)}")
    
    def similarity_search_with_score(self, query: str, k: int = 5):
        """
        带分数的相似性搜索
        
        Args:
            query: 查询文本
            k: 返回的最相似文档数量
            
        Returns:
            (文档, 分数) 列表
        """
        if self.vectorstore is None:
            self.initialize()
        
        try:
            results = self.vectorstore.similarity_search_with_relevance_scores(query, k=k)
            return results
        except Exception as e:
            raise Exception(f"带分数的相似性搜索失败: {str(e)}")
    
    def delete_collection(self):
        """删除当前集合"""
        if self.vectorstore is None:
            self.initialize()
        
        try:
            self.vectorstore.delete_collection()
        except Exception as e:
            raise Exception(f"删除集合失败: {str(e)}")
    
    def get_document_count(self) -> int:
        """
        获取文档数量
        
        Returns:
            文档数量
        """
        if self.vectorstore is None:
            self.initialize()
        
        try:
            return self.vectorstore._collection.count()
        except Exception as e:
            raise Exception(f"获取文档数量失败: {str(e)}")
