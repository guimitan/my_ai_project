"""
OCR图片识别模块 - 使用阿里云OCR服务识别图片中的文字
"""
from pathlib import Path
from typing import Optional
import dashscope
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import OCR_API_KEY, OCR_ENABLED


class ImageOCR:
    """图片OCR识别类，使用阿里云通义千问VL模型"""
    
    def __init__(self, api_key: str = None):
        """
        初始化OCR服务
        
        Args:
            api_key: API密钥，如果为None则从配置中获取
        """
        self.api_key = api_key or OCR_API_KEY
        self.enabled = OCR_ENABLED and bool(self.api_key)
        
        if not self.enabled:
            print("警告: OCR功能未启用或API密钥未配置")
        
        # 设置API密钥
        if self.enabled:
            dashscope.api_key = self.api_key
    
    def recognize_image(self, image_path: str) -> str:
        """
        识别图片中的文字
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            识别出的文本内容
        """
        if not self.enabled:
            raise Exception("OCR功能未启用，请配置API密钥")
        
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        try:
            # 使用通义千问VL模型进行OCR识别
            response = dashscope.MultiModalConversation.call(
                model='qwen-vl-plus',
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"image": f"file://{image_path.absolute()}"},
                            {"text": "请识别这张图片中的所有文字内容，保持原有的格式和排版。"}
                        ]
                    }
                ]
            )
            
            if response.status_code == 200:
                # 提取识别结果
                text_content = response.output.choices[0].message.content[0]['text']
                return text_content
            else:
                raise Exception(f"OCR识别失败: {response.message}")
        
        except Exception as e:
            raise Exception(f"OCR识别出错: {str(e)}")
    
    def recognize_image_from_bytes(self, image_bytes: bytes, filename: str = "temp.jpg") -> str:
        """
        从字节数据识别图片中的文字
        
        Args:
            image_bytes: 图片的字节数据
            filename: 临时文件名（用于确定格式）
            
        Returns:
            识别出的文本内容
        """
        if not self.enabled:
            raise Exception("OCR功能未启用，请配置API密钥")
        
        try:
            # 创建临时文件
            import tempfile
            suffix = Path(filename).suffix or '.jpg'
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(image_bytes)
                tmp_path = tmp_file.name
            
            try:
                # 识别图片
                text = self.recognize_image(tmp_path)
                return text
            finally:
                # 清理临时文件
                import os
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        
        except Exception as e:
            raise Exception(f"OCR识别出错: {str(e)}")
    
    def is_supported_format(self, file_path: str) -> bool:
        """
        检查文件格式是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持该格式
        """
        from config.settings import SUPPORTED_IMAGE_FORMATS
        suffix = Path(file_path).suffix.lower()
        return suffix in SUPPORTED_IMAGE_FORMATS
    
    def get_supported_formats(self) -> set:
        """
        获取支持的图片格式
        
        Returns:
            支持的格式集合
        """
        from config.settings import SUPPORTED_IMAGE_FORMATS
        return SUPPORTED_IMAGE_FORMATS.copy()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OCR图片识别测试")
    parser.add_argument("image", type=str, help="要识别的图片文件路径")
    parser.add_argument("--api-key", type=str, default=None, help="DashScope API密钥（可选，默认从环境变量读取）")
    args = parser.parse_args()

    # 初始化OCR
    ocr = ImageOCR(api_key=args.api_key)

    if not ocr.enabled:
        print("❌ OCR功能未启用！请确保：")
        print("  1. 已设置环境变量 DASHSCOPE_API_KEY")
        print("  2. 或通过 --api-key 参数传入密钥")
        print("  3. 可在 .env 文件或系统环境变量中配置")
        sys.exit(1)

    # 检查文件格式
    if not ocr.is_supported_format(args.image):
        print(f"❌ 不支持的图片格式: {Path(args.image).suffix}")
        print(f"   支持的格式: {ocr.get_supported_formats()}")
        sys.exit(1)

    print(f"\n🔍 正在识别图片: {args.image}")
    print("-" * 50)

    try:
        result = ocr.recognize_image(args.image)
        print("\n📝 OCR识别结果:")
        print("=" * 50)
        print(result)
        print("=" * 50)
        print("\n✅ 识别完成！")
    except Exception as e:
        print(f"\n❌ 识别失败: {str(e)}")
        sys.exit(1)
