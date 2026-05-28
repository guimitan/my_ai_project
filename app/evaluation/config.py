"""
评估系统配置
"""
import os
from pathlib import Path

# 评估系统根目录
EVALUATION_DIR = Path(__file__).parent.parent.parent / "data" / "evaluation"

# 测试数据集目录
TEST_DATASET_DIR = EVALUATION_DIR / "test_dataset"

# 实验结果存储目录
EXPERIMENTS_DIR = EVALUATION_DIR / "experiments"

# 数据库路径
EXPERIMENTS_DB_PATH = str(EVALUATION_DIR / "experiments.db")

# 确保目录存在
TEST_DATASET_DIR.mkdir(parents=True, exist_ok=True)
EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

# 评估配置
DEFAULT_K = 5  # 默认检索数量
EVALUATION_BATCH_SIZE = 10  # 批量评估大小

# LLM评估配置
FAITHFULNESS_WEIGHT = 0.4  # 忠实度权重
RELEVANCE_WEIGHT = 0.4  # 相关性权重
COMPLETENESS_WEIGHT = 0.2  # 完整性权重

# 相似度阈值
SIMILARITY_THRESHOLD_LOW = 0.5
SIMILARITY_THRESHOLD_HIGH = 0.8
