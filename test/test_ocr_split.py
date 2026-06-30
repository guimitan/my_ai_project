"""
通用文档处理测试脚本 (支持图片OCR、TXT、PDF、DOCX)
用法：python -m test.test_ocr_split <文件路径>
"""
import sys
from pathlib import Path

from app.core.data_loader import DataLoader
from app.core.text_splitter import TextSplitter
from config.settings import CHUNK_SIZE, CHUNK_OVERLAP


def test_document_processing(file_path: str):
    """
    测试文档加载 + 文本切分全流程

    Args:
        file_path: 文件路径（支持 jpg, png, txt, pdf, docx）
    """
    file_path = Path(file_path)

    # ========== 第1步：检查文件状态 ==========
    print("=" * 60)
    print("  通用文档处理与切分测试")
    print("=" * 60)

    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    ext = file_path.suffix.lower()
    is_image = ext in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    print(f"\n📄 文件名称: {file_path.name}")
    print(f"   文件格式: {ext}")
    print(f"   文件大小: {file_path.stat().st_size / 1024:.1f} KB")

    # ========== 第2步：加载文档内容 ==========
    loader = DataLoader()
    print(f"\n⏳ 正在加载文档...")
    if is_image:
        print("   (检测到图片格式，将启动 OCR 识别)")
    
    try:
        documents = loader.load_document(str(file_path))
    except Exception as e:
        print(f"\n❌ 文档加载失败: {str(e)}")
        sys.exit(1)

    # 合并所有页面/段落的文本
    full_text = "\n\n".join([doc.page_content for doc in documents])
    print(f"\n✅ 加载成功！原始文本总长度: {len(full_text)} 个字符")

    # ========== 第3步：文本切分 ==========
    splitter = TextSplitter()
    print(f"\n🔪 文本切分配置:")
    print(f"   chunk_size  = {CHUNK_SIZE}")
    print(f"   chunk_overlap = {CHUNK_OVERLAP}")

    chunks = splitter.split_text(full_text)

    print(f"\n📦 切分结果: 共 {len(chunks)} 个文本块")
    print("-" * 60)

    for i, chunk in enumerate(chunks, 1):
        print(f"\n  【文本块 {i}】 (长度: {len(chunk)} 字符)")
        print("  " + "-" * 50)
        # 完整显示每个块的内容
        for line in chunk.split("\n"):
            print(f"  {line}")
        print("  " + "-" * 50)

    # ========== 第4步：汇总 ==========
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    print(f"  输入文件:     {file_path.name}")
    print(f"  原始文本长度: {len(full_text)} 字符")
    print(f"  切分块数:     {len(chunks)} 块")
    print(f"  切分参数:     chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")
    if chunks:
        print(f"  最大块长度:   {max(len(c) for c in chunks)} 字符")
        print(f"  最小块长度:   {min(len(c) for c in chunks)} 字符")
    print("=" * 60)
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test/test_ocr_split.py <文件路径>")
        print("支持格式: .jpg, .png, .txt, .pdf, .docx")
        sys.exit(1)
    
    test_document_processing(sys.argv[1])