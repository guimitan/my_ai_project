# 🚀 快速开始 - 混合检索与重排序

## 第一步：安装依赖

```bash
pip install rank-bm25 jieba sentence-transformers
```

或者使用项目根目录的 requirements.txt：

```bash
pip install -r requirements.txt
```

---

## 第二步：基本使用（3行代码）

```python
from app.core.rag_chain import RAGChain

# 创建RAG链（自动启用混合检索+重排序）
rag = RAGChain()

# 查询
result = rag.query("你的问题", k=5)
print(result['answer'])
```

就这么简单！✨

---

## 第三步：查看效果

### 方式1：在代码中使用

```python
from app.core.rag_chain import RAGChain

rag = RAGChain()

# 对比不同策略
questions = [
    "RAG系统使用的是什么向量数据库？",
    "如何处理PDF文档中的表格？",
    "文本分割的策略是什么？"
]

for question in questions:
    print(f"\n问题: {question}")
    result = rag.query(question, k=5)
    print(f"答案: {result['answer'][:200]}...")
    print(f"来源数量: {result['context_count']}")
```

### 方式2：启动Web UI

```bash
streamlit run app/webui/main.py
```

然后在浏览器中体验问答功能。

---

## 常见问题

### Q1: 提示缺少模块怎么办？

**A:** 安装缺失的依赖：
```bash
pip install rank-bm25 jieba
```

### Q2: CrossEncoder模型下载很慢？

**A:** 使用启发式重排序代替：
```python
rag = RAGChain(reranker_type="heuristic")
```

### Q3: 首次运行很慢？

**A:** 正常现象，因为需要：
- 构建BM25索引（一次性）
- 下载CrossEncoder模型（一次性，约几百MB）

后续运行会快很多。

### Q4: 如何回退到原来的纯向量检索？

**A:** 
```python
rag = RAGChain(use_hybrid_retrieval=False, use_reranker=False)
```

---

## 下一步

- 📖 阅读完整指南：`HYBRID_RETRIEVAL_GUIDE.md`
- 💡 查看更多示例：`examples_hybrid_retrieval.py`
- 📊 了解技术细节：`IMPLEMENTATION_SUMMARY.md`

---

**祝使用愉快！** 🎉
