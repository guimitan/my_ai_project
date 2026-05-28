"""
重排序器 - 使用CrossEncoder对检索结果进行精排
"""
from typing import List, Tuple
from langchain_core.documents import Document
import numpy as np


class CrossEncoderReranker:
    """基于CrossEncoder的重排序器"""
    
    def __init__(self, model_name: str = "cross-encoder"):
        """
        初始化重排序器
        
        Args:
            model_name: 模型名称（预留参数，未来可接入真实的CrossEncoder模型）
        """
        self.model_name = model_name
        self._model = None
        print(f"⚠️ CrossEncoder重排序器已初始化（当前使用模拟排序）")
        print(f"   提示：如需使用真实模型，请安装 sentence-transformers 库")
    
    def rerank(
        self, 
        query: str, 
        documents: List[Document], 
        top_k: int = 5
    ) -> List[Document]:
        """
        对检索结果进行重排序
        
        Args:
            query: 查询文本
            documents: 待重排序的文档列表
            top_k: 返回的文档数量
            
        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []
        
        try:
            # 尝试使用真实的CrossEncoder模型
            if self._model is None:
                self._load_model()
            
            if self._model is not None:
                # 使用真实模型进行重排序
                return self._rerank_with_model(query, documents, top_k)
            else:
                # 降级到启发式重排序
                print("⚠️ 使用启发式重排序（未加载CrossEncoder模型）")
                return self._heuristic_rerank(query, documents, top_k)
                
        except Exception as e:
            print(f"⚠️ 重排序失败: {str(e)}，使用原始顺序")
            return documents[:top_k]
    
    def _load_model(self):
        """加载CrossEncoder模型"""
        try:
            from sentence_transformers import CrossEncoder
            # 使用中文优化的CrossEncoder模型
            self._model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            print(f"✅ CrossEncoder模型加载成功: {self.model_name}")
        except ImportError:
            print("⚠️ 未安装 sentence-transformers，将使用启发式重排序")
            print("   安装命令: pip install sentence-transformers")
            self._model = None
        except Exception as e:
            print(f"⚠️ 模型加载失败: {str(e)}")
            self._model = None
    
    def _rerank_with_model(
        self, 
        query: str, 
        documents: List[Document], 
        top_k: int
    ) -> List[Document]:
        """
        使用CrossEncoder模型进行重排序
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回数量
            
        Returns:
            重排序后的文档列表
        """
        # 构建查询-文档对
        pairs = [(query, doc.page_content) for doc in documents]
        
        # 计算相关性分数
        scores = self._model.predict(pairs)
        
        # 按分数排序
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # 更新文档元数据中的分数
        for doc, score in scored_docs:
            doc.metadata['reranker_score'] = float(score)
        
        # 返回Top-K
        return [doc for doc, score in scored_docs[:top_k]]
    
    def _heuristic_rerank(
        self, 
        query: str, 
        documents: List[Document], 
        top_k: int
    ) -> List[Document]:
        """
        启发式重排序（当没有CrossEncoder模型时使用）
        
        基于以下因素：
        1. 查询词匹配度
        2. 文档长度合理性
        3. 关键词密度
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回数量
            
        Returns:
            重排序后的文档列表
        """
        import jieba
        
        # 对查询进行分词
        query_tokens = set(jieba.cut(query))
        query_tokens = {t.strip() for t in query_tokens if t.strip() and len(t.strip()) > 1}
        
        scored_docs = []
        
        for doc in documents:
            content = doc.page_content
            
            # 1. 计算查询词匹配分数
            doc_tokens = set(jieba.cut(content))
            doc_tokens = {t.strip() for t in doc_tokens if t.strip() and len(t.strip()) > 1}
            
            if len(query_tokens) > 0:
                match_score = len(query_tokens & doc_tokens) / len(query_tokens)
            else:
                match_score = 0.0
            
            # 2. 计算关键词密度
            keyword_density = sum(
                content.count(token) for token in query_tokens
            ) / max(len(content), 1)
            
            # 3. 文档长度惩罚（避免过长或过短的文档）
            content_length = len(content)
            if content_length < 50:
                length_penalty = 0.5
            elif content_length > 2000:
                length_penalty = 0.7
            else:
                length_penalty = 1.0
            
            # 综合分数
            final_score = (
                0.5 * match_score + 
                0.3 * min(keyword_density * 10, 1.0) + 
                0.2 * length_penalty
            )
            
            # 更新元数据
            doc.metadata['reranker_score'] = float(final_score)
            doc.metadata['match_score'] = float(match_score)
            doc.metadata['keyword_density'] = float(keyword_density)
            
            scored_docs.append((doc, final_score))
        
        # 按分数排序
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in scored_docs[:top_k]]


class RerankerFactory:
    """重排序器工厂类"""
    
    @staticmethod
    def create_reranker(reranker_type: str = "cross_encoder", **kwargs):
        """
        创建重排序器实例
        
        Args:
            reranker_type: 重排序器类型
                - "cross_encoder": 使用CrossEncoder模型
                - "heuristic": 使用启发式方法
                - "none": 不重排序
            **kwargs: 其他参数
            
        Returns:
            重排序器实例
        """
        if reranker_type == "none":
            return None
        
        if reranker_type == "heuristic":
            # 创建一个只使用启发式方法的实例
            reranker = CrossEncoderReranker()
            reranker._model = None  # 强制不使用模型
            return reranker
        
        # 默认使用CrossEncoder（如果可用则自动加载，否则降级到启发式）
        return CrossEncoderReranker(**kwargs)
