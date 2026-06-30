# ⚡ Docker部署速查卡

## 🔑 3步快速部署

```bash
# 1️⃣ 配置API Key
cp .env.example .env
# 编辑.env，填入: DASHSCOPE_API_KEY=sk-your-key

# 2️⃣ 运行部署脚本
./deploy.sh          # Linux/Mac
deploy.bat           # Windows

# 3️⃣ 访问应用
# http://localhost:8501
```

---

## 📋 常用命令速查

### 启动/停止
```bash
docker-compose up -d          # 启动
docker-compose down           # 停止
docker-compose restart        # 重启
```

### 查看状态
```bash
docker-compose ps             # 容器状态
docker-compose logs -f        # 实时日志
docker stats                  # 资源使用
```

### 更新应用
```bash
git pull                      # 拉取代码
docker-compose up -d --build  # 重新构建
docker image prune -f         # 清理旧镜像
```

### 进入容器
```bash
docker exec -it jie-rag-app bash    # 进入容器
docker exec jie-rag-app env | grep DASHSCOPE  # 检查配置
```

### 备份数据
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz data/
```

---

## 🔍 故障排查速查

### 容器无法启动
```bash
docker-compose logs           # 查看错误
docker-compose config         # 检查配置
cat .env                      # 验证环境变量
```

### 无法访问应用
```bash
docker-compose ps             # 检查容器运行
netstat -tuln | grep 8501    # 检查端口
# 检查阿里云安全组是否开放8501
```

### API调用失败
```bash
docker exec jie-rag-app env | grep DASHSCOPE  # 检查API Key
# 验证API Key是否有效
```

### 内存不足
```bash
docker stats                  # 查看资源使用
# 修改docker-compose.yml的资源限制
```

---

## 🌐 访问地址

- **本地**: http://localhost:8501
- **服务器**: http://YOUR_SERVER_IP:8501

⚠️ **确保阿里云安全组已开放8501端口！**

---

## 📁 重要文件

| 文件 | 用途 |
|------|------|
| `.env` | API Key配置（不要提交Git） |
| `docker-compose.yml` | 服务配置 |
| `data/vector_store/` | 向量数据库（需备份） |
| `data/documents/` | 上传的文档（需备份） |

---

## 🔒 安全检查

- [ ] `.env` 文件已配置
- [ ] `.env` 未提交到Git
- [ ] 安全组开放8501端口
- [ ] 定期备份data目录
- [ ] 监控资源使用

---

## 💰 成本提示

- 阿里云DashScope API按用量计费
- 建议设置API用量告警
- 定期查看控制台费用

---

## 📞 获取帮助

- 快速指南: `QUICK_START.md`
- 详细文档: `DEPLOYMENT.md`
- 技术参考: `README_DOCKER.md`
- 流程图解: `DEPLOYMENT_FLOW.md`

---

**打印此卡片，放在手边随时查阅！** 📌
