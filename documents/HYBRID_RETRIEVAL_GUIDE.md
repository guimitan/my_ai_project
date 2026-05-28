# 混合检索与重排序功能说明

## 📋 功能概述

本项目现已支持**混合检索**和**重排序**功能，可以显著提升RAG系统的检索质量。

### 核心改进

1. **混合检索（Hybrid Retrieval）**
   - 结合向量语义检索 + BM25关键词检索
   - 同时捕捉语义相似性和精确匹配
   - 特别适合专有名词、技术术语等场景

2. **重排序（Reranking）**
   - 使用CrossEncoder对初步检索结果进行精排
   - 更准确地评估查询-文档相关性
   - 提升Top-K结果的质量

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

新增依赖：
- `rank-bm25`: BM25关键词检索算法
- `jieba`: 中文分词工具
- `sentence-transformers`: CrossEncoder重排序模型（可选）

### 2. 基本使用

#### 方式一：默认启用（推荐）

```python
from app.core.rag_chain import RAGChain

# 自动启用混合检索和重排序
rag = RAGChain()

# 查询
result = rag.query("你的问题", k=5)
print(result['answer'])
```

#### 方式二：自定义配置

```python
from app.core.rag_chain import RAGChain

# 只使用混合检索，不重排序
rag = RAGChain(
    use_hybrid_retrieval=True,
    use_reranker=False
)

# 只使用重排序，不使用混合检索
rag = RAGChain(
    use_hybrid_retrieval=False,
    use_reranker=True,
    reranker_type="heuristic"
)

# 完全禁用高级功能（回退到纯向量检索）
rag = RAGChain(
    use_hybrid_retrieval=False,
    use_reranker=False
)
```

#### 方式三：调整权重

```python
# 调整向量检索和BM25的权重
result = rag.query(
    "你的问题",
    k=5,
    vector_weight=0.8,  # 向量权重80%
    bm25_weight=0.2     # BM25权重20%
)
```

---

## 📊 检索策略对比

| 策略 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **纯向量检索** | 实现简单，语义理解强 | 专有名词效果差 | 通用语义搜索 |
| **混合检索** | 兼顾语义和精确匹配 | 需要构建BM25索引 | 技术文档、专业术语 |
| **混合+重排序** | 检索质量最高 | 计算开销较大 | 高质量问答场景 |

---

## 🔧 高级配置

### 1. 重排序器类型

```python
# CrossEncoder重排序（推荐，需要安装sentence-transformers）
rag = RAGChain(reranker_type="cross_encoder")

# 启发式重排序（无需额外模型）
rag = RAGChain(reranker_type="heuristic")

# 不重排序
rag = RAGChain(reranker_type="none")
```

### 2. 刷新BM25索引

当向量数据库更新后，需要刷新BM25索引：

```python
from app.core.hybrid_retriever import HybridRetriever
from app.core.vector_db import VectorDatabase

vector_db = VectorDatabase()
vector_db.initialize()

hybrid = HybridRetriever(vector_db)
hybrid.refresh_index()  # 重新构建BM25索引
```

### 3. 单独使用混合检索器

```python
from app.core.hybrid_retriever import HybridRetriever
from app.core.vector_db import VectorDatabase

vector_db = VectorDatabase()
vector_db.initialize()

hybrid = HybridRetriever(vector_db)

# 检索文档
docs = hybrid.retrieve(
    "查询文本",
    k=10,
    vector_weight=0.7,
    bm25_weight=0.3
)
```

---

## 📈 性能优化建议

### 1. 权衡速度与质量

- **生产环境**：建议使用 `混合检索 + 启发式重排序`
- **离线评估**：可以使用 `混合检索 + CrossEncoder重排序`
- **实时性要求高**：可以只用 `混合检索`，跳过重排序

### 2. 调整召回数量

```python
# 内部会召回 k*2 个文档，然后重排序选出 Top-K
result = rag.query("问题", k=5)  # 实际召回10个，重排序后返回5个
```

### 3. 权重调优

根据实际效果调整权重：
- 语义为主：`vector_weight=0.8, bm25_weight=0.2`
- 均衡模式：`vector_weight=0.7, bm25_weight=0.3`（默认）
- 精确匹配：`vector_weight=0.5, bm25_weight=0.5`

---

## ⚠️ 注意事项

1. **首次使用时会自动构建BM25索引**，可能需要几秒到几分钟（取决于文档数量）

2. **CrossEncoder模型下载**：
   - 首次使用CrossEncoder时会自动下载模型（约几百MB）
   - 如果网络不好，可以改用启发式重排序

3. **内存占用**：
   - BM25索引会占用一定内存
   - CrossEncoder模型推理时需要GPU加速（可选）

4. **索引同步**：
   - 每次添加/删除文档后，建议调用 `refresh_index()` 刷新BM25索引

---

## 🔍 故障排查

### 问题1：导入错误 `ModuleNotFoundError: No module named 'rank_bm25'`

**解决方案**：
```bash
pip install rank-bm25 jieba
```

### 问题2：CrossEncoder模型加载失败

**解决方案**：
使用启发式重排序代替：
```python
rag = RAGChain(reranker_type="heuristic")
```

### 问题3：BM25索引构建失败

**可能原因**：向量数据库为空

**解决方案**：
先上传文档，再初始化混合检索器

---

## 📝 示例代码

完整示例请参考项目中的以下文件：
- `app/core/hybrid_retriever.py` - 混合检索器实现
- `app/core/reranker.py` - 重排序器实现
- `app/core/rag_chain.py` - 集成示例

---

## 🎯 下一步

- 运行评估实验对比不同检索策略的效果
- 根据实际业务场景调优权重参数
- 考虑部署专用的CrossEncoder模型服务

---

**祝使用愉快！** 🎉
