# 使用Python 3.11基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY documents/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt  -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目代码
COPY . .

# 创建必要的目录
RUN mkdir -p data/documents data/vector_store/chroma_db

# 暴露Streamlit默认端口
EXPOSE 8501

# 健康检查
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 启动命令
CMD ["streamlit", "run", "app/webui/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
