"""
RAG链 - 检索增强生成（使用阿里通义千问）
支持混合检索和重排序
"""
from typing import List, Dict, Optional
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
try:
    # 尝试新的导入路径（langchain 0.2+ / 1.x）
    from langchain_community.chat_models import ChatTongyi
    USE_CHAT_MODEL = True
except ImportError:
    # 回退到旧的导入路径
    from langchain_community.llms import Tongyi
    USE_CHAT_MODEL = False
from app.core.vector_db import VectorDatabase
from app.core.hybrid_retriever import HybridRetriever
from app.core.reranker import RerankerFactory
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import LLM_MODEL_NAME, LLM_API_KEY, LLM_TEMPERATURE, LLM_MAX_TOKENS


class RAGChain:
    """RAG问答链（支持混合检索和重排序）"""
    
    def __init__(
        self, 
        use_hybrid_retrieval: bool = True,
        use_reranker: bool = True,
        reranker_type: str = "cross_encoder"
    ):
        """
        初始化RAG链
        
        Args:
            use_hybrid_retrieval: 是否使用混合检索
            use_reranker: 是否使用重排序
            reranker_type: 重排序器类型 ("cross_encoder", "heuristic", "none")
        """
        self.vector_db = VectorDatabase()
        self.vector_db.initialize()
        
        # 初始化检索策略
        self.use_hybrid_retrieval = use_hybrid_retrieval
        if use_hybrid_retrieval:
            self.hybrid_retriever = HybridRetriever(self.vector_db)
            print("✅ 已启用混合检索（向量 + BM25）")
        else:
            self.hybrid_retriever = None
            print("ℹ️  使用纯向量检索")
        
        # 初始化重排序器
        self.use_reranker = use_reranker
        if use_reranker:
            self.reranker = RerankerFactory.create_reranker(reranker_type)
            if self.reranker:
                print(f"✅ 已启用重排序器 ({reranker_type})")
            else:
                print("ℹ️  重排序器未启用")
        else:
            self.reranker = None
            print("ℹ️  未启用重排序")
        
        self.llm = self._initialize_llm()
        self.prompt = self._create_prompt()
    
    def _initialize_llm(self):
        """
        初始化LLM模型（使用阿里通义千问）
        
        Returns:
            LLM实例
        """
        try:
            if not LLM_API_KEY:
                raise ValueError("未找到API密钥！请设置环境变量 DASHSCOPE_API_KEY")
            
            # 使用阿里通义千问作为LLM
            if USE_CHAT_MODEL:
                # 新版本使用ChatTongyi
                llm = ChatTongyi(
                    model=LLM_MODEL_NAME,
                    dashscope_api_key=LLM_API_KEY,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=LLM_MAX_TOKENS
                )
            else:
                # 旧版本使用Tongyi
                llm = Tongyi(
                    model=LLM_MODEL_NAME,
                    dashscope_api_key=LLM_API_KEY,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=LLM_MAX_TOKENS
                )
            return llm
        except Exception as e:
            print(f"警告: 无法初始化LLM，将使用模拟响应: {str(e)}")
            return None
    
    def _create_prompt(self):
        """
        创建提示模板
        
        Returns:
            提示模板
        """
        template = """你是一个专业的知识库助手。请根据以下提供的上下文信息和对话历史回答问题。
如果上下文中没有足够的信息来回答问题，请结合对话历史进行回答，或者诚实地说你不知道。

对话历史：
{history}

上下文信息：
{context}

当前问题：{question}

请提供详细、准确的回答："""
        
        return PromptTemplate(
            input_variables=["context", "question", "history"],
            template=template
        )
    
    def retrieve_context(
        self, 
        query: str, 
        k: int = 5,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3
    ) -> List[Document]:
        """
        检索相关文档（支持混合检索和重排序）
        
        Args:
            query: 查询文本
            k: 返回的文档数量
            vector_weight: 向量检索权重（仅混合检索时有效）
            bm25_weight: BM25检索权重（仅混合检索时有效）
            
        Returns:
            相关文档列表
        """
        # 1. 检索阶段
        if self.use_hybrid_retrieval and self.hybrid_retriever:
            # 使用混合检索
            retrieved_docs = self.hybrid_retriever.retrieve(
                query, 
                k=k*2,  # 召回更多文档用于重排序
                vector_weight=vector_weight,
                bm25_weight=bm25_weight
            )
        else:
            # 使用纯向量检索
            retrieved_docs = self.vector_db.similarity_search(query, k=k*2)
        
        # 2. 重排序阶段
        if self.use_reranker and self.reranker and len(retrieved_docs) > 0:
            reranked_docs = self.reranker.rerank(query, retrieved_docs, top_k=k)
            return reranked_docs
        else:
            # 不重排序，直接返回Top-K
            return retrieved_docs[:k]
    
    def generate_answer(self, question: str, context: List[Document], history: str = "") -> str:
        """
        基于上下文生成答案
        
        Args:
            question: 问题
            context: 上下文文档列表
            history: 格式化的对话历史字符串
            
        Returns:
            生成的答案
        """
        # 构建上下文文本
        context_text = "\n\n".join([doc.page_content for doc in context])
        
        # 如果没有LLM，返回模拟响应
        if self.llm is None:
            return self._mock_response(question, context_text)
        
        try:
            # 格式化提示
            formatted_prompt = self.prompt.format(
                context=context_text,
                question=question,
                history=history
            )
            
            # 生成回答（兼容ChatModel和LLM）
            if USE_CHAT_MODEL:
                # ChatModel需要使用HumanMessage包装
                from langchain_core.messages import HumanMessage
                response = self.llm.invoke([HumanMessage(content=formatted_prompt)])
                # ChatModel返回的是AIMessage对象，需要提取content
                answer = response.content if hasattr(response, 'content') else str(response)
            else:
                # 传统LLM直接调用
                answer = self.llm.invoke(formatted_prompt)
            
            return answer
        
        except Exception as e:
            return f"生成答案时出错: {str(e)}\n\n基于检索到的上下文，这里是一些相关信息：\n\n{context_text[:500]}..."
    
    def _mock_response(self, question: str, context: str) -> str:
        """
        模拟响应（当LLM不可用时）
        
        Args:
            question: 问题
            context: 上下文
            
        Returns:
            模拟的回答
        """
        return f"""基于检索到的知识库内容，我找到了以下相关信息：

{context[:800]}

注意：由于LLM服务未配置或不可用，以上显示的是检索到的原始上下文内容。
要获得更好的回答体验，请配置并启动Ollama服务。"""
    
    def query(
        self, 
        question: str, 
        k: int = 5, 
        history: List[Dict] = None,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3
    ) -> Dict:
        """
        完整的RAG查询流程
        
        Args:
            question: 用户问题
            k: 检索的文档数量
            history: 对话历史记录列表 [{'role': 'user', 'content': '...'}, ...]
            vector_weight: 向量检索权重
            bm25_weight: BM25检索权重
            
        Returns:
            包含答案和上下文的字典
        """
        try:
            # 1. 格式化历史记录
            history_text = ""
            if history:
                # 只取最近 5 轮对话，避免 Token 溢出
                recent_history = history[-10:] 
                history_parts = []
                for msg in recent_history:
                    role_name = "用户" if msg['role'] == 'user' else "助手"
                    history_parts.append(f"{role_name}: {msg['content']}")
                history_text = "\n".join(history_parts)

            # 2. 检索相关文档（使用混合检索和重排序）
            context_docs = self.retrieve_context(
                question, 
                k=k,
                vector_weight=vector_weight,
                bm25_weight=bm25_weight
            )
            
            # 3. 生成答案（传入历史记录）
            answer = self.generate_answer(question, context_docs, history_text)
            
            # 构建来源信息
            sources = []
            for doc in context_docs:
                source_info = {
                    'content': doc.page_content[:200] + '...',
                    'metadata': doc.metadata
                }
                sources.append(source_info)
            
            return {
                'answer': answer,
                'sources': sources,
                'context_count': len(context_docs)
            }
        
        except Exception as e:
            return {
                'answer': f"查询处理失败: {str(e)}",
                'sources': [],
                'context_count': 0
            }
