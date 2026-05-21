"""
系统测试脚本 - 验证各个组件是否正常工作
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """测试导入是否成功"""
    print("=" * 50)
    print("测试1: 检查模块导入")
    print("=" * 50)
    
    try:
        from config.settings import CHUNK_SIZE, EMBEDDING_MODEL_NAME
        print("✓ 配置模块导入成功")
        
        from app.data_loader import DataLoader
        print("✓ 数据加载器导入成功")
        
        from app.text_spliter import TextSpliter
        print("✓ 文本分割器导入成功")
        
        from app.embedding import EmbeddingModel
        print("✓ 嵌入模型导入成功")
        
        from app.vector_db import VectorDatabase
        print("✓ 向量数据库导入成功")
        
        from app.rag_chain import RAGChain
        print("✓ RAG链导入成功")
        
        print("\n✅ 所有模块导入成功！\n")
        return True
        
    except ImportError as e:
        print(f"\n❌ 模块导入失败: {str(e)}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt\n")
        return False


def test_config():
    """测试配置是否正确"""
    print("=" * 50)
    print("测试2: 检查配置")
    print("=" * 50)
    
    try:
        from config.settings import (
            ROOT_DIR, DATA_DIR, DOCUMENTS_DIR, 
            VECTOR_STORE_DIR, CHUNK_SIZE, CHUNK_OVERLAP
        )
        
        print(f"项目根目录: {ROOT_DIR}")
        print(f"数据目录: {DATA_DIR}")
        print(f"文档目录: {DOCUMENTS_DIR}")
        print(f"向量库目录: {VECTOR_STORE_DIR}")
        print(f"文本块大小: {CHUNK_SIZE}")
        print(f"文本块重叠: {CHUNK_OVERLAP}")
        
        # 检查目录是否存在
        if DOCUMENTS_DIR.exists():
            print("✓ 文档目录存在")
        else:
            print("✗ 文档目录不存在，正在创建...")
            DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
            
        if VECTOR_STORE_DIR.exists():
            print("✓ 向量库目录存在")
        else:
            print("✗ 向量库目录不存在，正在创建...")
            VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
        
        print("\n✅ 配置检查通过！\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 配置检查失败: {str(e)}\n")
        return False


def test_data_loader():
    """测试数据加载器"""
    print("=" * 50)
    print("测试3: 检查数据加载器")
    print("=" * 50)
    
    try:
        from app.data_loader import DataLoader
        
        loader = DataLoader()
        print(f"支持的文件格式: {loader.supported_extensions}")
        print("✓ 数据加载器初始化成功")
        
        print("\n✅ 数据加载器测试通过！\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 数据加载器测试失败: {str(e)}\n")
        return False


def test_text_splitter():
    """测试文本分割器"""
    print("=" * 50)
    print("测试4: 检查文本分割器")
    print("=" * 50)
    
    try:
        from app.text_spliter import TextSpliter
        
        splitter = TextSpliter()
        print(f"文本块大小: {splitter.text_splitter._chunk_size}")
        print(f"文本块重叠: {splitter.text_splitter._chunk_overlap}")
        print("✓ 文本分割器初始化成功")
        
        # 测试文本分割
        test_text = "这是第一段文本。这是第二段文本。这是第三段文本。"
        chunks = splitter.split_text(test_text)
        print(f"测试文本分割结果: {len(chunks)} 个文本块")
        
        print("\n✅ 文本分割器测试通过！\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 文本分割器测试失败: {str(e)}\n")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 50)
    print("  戒学书院知识库问答系统 - 组件测试")
    print("=" * 50 + "\n")
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("配置检查", test_config()))
    results.append(("数据加载器", test_data_loader()))
    results.append(("文本分割器", test_text_splitter()))
    
    # 显示测试结果
    print("=" * 50)
    print("  测试结果汇总")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！系统可以正常使用。")
        print("\n运行以下命令启动应用:")
        print("  streamlit run app/main.py")
    else:
        print("⚠️  部分测试失败，请检查错误信息并修复。")
    print("=" * 50 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
