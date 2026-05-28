"""
混合检索器 - 结合向量检索和BM25关键词检索
"""
from typing import List, Dict, Tuple
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
import numpy as np
import jieba
from app.core.vector_db import VectorDatabase


class BM25Retriever:
    """BM25关键词检索器"""
    
    def __init__(self):
        """初始化BM25检索器"""
        self.bm25 = None
        self.documents = []
        self.doc_mapping = {}  # 映射索引到文档
        
    def build_index(self, documents: List[Document]):
        """
        构建BM25索引
        
        Args:
            documents: 文档列表
        """
        self.documents = documents
        self.doc_mapping = {i: doc for i, doc in enumerate(documents)}
        
        # 对文档进行分词
        tokenized_docs = []
        for doc in documents:
            # 使用jieba进行中文分词
            tokens = list(jieba.cut(doc.page_content))
            # 过滤掉空格和标点符号
            tokens = [t.strip() for t in tokens if t.strip() and len(t.strip()) > 1]
            tokenized_docs.append(tokens)
        
        # 构建BM25索引
        self.bm25 = BM25Okapi(tokenized_docs)
        print(f"✅ BM25索引构建完成，共 {len(documents)} 个文档")
    
    def search(self, query: str, k: int = 10) -> List[Tuple[Document, float]]:
        """
        使用BM25搜索相关文档
        
        Args:
            query: 查询文本
            k: 返回的文档数量
            
        Returns:
            (文档, 分数) 列表，按分数降序排列
        """
        if self.bm25 is None:
            raise ValueError("BM25索引未构建，请先调用build_index()")
        
        # 对查询进行分词
        query_tokens = list(jieba.cut(query))
        query_tokens = [t.strip() for t in query_tokens if t.strip() and len(t.strip()) > 1]
        
        # 获取BM25分数
        scores = self.bm25.get_scores(query_tokens)
        
        # 获取Top-K的索引
        top_k_indices = np.argsort(scores)[::-1][:k]
        
        # 构建结果
        results = []
        for idx in top_k_indices:
            if scores[idx] > 0:  # 只返回有分数的文档
                doc = self.doc_mapping[idx]
                results.append((doc, float(scores[idx])))
        
        return results


class HybridRetriever:
    """混合检索器：结合向量检索和BM25关键词检索"""
    
    def __init__(self, vector_db: VectorDatabase = None):
        """
        初始化混合检索器
        
        Args:
            vector_db: 向量数据库实例，如果为None则自动创建
        """
        self.vector_db = vector_db or VectorDatabase()
        self.vector_db.initialize()
        self.bm25_retriever = BM25Retriever()
        self._is_bm25_built = False
    
    def build_bm25_index(self):
        """从向量数据库构建BM25索引"""
        try:
            # 从ChromaDB获取所有文档
            collection = self.vector_db.vectorstore._collection
            results = collection.get(include=['metadatas', 'documents'])
            
            if not results['ids']:
                print("⚠️ 向量数据库为空，无法构建BM25索引")
                return
            
            # 转换为LangChain Document对象
            documents = []
            for i, doc_id in enumerate(results['ids']):
                doc = Document(
                    page_content=results['documents'][i],
                    metadata=results['metadatas'][i] if results['metadatas'] else {}
                )
                documents.append(doc)
            
            # 构建BM25索引
            self.bm25_retriever.build_index(documents)
            self._is_bm25_built = True
            
        except Exception as e:
            print(f"❌ 构建BM25索引失败: {str(e)}")
            raise
    
    def retrieve(
        self, 
        query: str, 
        k: int = 10,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3
    ) -> List[Document]:
        """
        混合检索流程
        
        Args:
            query: 查询文本
            k: 返回的文档数量
            vector_weight: 向量检索权重
            bm25_weight: BM25检索权重
            
        Returns:
            排序后的文档列表
        """
        if not self._is_bm25_built:
            print("⚠️ BM25索引未构建，正在自动构建...")
            self.build_bm25_index()
        
        # 1. 向量检索
        vector_docs = self.vector_db.similarity_search_with_score(query, k=k*2)
        
        # 2. BM25检索
        bm25_results = self.bm25_retriever.search(query, k=k*2)
        
        # 3. 合并结果并去重
        merged_docs = self._merge_results(vector_docs, bm25_results)
        
        # 4. 加权融合排序
        ranked_docs = self._rank_fusion(
            merged_docs, 
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
            top_k=k
        )
        
        return ranked_docs
    
    def _merge_results(
        self, 
        vector_results: List,
        bm25_results: List[Tuple[Document, float]]
    ) -> Dict[str, Dict]:
        """
        合并向量检索和BM25检索结果
        
        Args:
            vector_results: 向量检索结果 (Document, score) 列表
            bm25_results: BM25检索结果 (Document, score) 列表
            
        Returns:
            合并后的文档字典，key为文档内容
        """
        merged = {}
        
        # 添加向量检索结果
        for doc, score in vector_results:
            content = doc.page_content
            if content not in merged:
                merged[content] = {
                    'document': doc,
                    'vector_score': score,
                    'bm25_score': 0.0
                }
            else:
                # 如果已存在，取更高的向量分数
                merged[content]['vector_score'] = max(merged[content]['vector_score'], score)
        
        # 添加BM25检索结果
        for doc, score in bm25_results:
            content = doc.page_content
            if content not in merged:
                merged[content] = {
                    'document': doc,
                    'vector_score': 0.0,
                    'bm25_score': score
                }
            else:
                # 如果已存在，取更高的BM25分数
                merged[content]['bm25_score'] = max(merged[content]['bm25_score'], score)
        
        return merged
    
    def _rank_fusion(
        self,
        merged_docs: Dict[str, Dict],
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
        top_k: int = 10
    ) -> List[Document]:
        """
        使用加权融合对合并结果进行排序
        
        Args:
            merged_docs: 合并后的文档字典
            vector_weight: 向量检索权重
            bm25_weight: BM25检索权重
            top_k: 返回的文档数量
            
        Returns:
            排序后的文档列表
        """
        # 归一化分数
        vector_scores = [info['vector_score'] for info in merged_docs.values()]
        bm25_scores = [info['bm25_score'] for info in merged_docs.values()]
        
        # 计算最大值用于归一化
        max_vector = max(vector_scores) if vector_scores else 1.0
        max_bm25 = max(bm25_scores) if bm25_scores else 1.0
        
        # 避免除以零
        max_vector = max_vector if max_vector > 0 else 1.0
        max_bm25 = max_bm25 if max_bm25 > 0 else 1.0
        
        # 计算加权分数
        scored_docs = []
        for content, info in merged_docs.items():
            normalized_vector = info['vector_score'] / max_vector
            normalized_bm25 = info['bm25_score'] / max_bm25
            
            # 加权融合
            final_score = (
                vector_weight * normalized_vector + 
                bm25_weight * normalized_bm25
            )
            
            scored_docs.append((info['document'], final_score))
        
        # 按最终分数排序
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # 返回Top-K文档
        return [doc for doc, score in scored_docs[:top_k]]
    
    def refresh_index(self):
        """刷新BM25索引（当向量数据库更新时调用）"""
        print("🔄 正在刷新BM25索引...")
        self.build_bm25_index()
        print("✅ BM25索引刷新完成")
