"""
文本分割器 - 将文档分割成小块
"""
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import sys
sys.path.append('..')
from config.settings import CHUNK_SIZE, CHUNK_OVERLAP


class TextSpliter:
    """文本分割器，使用递归字符分割方法"""
    
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        """
        初始化文本分割器
        
        Args:
            chunk_size: 每个文本块的大小
            chunk_overlap: 文本块之间的重叠
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", " ", ""]
        )
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        分割文档列表
        
        Args:
            documents: 文档列表
            
        Returns:
            分割后的文档列表
        """
        return self.text_splitter.split_documents(documents)
    
    def split_text(self, text: str) -> List[str]:
        """
        分割纯文本
        
        Args:
            text: 要分割的文本
            
        Returns:
            分割后的文本列表
        """
        return self.text_splitter.split_text(text)
