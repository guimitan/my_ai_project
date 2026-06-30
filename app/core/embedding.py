"""
嵌入模型 - 使用阿里通义千问嵌入模型
"""
from typing import List
import dashscope
from dashscope import TextEmbedding
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config.settings import EMBEDDING_MODEL_NAME, EMBEDDING_API_KEY


class EmbeddingModel:
    """阿里通义千问嵌入模型封装类"""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME, api_key: str = None):
        """
        初始化嵌入模型
        
        Args:
            model_name: 嵌入模型名称，默认text-embedding-v3
            api_key: API密钥，如果为None则从配置中获取
        """
        self.model_name = model_name
        self.api_key = api_key or EMBEDDING_API_KEY
        
        if not self.api_key:
            raise ValueError(
                "未找到API密钥！请设置环境变量 DASHSCOPE_API_KEY 或在配置文件中指定"
            )
        
        # 设置API密钥
        dashscope.api_key = self.api_key
    
    def get_embeddings(self):
        """
        获取嵌入模型实例（返回自身，用于LangChain兼容）
        
        Returns:
            嵌入模型实例
        """
        return self
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def embed_query(self, query: str) -> List[float]:
        """
        对查询文本进行嵌入（带自动重试）

        Args:
            query: 查询文本

        Returns:
            嵌入向量
        """
        response = TextEmbedding.call(
            model=self.model_name,
            input=query
        )

        if response.status_code == 200:
            return response.output['embeddings'][0]['embedding']
        else:
            raise Exception(f"嵌入失败: {response.message}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        对文档列表进行嵌入（带自动重试）

        Args:
            documents: 文档列表

        Returns:
            嵌入向量列表
        """
        # 批量处理，每次最多10个文档（阿里云API限制）
        batch_size = 10
        all_embeddings = []

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            response = TextEmbedding.call(
                model=self.model_name,
                input=batch
            )

            if response.status_code == 200:
                embeddings = [
                    item['embedding']
                    for item in response.output['embeddings']
                ]
                all_embeddings.extend(embeddings)
            else:
                raise Exception(f"批量嵌入失败: {response.message}")

        return all_embeddings
    
    def __call__(self, texts: List[str]) -> List[List[float]]:
        """
        使该类可调用，兼容LangChain接口
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        return self.embed_documents(texts)
