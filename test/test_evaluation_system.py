"""
评估系统快速测试脚本
验证所有模块是否可以正常导入和运行
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """测试所有模块的导入"""
    print("=" * 60)
    print("测试1: 模块导入")
    print("=" * 60)
    
    try:
        from app.evaluation.config import TEST_DATASET_DIR, DEFAULT_K
        print("✅ config.py 导入成功")
        print(f"   - 测试数据集目录: {TEST_DATASET_DIR}")
        print(f"   - 默认检索数量: {DEFAULT_K}")
    except Exception as e:
        print(f"❌ config.py 导入失败: {e}")
        return False
    
    try:
        from app.evaluation.dataset_manager import TestDatasetManager
        print("✅ dataset_manager.py 导入成功")
    except Exception as e:
        print(f"❌ dataset_manager.py 导入失败: {e}")
        return False
    
    try:
        from app.evaluation.retrieval_evaluator import RetrievalEvaluator
        print("✅ retrieval_evaluator.py 导入成功")
    except Exception as e:
        print(f"❌ retrieval_evaluator.py 导入失败: {e}")
        return False
    
    try:
        from app.evaluation.generation_evaluator import GenerationEvaluator
        print("✅ generation_evaluator.py 导入成功")
    except Exception as e:
        print(f"❌ generation_evaluator.py 导入失败: {e}")
        return False
    
    try:
        from app.evaluation.experiment_tracker import ExperimentTracker
        print("✅ experiment_tracker.py 导入成功")
    except Exception as e:
        print(f"❌ experiment_tracker.py 导入失败: {e}")
        return False
    
    try:
        from app.evaluation.evaluation_runner import EvaluationRunner
        print("✅ evaluation_runner.py 导入成功")
    except Exception as e:
        print(f"❌ evaluation_runner.py 导入失败: {e}")
        return False
    
    print("\n✅ 所有模块导入成功！\n")
    return True


def test_dataset_manager():
    """测试数据集管理器"""
    print("=" * 60)
    print("测试2: 数据集管理器")
    print("=" * 60)
    
    try:
        from app.evaluation.dataset_manager import TestDatasetManager
        
        manager = TestDatasetManager("test_cases")
        test_cases = manager.get_all_test_cases()
        
        print(f"✅ 加载测试用例: {len(test_cases)} 个")
        
        if len(test_cases) > 0:
            stats = manager.get_statistics()
            print(f"   - 类别分布: {stats['categories']}")
            print(f"   - 难度分布: {stats['difficulties']}")
            
            # 显示第一个测试用例
            first_case = test_cases[0]
            print(f"\n示例测试用例:")
            print(f"   ID: {first_case.test_id}")
            print(f"   问题: {first_case.question[:50]}...")
            print(f"   类别: {first_case.category}")
            print(f"   难度: {first_case.difficulty}")
        
        print("\n✅ 数据集管理器测试通过！\n")
        return True
        
    except Exception as e:
        print(f"❌ 数据集管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_experiment_tracker():
    """测试实验追踪器"""
    print("=" * 60)
    print("测试3: 实验追踪器")
    print("=" * 60)
    
    try:
        from app.evaluation.experiment_tracker import ExperimentTracker
        
        tracker = ExperimentTracker()
        
        # 创建测试实验
        config = {"test_param": 123}
        exp_id = tracker.create_experiment(config, "测试实验")
        print(f"✅ 创建实验: {exp_id}")
        
        # 查询实验
        exp_info = tracker.get_experiment(exp_id)
        if exp_info:
            print(f"✅ 查询实验成功")
            print(f"   - 配置: {exp_info['config']}")
            print(f"   - 描述: {exp_info['description']}")
        
        # 列出实验
        experiments = tracker.list_experiments(limit=5)
        print(f"✅ 实验列表: {len(experiments)} 个实验")
        
        # 清理测试实验
        tracker.delete_experiment(exp_id)
        print(f"✅ 已清理测试实验")
        
        print("\n✅ 实验追踪器测试通过！\n")
        return True
        
    except Exception as e:
        print(f"❌ 实验追踪器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retrieval_evaluator_initialization():
    """测试检索评估器初始化"""
    print("=" * 60)
    print("测试4: 检索评估器初始化")
    print("=" * 60)
    
    try:
        from app.evaluation.retrieval_evaluator import RetrievalEvaluator
        
        print("正在初始化检索评估器...")
        evaluator = RetrievalEvaluator()
        
        print("✅ 检索评估器初始化成功")
        print(f"   - RAG链: {evaluator.rag_chain is not None}")
        print(f"   - 向量数据库: {evaluator.rag_chain.vector_db is not None}")
        
        print("\n✅ 检索评估器测试通过！\n")
        return True
        
    except Exception as e:
        print(f"❌ 检索评估器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("   RAG检索质量评估系统 - 快速测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 测试1: 模块导入
    results.append(("模块导入", test_imports()))
    
    # 测试2: 数据集管理器
    results.append(("数据集管理器", test_dataset_manager()))
    
    # 测试3: 实验追踪器
    results.append(("实验追踪器", test_experiment_tracker()))
    
    # 测试4: 检索评估器初始化
    results.append(("检索评估器初始化", test_retrieval_evaluator_initialization()))
    
    # 汇总结果
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统可以正常使用。")
        print("\n下一步:")
        print("1. 运行评估: python -m app.evaluation.evaluation_runner --mode retrieval --k 5")
        print("2. 启动Dashboard: streamlit run app/evaluation/dashboard.py")
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息。")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
