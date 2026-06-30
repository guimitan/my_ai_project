"""
向量数据库 - 使用ChromaDB存储和检索向量
"""
from typing import List, Optional
import json
from datetime import datetime
try:
    # LangChain 0.2+ / 1.x 的新导入路径
    from langchain_chroma import Chroma
except ImportError:
    # 旧版本的导入路径
    from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from config.settings import CHROMA_DB_PATH, COLLECTION_NAME
from app.core.embedding import EmbeddingModel


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
    
    def export_to_json(self, output_path: str = None, include_embeddings: bool = False) -> str:
        """
        将向量数据库中的所有文档导出为JSON文件
        
        Args:
            output_path: 输出文件路径，如果为None则自动生成
            include_embeddings: 是否包含向量嵌入（会增加文件大小）
            
        Returns:
            导出文件的完整路径
        """
        if self.vectorstore is None:
            self.initialize()
        
        try:
            # 获取所有文档数据
            collection = self.vectorstore._collection
            results = collection.get(
                include=['metadatas', 'documents'] + (['embeddings'] if include_embeddings else [])
            )
            
            # 构建导出数据结构
            export_data = {
                "export_info": {
                    "collection_name": self.collection_name,
                    "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_documents": len(results['ids']),
                    "include_embeddings": include_embeddings
                },
                "documents": []
            }
            
            # 遍历所有文档
            for i, doc_id in enumerate(results['ids']):
                doc_entry = {
                    "id": doc_id,
                    "content": results['documents'][i],
                    "metadata": results['metadatas'][i] if results['metadatas'] else {}
                }
                
                # 如果需要包含向量
                if include_embeddings and results.get('embeddings'):
                    doc_entry["embedding"] = results['embeddings'][i]
                
                export_data["documents"].append(doc_entry)
            
            # 确定输出路径
            if output_path is None:
                output_dir = Path(CHROMA_DB_PATH).parent
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(output_dir / f"vector_store_export_{timestamp}.json")
            
            # 写入JSON文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 成功导出 {len(results['ids'])} 个文档到: {output_path}")
            return output_path
            
        except Exception as e:
            raise Exception(f"导出JSON失败: {str(e)}")
    
    def get_all_documents(self) -> List[dict]:
        """
        获取所有文档的详细信息（不导出文件，直接返回数据）
        
        Returns:
            文档列表，每个文档包含id、content和metadata
        """
        if self.vectorstore is None:
            self.initialize()
        
        try:
            collection = self.vectorstore._collection
            results = collection.get(include=['metadatas', 'documents'])
            
            documents = []
            for i, doc_id in enumerate(results['ids']):
                documents.append({
                    "id": doc_id,
                    "content": results['documents'][i],
                    "metadata": results['metadatas'][i] if results['metadatas'] else {}
                })
            
            return documents
            
        except Exception as e:
            raise Exception(f"获取文档列表失败: {str(e)}")
