"""
项目配置文件
"""
import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 数据目录
DATA_DIR = ROOT_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

# 确保目录存在
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

# 向量数据库配置
CHROMA_DB_PATH = str(VECTOR_STORE_DIR / "chroma_db")
COLLECTION_NAME = "jie_rag_collection"

# 文本分割配置
CHUNK_SIZE = 1000  # 每个文本块的大小
CHUNK_OVERLAP = 200  # 文本块之间的重叠

# 嵌入模型配置
# 使用阿里通义千问嵌入模型
EMBEDDING_MODEL_NAME = "text-embedding-v3"  # 阿里嵌入模型
EMBEDDING_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")  # 从环境变量获取API Key

# LLM配置 - 使用阿里通义千问
LLM_MODEL_NAME = "qwen-plus"  # 可选: qwen-turbo, qwen-plus, qwen-max
LLM_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")  # 从环境变量获取API Key
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 1000

# OCR配置 - 使用阿里云OCR服务
OCR_ENABLED = True  # 是否启用OCR功能
OCR_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")  # 使用相同的API Key
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
