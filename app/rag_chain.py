"""
RAG链 - 检索增强生成（使用阿里通义千问）
"""
from typing import List, Dict
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
from app.vector_db import VectorDatabase
import sys
sys.path.append('..')
from config.settings import LLM_MODEL_NAME, LLM_API_KEY, LLM_TEMPERATURE, LLM_MAX_TOKENS


class RAGChain:
    """RAG问答链"""
    
    def __init__(self):
        """初始化RAG链"""
        self.vector_db = VectorDatabase()
        self.vector_db.initialize()
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
        template = """你是一个专业的知识库助手。请根据以下提供的上下文信息回答问题。
如果上下文中没有足够的信息来回答问题，请诚实地说你不知道。

上下文信息：
{context}

问题：{question}

请提供详细、准确的回答："""
        
        return PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )
    
    def retrieve_context(self, query: str, k: int = 5) -> List[Document]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            k: 返回的文档数量
            
        Returns:
            相关文档列表
        """
        return self.vector_db.similarity_search(query, k=k)
    
    def generate_answer(self, question: str, context: List[Document]) -> str:
        """
        基于上下文生成答案
        
        Args:
            question: 问题
            context: 上下文文档列表
            
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
                question=question
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
    
    def query(self, question: str, k: int = 5) -> Dict:
        """
        完整的RAG查询流程
        
        Args:
            question: 用户问题
            k: 检索的文档数量
            
        Returns:
            包含答案和上下文的字典
        """
        try:
            # 检索相关文档
            context_docs = self.retrieve_context(question, k=k)
            
            # 生成答案
            answer = self.generate_answer(question, context_docs)
            
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
