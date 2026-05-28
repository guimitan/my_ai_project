"""
文档加载器 - 支持多种文档格式（包括图片OCR）
"""
from pathlib import Path
from typing import List
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_core.documents import Document
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import SUPPORTED_IMAGE_FORMATS
from app.core.image_ocr import ImageOCR


class DataLoader:
    """文档加载器，支持PDF、DOCX、TXT和图片格式"""
    
    def __init__(self):
        self.supported_extensions = {'.pdf', '.docx', '.txt'}
        self.image_extensions = SUPPORTED_IMAGE_FORMATS
        self.ocr = ImageOCR()
    
    def load_document(self, file_path: str) -> List[Document]:
        """
        加载单个文档（包括图片）
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            文档列表
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        # 检查是否为图片格式
        if extension in self.image_extensions:
            return self._load_image(file_path)
        
        # 传统文档格式
        if extension not in self.supported_extensions:
            raise ValueError(f"不支持的文件格式: {extension}")
        
        try:
            if extension == '.pdf':
                loader = PyPDFLoader(str(file_path))
            elif extension == '.docx':
                loader = Docx2txtLoader(str(file_path))
            elif extension == '.txt':
                loader = TextLoader(str(file_path), encoding='utf-8')
            else:
                raise ValueError(f"不支持的文件格式: {extension}")
            
            documents = loader.load()
            # 为每个文档添加元数据
            for doc in documents:
                doc.metadata['source'] = str(file_path)
                doc.metadata['filename'] = file_path.name
            
            return documents
        
        except Exception as e:
            raise Exception(f"加载文档失败: {str(e)}")
    
    def _load_image(self, image_path: Path) -> List[Document]:
        """
        加载图片并使用OCR识别文字
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            文档列表（包含OCR识别的文本）
        """
        try:
            # 使用OCR识别图片中的文字
            text_content = self.ocr.recognize_image(str(image_path))
            
            # 创建文档对象
            doc = Document(
                page_content=text_content,
                metadata={
                    'source': str(image_path),
                    'filename': image_path.name,
                    'type': 'image',
                    'format': image_path.suffix.lower()
                }
            )
            
            return [doc]
        
        except Exception as e:
            raise Exception(f"图片OCR识别失败: {str(e)}")
    
    def load_multiple_documents(self, file_paths: List[str]) -> List[Document]:
        """
        加载多个文档
        
        Args:
            file_paths: 文档文件路径列表
            
        Returns:
            文档列表
        """
        all_documents = []
        for file_path in file_paths:
            try:
                documents = self.load_document(file_path)
                all_documents.extend(documents)
            except Exception as e:
                print(f"警告: 加载文件 {file_path} 失败: {str(e)}")
                continue
        
        return all_documents
    
    def load_directory(self, directory_path: str) -> List[Document]:
        """
        加载目录下的所有支持的文档
        
        Args:
            directory_path: 目录路径
            
        Returns:
            文档列表
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"目录不存在: {directory_path}")
        
        file_paths = []
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                file_paths.append(str(file_path))
        
        return self.load_multiple_documents(file_paths)
