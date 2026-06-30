# RAG系统Docker部署指南

本文档说明如何将Jie_RAG项目通过Docker部署到阿里云服务器。

## 📋 前置要求

1. **本地环境**：
   - 已安装 Docker Desktop
   - 已安装 Docker Compose

2. **阿里云服务器**：
   - 已购买阿里云ECS服务器
   - 已安装 Docker 和 Docker Compose
   - 已配置安全组规则，开放8501端口

3. **阿里云账号**：
   - 已注册阿里云账号
   - 已开通 DashScope 服务
   - 已获取 API Key

---

## 🚀 部署步骤

### 第一步：获取阿里云 DashScope API Key

1. 访问 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)
2. 登录阿里云账号
3. 在左侧菜单选择 "API-KEY管理"
4. 创建或复制您的 API Key
5. 确保已开通以下服务：
   - 通义千问大模型（qwen-plus）
   - 文本嵌入模型（text-embedding-v3）
   - 多模态模型（用于OCR，可选）

### 第二步：配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 文件，填入您的API Key
nano .env
```

`.env` 文件内容：
```env
DASHSCOPE_API_KEY=sk-your-actual-api-key-here
```

⚠️ **重要提示**：不要将 `.env` 文件提交到Git仓库！

### 第三步：本地构建和测试（可选）

在部署到服务器之前，建议先在本地测试：

```bash
# 构建Docker镜像
docker-compose build

# 启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 访问应用
# 浏览器打开: http://localhost:8501
```

### 第四步：上传项目到阿里云服务器

#### 方法一：使用 Git（推荐）

```bash
# 1. 在服务器上克隆项目
ssh root@your_server_ip
git clone <your_repository_url>
cd Jie_Rag

# 2. 创建 .env 文件
nano .env
# 填入 DASHSCOPE_API_KEY=your_api_key

# 3. 构建并启动
docker-compose up -d
```

#### 方法二：使用 SCP 上传

```bash
# 在本地执行
# 压缩项目（排除不必要的文件）
tar -czf jie_rag.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='data/documents/*' \
  --exclude='data/vector_store/*' \
  .

# 上传到服务器
scp jie_rag.tar.gz root@your_server_ip:/root/

# 在服务器上解压
ssh root@your_server_ip
mkdir -p /opt/jie_rag
cd /opt/jie_rag
tar -xzf ~/jie_rag.tar.gz

# 创建 .env 文件
nano .env
# 填入 DASHSCOPE_API_KEY=your_api_key

# 构建并启动
docker-compose up -d
```

#### 方法三：使用 Docker Registry

```bash
# 1. 在本地构建并推送到镜像仓库
docker-compose build
docker tag jie-rag-app:latest registry.cn-hangzhou.aliyuncs.com/your_namespace/jie-rag:latest
docker push registry.cn-hangzhou.aliyuncs.com/your_namespace/jie-rag:latest

# 2. 在服务器上拉取并运行
ssh root@your_server_ip
docker pull registry.cn-hangzhou.aliyuncs.com/your_namespace/jie-rag:latest
docker run -d \
  --name jie-rag-app \
  -p 8501:8501 \
  -e DASHSCOPE_API_KEY=your_api_key \
  -v /opt/jie_rag/data/vector_store:/app/data/vector_store \
  -v /opt/jie_rag/data/documents:/app/data/documents \
  --restart unless-stopped \
  registry.cn-hangzhou.aliyuncs.com/your_namespace/jie-rag:latest
```

### 第五步：配置阿里云服务器

#### 1. 安装 Docker（如果未安装）

```bash
# SSH连接到服务器
ssh root@your_server_ip

# 安装Docker
curl -fsSL https://get.docker.com | bash

# 启动Docker服务
systemctl start docker
systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

#### 2. 配置安全组规则

在阿里云控制台配置安全组，开放以下端口：
- **8501**：Streamlit应用端口
- **22**：SSH端口（已默认开放）

配置步骤：
1. 登录阿里云控制台
2. 进入 ECS 实例详情
3. 点击 "安全组" → "配置规则"
4. 添加入方向规则：
   - 端口范围：8501/8501
   - 授权对象：0.0.0.0/0（或指定IP）
   - 协议类型：TCP

### 第六步：启动应用

```bash
# 在服务器上执行
cd /path/to/Jie_Rag

# 创建 .env 文件（如果还没有）
nano .env
# 填入：DASHSCOPE_API_KEY=your_api_key

# 构建并启动
docker-compose up -d

# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 第七步：访问应用

在浏览器中访问：
```
http://your_server_ip:8501
```

---

## 🔧 常用运维命令

### 查看容器状态
```bash
docker-compose ps
```

### 查看实时日志
```bash
docker-compose logs -f
```

### 重启服务
```bash
docker-compose restart
```

### 停止服务
```bash
docker-compose down
```

### 更新应用
```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### 备份向量数据库
```bash
# 备份数据
tar -czf vector_store_backup_$(date +%Y%m%d_%H%M%S).tar.gz data/vector_store/

# 或使用docker命令
docker exec jie-rag-app tar -czf /tmp/backup.tar.gz /app/data/vector_store
docker cp jie-rag-app:/tmp/backup.tar.gz ./backup.tar.gz
```

### 清理空间
```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的容器
docker container prune

# 清理日志
truncate -s 0 $(docker inspect --format='{{.LogPath}}' jie-rag-app)
```

---

## 🛡️ 安全建议

### 1. 使用HTTPS（推荐）

使用Nginx反向代理配置HTTPS：

```bash
# 安装Nginx
apt-get install nginx certbot python3-certbot-nginx

# 创建Nginx配置
nano /etc/nginx/sites-available/jie-rag
```

Nginx配置文件：
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

启用配置并申请SSL证书：
```bash
ln -s /etc/nginx/sites-available/jie-rag /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# 申请Let's Encrypt证书
certbot --nginx -d your_domain.com
```

### 2. 添加身份验证

在 `docker-compose.yml` 中添加基本认证：

```yaml
services:
  rag-app:
    # ... 其他配置 ...
    environment:
      - STREAMLIT_SERVER_ENABLE_CORS=false
      - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

或在Nginx层添加HTTP Basic Auth。

### 3. 防火墙配置

```bash
# 启用UFW防火墙
ufw enable

# 只开放必要端口
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 8501/tcp   # 不直接暴露8501，通过Nginx访问
```

---

## 🐛 故障排查

### 问题1：容器无法启动

```bash
# 查看详细日志
docker-compose logs

# 检查环境变量
docker exec jie-rag-app env | grep DASHSCOPE

# 检查API Key是否正确
docker exec jie-rag-app python -c "import os; print(os.getenv('DASHSCOPE_API_KEY'))"
```

### 问题2：无法访问应用

```bash
# 检查容器是否运行
docker-compose ps

# 检查端口是否监听
netstat -tuln | grep 8501

# 检查防火墙
ufw status

# 检查阿里云安全组规则
```

### 问题3：API调用失败

```bash
# 测试API连接
docker exec jie-rag-app python -c "
import os
from dashscope import Generation
response = Generation.call(
    model='qwen-turbo',
    prompt='Hello',
    api_key=os.getenv('DASHSCOPE_API_KEY')
)
print(response)
"
```

### 问题4：内存不足

```bash
# 查看资源使用
docker stats

# 调整docker-compose.yml中的资源限制
# 或增加服务器内存
```

### 问题5：向量数据库损坏

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

## 📊 性能优化

### 1. 使用阿里云容器镜像服务

加速镜像拉取：
```bash
# 配置阿里云镜像加速器
mkdir -p /etc/docker
tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://your_mirror.mirror.aliyuncs.com"
  ]
}
EOF
systemctl restart docker
```

### 2. 调整资源限制

根据服务器配置调整 `docker-compose.yml`：
```yaml
deploy:
  resources:
    limits:
      memory: 8G    # 根据实际内存调整
      cpus: '4.0'   # 根据实际CPU调整
```

### 3. 使用Redis缓存（可选）

添加Redis缓存层提高响应速度。

---

## 📝 注意事项

1. **API费用**：阿里云DashScope API按用量计费，请注意控制成本
2. **数据安全**：定期备份向量数据库和重要文档
3. **监控告警**：建议配置服务器监控和告警
4. **日志轮转**：配置Docker日志轮转防止磁盘占满
5. **自动重启**：已配置 `restart: unless-stopped`，容器异常会自动重启

---

## 📞 技术支持

如遇到问题，请检查：
1. Docker和Docker Compose版本
2. 阿里云API Key是否有效
3. 服务器安全组配置
4. 应用日志输出

---

**祝部署顺利！** 🎉
