# RAG 文档问答（/rag）

## 一、概述

RAG（Retrieval-Augmented Generation）文档问答功能允许用户基于项目中的 Markdown 文档进行提问，系统会自动检索相关文档并生成准确的回答。

## 二、核心原理

```
用户问题 → 向量化 → FAISS向量检索 → 拼接上下文 → LLM生成 → 返回答案
```

### 2.1 技术栈

| 组件 | 技术 | 作用 |
|------|------|------|
| **向量化模型** | HuggingFace all-MiniLM-L6-v2 | 将文本转换为向量 |
| **向量数据库** | FAISS | 存储和检索向量 |
| **文档分割** | LangChain MarkdownTextSplitter | 将长文档分割为 chunks |
| **LLM** | 火山引擎 ark-code-latest | 生成最终回答 |

## 三、处理流程

### 3.1 流程详解

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  用户发送问题    │───→│   问题向量化     │───→│   FAISS检索      │
└──────────────────┘    └──────────────────┘    └────────┬─────────┘
                                                          │
                                                          ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   构建提示词     │←───│   拼接上下文     │←───│   获取相关文档   │
└────────┬─────────┘    └──────────────────┘    └──────────────────┘
         │
         ▼
┌──────────────────┐    ┌──────────────────┐
│   调用LLM生成    │───→│   返回回答       │
└──────────────────┘    └──────────────────┘
```

### 3.2 关键代码

```python
# app/services/rag_service.py
async def query(self, question: str) -> str:
    # 1. 加载文档并构建向量索引（延迟加载）
    if not self.vector_store:
        await self._load_documents()
    
    # 2. 检索相关文档（默认返回3条）
    retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
    docs = await retriever.ainvoke(question)
    
    # 3. 拼接上下文
    context = "\n\n".join([doc.page_content for doc in docs])
    
    # 4. 构建提示词
    prompt = f"""根据以下上下文回答问题：

    {context}

    问题：{question}

    如果上下文没有相关信息，请回答"未找到相关答案"。
    """
    
    # 5. 调用 LLM 生成回答
    response = await self.ai_chat_service.chat(prompt)
    return response
```

## 四、文档加载机制

### 4.1 加载流程

```python
# app/services/rag_service.py
async def _load_documents(self):
    # 1. 扫描 documents 目录
    docs_path = settings.rag_docs_path
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)
    
    # 2. 加载所有 Markdown 文件
    md_files = list(docs_path.glob("*.md"))
    if not md_files:
        # 创建默认欢迎文档
        welcome_content = "# 欢迎使用\n\n这是一个聊天机器人..."
        (docs_path / "welcome.md").write_text(welcome_content, encoding='utf-8')
        md_files = [docs_path / "welcome.md"]
    
    # 3. 读取文档内容
    docs = []
    for md_file in md_files:
        content = md_file.read_text(encoding='utf-8')
        docs.append(Document(page_content=content, metadata={"source": str(md_file)}))
    
    # 4. 分割文档为 chunks（每块1000字符，重叠200字符）
    from langchain.text_splitter import MarkdownTextSplitter
    text_splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = text_splitter.split_documents(docs)
    
    # 5. 向量化并构建 FAISS 索引
    from langchain.vectorstores import FAISS
    from langchain.embeddings import HuggingFaceEmbeddings
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    self.vector_store = FAISS.from_documents(split_docs, embeddings)
```

### 4.2 文档分割策略

| 参数 | 值 | 说明 |
|------|-----|------|
| chunk_size | 1000 | 每个 chunk 的最大字符数 |
| chunk_overlap | 200 | 相邻 chunk 的重叠字符数 |

## 五、向量检索机制

### 5.1 检索原理

FAISS 使用余弦相似度来匹配问题向量与文档向量：

```python
# 伪代码展示检索原理
def search(query_vector, document_vectors, top_k=3):
    # 计算余弦相似度
    similarities = [cosine_similarity(query_vector, doc_vec) for doc_vec in document_vectors]
    
    # 按相似度排序
    sorted_indices = argsort(similarities)[::-1]
    
    # 返回前 top_k 个结果
    return [document_vectors[i] for i in sorted_indices[:top_k]]
```

### 5.2 检索优化

- **延迟加载**：只在首次查询时加载文档，避免启动时的性能开销
- **向量缓存**：加载后缓存到内存，后续查询直接使用
- **动态更新**：支持热更新，添加新文档后自动重建索引

## 六、提示词工程

### 6.1 提示词模板

```python
prompt = f"""根据以下上下文回答问题：

{context}

问题：{question}

如果上下文没有相关信息，请回答"未找到相关答案"。
"""
```

### 6.2 设计原则

1. **明确指令**：告诉模型必须基于提供的上下文回答
2. **边界处理**：明确告知模型如何处理找不到答案的情况
3. **格式要求**：保持回答简洁清晰

## 七、使用示例

### 7.1 基本用法

```
/rag 如何配置 MCP 服务？
/rag 项目的目录结构是什么？
/rag 如何添加新的聊天平台？
```

### 7.2 高级用法

```
/rag 请解释 RAG 的工作原理
/rag 如何配置 GitHub Token？
/rag 代码修改助手的安全机制有哪些？
```

## 八、配置说明

### 8.1 环境变量

```env
# RAG 配置
RAG_DOCS_PATH=data/documents
```

### 8.2 文档目录结构

```
data/
└── documents/
    ├── welcome.md      # 默认欢迎文档
    ├── api.md          # API 文档
    ├── config.md       # 配置说明
    └── features.md     # 功能说明
```

## 九、扩展能力

### 9.1 添加新文档

只需将 Markdown 文件放入 `data/documents/` 目录，系统会自动加载。

### 9.2 更换向量化模型

修改 `rag_service.py` 中的模型名称：

```python
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# 可更换为其他模型
# embeddings = HuggingFaceEmbeddings(model_name="bert-base-chinese")
```

## 十、代码位置

| 文件 | 说明 |
|------|------|
| `app/services/rag_service.py` | RAG 服务实现 |
| `app/core/agent.py` | /rag 命令处理 |
| `data/documents/` | Markdown 文档目录 |
