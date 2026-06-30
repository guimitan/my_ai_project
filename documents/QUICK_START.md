# 🚀 快速部署指南（5分钟上手）

## 📝 前置准备

1. ✅ 阿里云ECS服务器（已安装Docker）
2. ✅ 阿里云DashScope API Key（[获取地址](https://dashscope.console.aliyun.com/)）

---

## 🔧 部署步骤

### 方式一：使用自动化脚本（推荐）

#### Windows系统：
```bash
# 1. 配置API Key
copy .env.example .env
# 用记事本打开.env，填入你的API Key

# 2. 一键部署
deploy.bat
```

#### Linux/Mac系统：
```bash
# 1. 配置API Key
cp .env.example .env
nano .env  # 填入你的API Key

# 2. 赋予执行权限
chmod +x deploy.sh

# 3. 一键部署
./deploy.sh
```

### 方式二：手动部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑.env文件，设置 DASHSCOPE_API_KEY=your_api_key

# 2. 构建并启动
docker-compose up -d

# 3. 查看状态
docker-compose ps
docker-compose logs -f
```

---

## 🌐 访问应用

- **本地访问**：http://localhost:8501
- **服务器访问**：http://YOUR_SERVER_IP:8501

⚠️ **重要**：确保阿里云安全组已开放 **8501** 端口！

---

## 📋 常用命令速查

```bash
# 查看运行状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新代码后重新部署
git pull
docker-compose up -d --build

# 备份数据
tar -czf backup_$(date +%Y%m%d).tar.gz data/
```

---

## 🐛 常见问题

### Q1: 无法访问应用？
```bash
# 检查容器是否运行
docker-compose ps

# 检查端口监听
netstat -tuln | grep 8501

# 检查阿里云安全组是否开放8501端口
```

### Q2: API调用失败？
```bash
# 验证API Key是否正确配置
docker exec jie-rag-app env | grep DASHSCOPE

# 测试API连接
docker exec jie-rag-app python -c "import os; print(os.getenv('DASHSCOPE_API_KEY')[:10])"
```

### Q3: 如何更新应用？
```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

---

## 📊 架构图

```
用户浏览器
    ↓
http://server_ip:8501
    ↓
┌─────────────────────┐
│   Streamlit Web UI  │
└─────────────────────┘
    ↓
┌─────────────────────┐
│   RAG Chain         │
│  (检索+生成)         │
└─────────────────────┘
    ↓         ↓
┌────────┐ ┌──────────┐
│向量数据库│ │阿里云API  │
│ChromaDB│ │DashScope │
└────────┘ └──────────┘
```

---

## 💡 下一步

1. 📤 上传文档到知识库（支持PDF、TXT、图片等）
2. 💬 开始智能问答
3. 📊 查看向量可视化
4. 🔍 搜索和管理文档

详细使用说明请查看 [DEPLOYMENT.md](DEPLOYMENT.md)

---

**祝你使用愉快！** 🎉
