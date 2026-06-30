"""
测试向量数据库导出功能
"""
from pathlib import Path

from app.core.vector_db import VectorDatabase


def test_export_to_json():
    """测试导出向量数据库到JSON文件"""
    print("=" * 60)
    print("测试1: 导出向量数据库到JSON（不包含向量）")
    print("=" * 60)
    
    try:
        # 初始化向量数据库
        vector_db = VectorDatabase()
        vector_db.initialize()
        
        # 获取文档数量
        count = vector_db.get_document_count()
        print(f"\n当前向量数据库中有 {count} 个文档块\n")
        
        if count == 0:
            print("⚠️ 向量数据库为空，请先上传一些文档")
            return
        
        # 导出到JSON（不包含向量嵌入）
        output_path = vector_db.export_to_json(include_embeddings=False)
        print(f"\n✅ 导出成功！文件路径: {output_path}")
        print(f"💡 提示: 可以用文本编辑器或浏览器打开查看\n")
        
    except Exception as e:
        print(f"❌ 导出失败: {str(e)}")
        import traceback
        traceback.print_exc()


def test_export_with_embeddings():
    """测试导出包含向量嵌入的JSON文件"""
    print("\n" + "=" * 60)
    print("测试2: 导出向量数据库到JSON（包含向量）")
    print("=" * 60)
    
    try:
        vector_db = VectorDatabase()
        vector_db.initialize()
        
        count = vector_db.get_document_count()
        print(f"\n当前向量数据库中有 {count} 个文档块\n")
        
        if count == 0:
            print("⚠️ 向量数据库为空")
            return
        
        # 导出到JSON（包含向量嵌入）
        output_path = vector_db.export_to_json(
            include_embeddings=True,
            output_path="data/vector_store/export_with_vectors.json"
        )
        print(f"\n✅ 导出成功！文件路径: {output_path}")
        print(f"⚠️ 注意: 包含向量的文件会比较大\n")
        
    except Exception as e:
        print(f"❌ 导出失败: {str(e)}")


def test_get_all_documents():
    """测试直接获取所有文档信息"""
    print("\n" + "=" * 60)
    print("测试3: 直接获取所有文档信息（不导出文件）")
    print("=" * 60)
    
    try:
        vector_db = VectorDatabase()
        vector_db.initialize()
        
        documents = vector_db.get_all_documents()
        print(f"\n获取到 {len(documents)} 个文档块\n")
        
        # 显示前3个文档的信息
        for i, doc in enumerate(documents[:3]):
            print(f"--- 文档 {i+1} ---")
            print(f"ID: {doc['id']}")
            print(f"内容预览: {doc['content'][:100]}...")
            print(f"元数据: {doc['metadata']}")
            print()
        
        if len(documents) > 3:
            print(f"... 还有 {len(documents) - 3} 个文档未显示\n")
        
    except Exception as e:
        print(f"❌ 获取失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 开始测试向量数据库导出功能\n")
    
    # 运行测试
    test_export_to_json()
    test_get_all_documents()
    
    # 可选：测试包含向量的导出（文件较大）
    # test_export_with_embeddings()
    
    print("\n✨ 测试完成！")
    print("\n💡 使用建议:")
    print("1. 定期导出JSON作为备份")
    print("2. 用文本编辑器查看导出的JSON文件")
    print("3. 可以导入到其他系统进行分析")
    print("4. 包含向量的文件较大，仅在需要时导出\n")
