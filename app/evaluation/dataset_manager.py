"""
测试数据集管理器
负责测试用例的加载、保存和管理
"""
import json
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from app.evaluation.config import TEST_DATASET_DIR


class TestCase:
    """测试用例数据类"""
    
    def __init__(
        self,
        test_id: str,
        question: str,
        category: str = "通用",
        difficulty: str = "medium",
        relevant_doc_ids: List[str] = None,
        expected_keywords: List[str] = None,
        notes: str = ""
    ):
        self.test_id = test_id
        self.question = question
        self.category = category
        self.difficulty = difficulty
        self.relevant_doc_ids = relevant_doc_ids or []
        self.expected_keywords = expected_keywords or []
        self.notes = notes
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.test_id,
            "question": self.question,
            "category": self.category,
            "difficulty": self.difficulty,
            "relevant_doc_ids": self.relevant_doc_ids,
            "expected_keywords": self.expected_keywords,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TestCase':
        """从字典创建"""
        return cls(
            test_id=data["id"],
            question=data["question"],
            category=data.get("category", "通用"),
            difficulty=data.get("difficulty", "medium"),
            relevant_doc_ids=data.get("relevant_doc_ids", []),
            expected_keywords=data.get("expected_keywords", []),
            notes=data.get("notes", "")
        )


class TestDatasetManager:
    """测试数据集管理器"""
    
    def __init__(self, dataset_name: str = "test_cases"):
        """
        初始化数据集管理器
        
        Args:
            dataset_name: 数据集名称（对应JSON文件名）
        """
        self.dataset_name = dataset_name
        self.dataset_path = TEST_DATASET_DIR / f"{dataset_name}.json"
        self.test_cases: List[TestCase] = []
        self.version = "1.0"
        self.created_at = ""
        
        # 如果文件存在，加载数据
        if self.dataset_path.exists():
            self.load_dataset()
    
    def load_dataset(self):
        """加载数据集"""
        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.version = data.get("version", "1.0")
            self.created_at = data.get("created_at", "")
            
            self.test_cases = [
                TestCase.from_dict(tc) 
                for tc in data.get("test_cases", [])
            ]
            
            print(f"✅ 成功加载数据集: {len(self.test_cases)} 个测试用例")
            
        except Exception as e:
            print(f"⚠️ 加载数据集失败: {str(e)}")
            self.test_cases = []
    
    def save_dataset(self):
        """保存数据集"""
        try:
            data = {
                "version": self.version,
                "created_at": self.created_at or datetime.now().strftime("%Y-%m-%d"),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "test_cases": [tc.to_dict() for tc in self.test_cases]
            }
            
            with open(self.dataset_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 数据集已保存: {len(self.test_cases)} 个测试用例")
            
        except Exception as e:
            raise Exception(f"保存数据集失败: {str(e)}")
    
    def add_test_case(self, test_case: TestCase):
        """
        添加测试用例
        
        Args:
            test_case: 测试用例对象
        """
        self.test_cases.append(test_case)
    
    def add_test_case_from_dict(self, data: Dict):
        """
        从字典添加测试用例
        
        Args:
            data: 测试用例字典
        """
        test_case = TestCase.from_dict(data)
        self.add_test_case(test_case)
    
    def remove_test_case(self, test_id: str) -> bool:
        """
        删除测试用例
        
        Args:
            test_id: 测试用例ID
            
        Returns:
            是否成功删除
        """
        original_count = len(self.test_cases)
        self.test_cases = [tc for tc in self.test_cases if tc.test_id != test_id]
        
        if len(self.test_cases) < original_count:
            print(f"✅ 已删除测试用例: {test_id}")
            return True
        else:
            print(f"⚠️ 未找到测试用例: {test_id}")
            return False
    
    def get_test_case(self, test_id: str) -> Optional[TestCase]:
        """
        获取单个测试用例
        
        Args:
            test_id: 测试用例ID
            
        Returns:
            测试用例对象或None
        """
        for tc in self.test_cases:
            if tc.test_id == test_id:
                return tc
        return None
    
    def get_all_test_cases(self) -> List[TestCase]:
        """获取所有测试用例"""
        return self.test_cases
    
    def filter_by_category(self, category: str) -> List[TestCase]:
        """
        按类别筛选测试用例
        
        Args:
            category: 类别名称
            
        Returns:
            筛选后的测试用例列表
        """
        return [tc for tc in self.test_cases if tc.category == category]
    
    def filter_by_difficulty(self, difficulty: str) -> List[TestCase]:
        """
        按难度筛选测试用例
        
        Args:
            difficulty: 难度级别 (easy/medium/hard)
            
        Returns:
            筛选后的测试用例列表
        """
        return [tc for tc in self.test_cases if tc.difficulty == difficulty]
    
    def get_statistics(self) -> Dict:
        """
        获取数据集统计信息
        
        Returns:
            统计信息字典
        """
        categories = {}
        difficulties = {}
        
        for tc in self.test_cases:
            categories[tc.category] = categories.get(tc.category, 0) + 1
            difficulties[tc.difficulty] = difficulties.get(tc.difficulty, 0) + 1
        
        return {
            "total_cases": len(self.test_cases),
            "categories": categories,
            "difficulties": difficulties,
            "version": self.version,
            "created_at": self.created_at
        }
    
    def create_sample_dataset(self):
        """创建示例数据集（用于快速开始）"""
        sample_cases = [
            {
                "id": "tc_001",
                "question": "如何处理PDF文档中的表格数据？",
                "category": "技术操作",
                "difficulty": "medium",
                "relevant_doc_ids": [],  # 需要实际运行后填充
                "expected_keywords": ["表格", "OCR", "解析"],
                "notes": "用户常见技术问题"
            },
            {
                "id": "tc_002",
                "question": "系统的向量数据库使用的是什么？",
                "category": "技术架构",
                "difficulty": "easy",
                "relevant_doc_ids": [],
                "expected_keywords": ["ChromaDB", "向量", "存储"],
                "notes": "技术架构相关问题"
            },
            {
                "id": "tc_003",
                "question": "文本分割的策略是什么？",
                "category": "技术实现",
                "difficulty": "medium",
                "relevant_doc_ids": [],
                "expected_keywords": ["分割", "chunk", "递归"],
                "notes": "核心实现细节"
            },
            {
                "id": "tc_004",
                "question": "如何上传图片并进行OCR识别？",
                "category": "功能使用",
                "difficulty": "easy",
                "relevant_doc_ids": [],
                "expected_keywords": ["图片", "OCR", "上传"],
                "notes": "基本功能操作"
            },
            {
                "id": "tc_005",
                "question": "RAG系统的完整工作流程是怎样的？",
                "category": "系统架构",
                "difficulty": "hard",
                "relevant_doc_ids": [],
                "expected_keywords": ["检索", "增强", "生成", "流程"],
                "notes": "综合性问题"
            }
        ]
        
        for case_data in sample_cases:
            self.add_test_case_from_dict(case_data)
        
        self.save_dataset()
        print(f"✅ 已创建示例数据集，包含 {len(sample_cases)} 个测试用例")


# 便捷函数
def load_dataset(dataset_name: str = "test_cases") -> TestDatasetManager:
    """
    加载数据集的便捷函数
    
    Args:
        dataset_name: 数据集名称
        
    Returns:
        TestDatasetManager实例
    """
    manager = TestDatasetManager(dataset_name)
    return manager


if __name__ == "__main__":
    # 测试代码
    manager = TestDatasetManager("test_cases")
    
    if len(manager.get_all_test_cases()) == 0:
        print("创建示例数据集...")
        manager.create_sample_dataset()
    
    # 显示统计信息
    stats = manager.get_statistics()
    print("\n===== 数据集统计 =====")
    print(f"总测试用例数: {stats['total_cases']}")
    print(f"类别分布: {stats['categories']}")
    print(f"难度分布: {stats['difficulties']}")
