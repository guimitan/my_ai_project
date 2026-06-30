# 🐳 Docker 部署说明

本文档专门说明如何使用 Docker 部署 Jie_RAG 项目。

## 📦 项目结构

```
Jie_Rag/
├── Dockerfile              # Docker镜像构建文件
├── docker-compose.yml      # Docker Compose配置文件
├── .dockerignore          # Docker忽略文件
├── .env.example           # 环境变量示例文件
├── deploy.sh              # Linux/Mac一键部署脚本
├── deploy.bat             # Windows一键部署脚本
├── QUICK_START.md         # 快速开始指南
├── DEPLOYMENT.md          # 详细部署文档
└── README_DOCKER.md       # 本文件
```

## 🚀 快速开始

### 1. 配置API Key

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入你的阿里云DashScope API Key
# DASHSCOPE_API_KEY=sk-your-actual-api-key
```

### 2. 一键部署

**Windows:**
```bash
deploy.bat
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

### 3. 访问应用

打开浏览器访问：`http://localhost:8501`

---

## 🔧 手动部署

如果不使用自动化脚本，可以手动执行：

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 查看状态
docker-compose ps
```

---

## 📋 Docker 配置说明

### Dockerfile

- **基础镜像**: `python:3.11-slim`
- **工作目录**: `/app`
- **暴露端口**: `8501` (Streamlit)
- **健康检查**: 每30秒检查应用状态

### docker-compose.yml

主要配置项：

```yaml
services:
  rag-app:
    ports:
      - "8501:8501"          # 端口映射
    environment:
      - DASHSCOPE_API_KEY    # API密钥
    volumes:
      - ./data/vector_store  # 向量数据库持久化
      - ./data/documents     # 文档持久化
    restart: unless-stopped  # 自动重启
    deploy:
      resources:
        limits:
          memory: 4G         # 内存限制
          cpus: '2.0'        # CPU限制
```

### 数据持久化

通过 Docker volumes 实现数据持久化：

- `data/vector_store`: 向量数据库（ChromaDB）
- `data/documents`: 上传的文档文件

这些数据在容器删除后仍然保留。

---

## 🛠️ 常用命令

### 基本操作

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 查看状态
docker-compose ps
```

### 进入容器

```bash
# 进入运行中的容器
docker exec -it jie-rag-app bash

# 在容器中执行Python命令
docker exec jie-rag-app python --version

# 查看环境变量
docker exec jie-rag-app env | grep DASHSCOPE
```

### 更新应用

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 清理旧镜像
docker image prune -f
```

### 备份数据

```bash
# 备份向量数据库
tar -czf vector_store_backup_$(date +%Y%m%d).tar.gz data/vector_store/

# 备份所有数据
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
```

### 清理空间

```bash
# 删除未使用的镜像
docker image prune -a

# 删除未使用的容器
docker container prune

# 删除未使用的卷
docker volume prune

# 清理日志
truncate -s 0 $(docker inspect --format='{{.LogPath}}' jie-rag-app)
```

---

## 🔍 故障排查

### 问题1: 容器无法启动

```bash
# 查看详细错误信息
docker-compose logs

# 检查配置文件语法
docker-compose config

# 验证.env文件
cat .env
```

### 问题2: 端口被占用

```bash
# 查看8501端口占用情况
# Windows
netstat -ano | findstr :8501

# Linux/Mac
lsof -i :8501

# 解决方案：修改docker-compose.yml中的端口映射
ports:
  - "8502:8501"  # 改为其他端口
```

### 问题3: 内存不足

```bash
# 查看资源使用情况
docker stats

# 调整资源限制（编辑docker-compose.yml）
deploy:
  resources:
    limits:
      memory: 2G  # 降低内存限制
```

### 问题4: API连接失败

```bash
# 测试网络连接
docker exec jie-rag-app ping dashscope.aliyuncs.com

# 验证API Key
docker exec jie-rag-app python -c "
import os
from dashscope import Generation
response = Generation.call(
    model='qwen-turbo',
    prompt='Hello',
    api_key=os.getenv('DASHSCOPE_API_KEY')
)
print(response.status_code)
"
```

### 问题5: 向量数据库损坏

```bash
# 停止服务
docker-compose down

# 删除向量数据库
rm -rf data/vector_store/chroma_db

# 重新启动
docker-compose up -d

# 重新上传文档
```

---

## 🌐 生产环境部署

### 1. 使用Nginx反向代理

创建 `nginx.conf`:

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2. 配置HTTPS

```bash
# 安装certbot
apt-get install certbot python3-certbot-nginx

# 申请SSL证书
certbot --nginx -d your_domain.com
```

### 3. 添加监控

使用 Prometheus + Grafana 监控容器状态：

```yaml
# docker-compose.yml 添加监控服务
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

---

## 🔒 安全建议

### 1. 保护API Key

- ✅ 使用 `.env` 文件管理密钥
- ✅ 不要将 `.env` 提交到Git
- ✅ 定期轮换API Key
- ❌ 不要在代码中硬编码密钥

### 2. 网络隔离

```yaml
# docker-compose.yml 添加网络配置
networks:
  rag-network:
    driver: bridge

services:
  rag-app:
    networks:
      - rag-network
```

### 3. 限制资源

```yaml
# 防止资源滥用
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
    reservations:
      memory: 2G
      cpus: '1.0'
```

### 4. 定期更新

```bash
# 每周检查更新
docker-compose pull
docker-compose up -d
```

---

## 📊 性能优化

### 1. 使用多阶段构建

优化Dockerfile减小镜像体积（已优化）。

### 2. 启用缓存

```bash
# 利用Docker层缓存
docker-compose build --no-cache  # 首次构建
docker-compose build             # 后续构建使用缓存
```

### 3. 调整Python参数

```bash
# 设置Python优化标志
ENV PYTHONOPTIMIZE=1
```

---

## 📞 获取帮助

如遇到问题：

1. 查看 [DEPLOYMENT.md](DEPLOYMENT.md) 详细文档
2. 查看 [QUICK_START.md](QUICK_START.md) 快速指南
3. 检查应用日志：`docker-compose logs -f`
4. 查看Docker日志：`docker logs jie-rag-app`

---

## 🎯 下一步

- 📖 阅读完整部署文档：[DEPLOYMENT.md](DEPLOYMENT.md)
- 🚀 查看快速开始：[QUICK_START.md](QUICK_START.md)
- 📚 了解项目架构：查看项目主README

---

**Happy Deploying!** 🎉
