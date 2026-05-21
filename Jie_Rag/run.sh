#!/bin/bash

echo "========================================"
echo "  戒学书院知识库问答系统 - 启动脚本"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3，请先安装Python 3.8+"
    exit 1
fi

echo "[信息] Python版本: $(python3 --version)"
echo ""

# 检查依赖
echo "[信息] 正在检查依赖..."
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "[警告] 未检测到Streamlit，正在安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
fi

echo ""
echo "[重要提示] 请确保已设置阿里云 API 密钥"
echo "[提示] 可以通过以下方式设置："
echo "  1. 设置环境变量 DASHSCOPE_API_KEY"
echo "  2. 或创建 .env 文件并填入 API Key"
echo ""

# 检查是否设置了API密钥
if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "[警告] 未检测到 DASHSCOPE_API_KEY 环境变量"
    if [ -f .env ]; then
        echo "[信息] 发现 .env 文件，将尝试加载..."
        export $(cat .env | grep -v '^#' | xargs)
    else
        echo "[错误] 请先配置 API 密钥后再启动应用"
        echo "[提示] 复制 .env.example 为 .env 并填入您的 API Key"
        exit 1
    fi
fi

echo ""
echo "[信息] 正在启动Streamlit应用..."
echo "[提示] 浏览器会自动打开应用页面"
echo "[提示] 按 Ctrl+C 可停止服务"
echo ""

cd app
streamlit run main.py
