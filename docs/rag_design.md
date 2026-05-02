# RAG 模块设计

## 目标

RAG 模块用于把简历、岗位 JD、项目经历和历史投递记录转化为可检索上下文，辅助 JD 分析、简历匹配、简历优化和面试问题生成。

## 模块边界

`app/rag/` 后续建议拆分为：

- `loaders.py`：文档读取与文本抽取。
- `splitters.py`：文本切分策略。
- `embeddings.py`：Embedding Provider 封装。
- `vector_store.py`：Qdrant 写入、更新、删除和查询。
- `retriever.py`：面向业务的检索接口。

## 数据流程

```text
文档 / 文本
 |
解析
 |
切分
 |
Embedding
 |
Qdrant 写入
 |
检索
 |
LLM / Tool / Agent 使用上下文
```

## 切分策略

初始配置来自 `config/app.yaml`：

- `rag.chunk_size`
- `rag.chunk_overlap`
- `rag.top_k`

MVP 阶段建议先使用固定长度加 overlap 的策略。后续可以根据简历结构升级为标题、项目、经历、技能等语义块切分。

## Qdrant Payload 设计

建议每个向量点保留以下 payload：

```json
{
  "document_id": "resume-001",
  "document_type": "resume",
  "source": "resume.pdf",
  "section": "project",
  "text": "chunk text",
  "created_at": "2026-05-02T00:00:00Z"
}
```

`document_type` 可选值建议包括：

- `resume`
- `job_description`
- `application_note`
- `interview_note`

## 检索策略

- JD 分析：优先检索岗位相关历史记录和岗位知识片段。
- 简历匹配：同时检索简历片段和 JD 片段，生成证据化评分。
- 简历优化：检索目标岗位要求、候选人经历和缺口信息。
- 面试问题生成：检索简历项目片段、JD 要求和匹配缺口。

## 测试要求

- 文档解析测试不依赖真实简历隐私数据。
- Embedding 和 Qdrant 调用优先使用 fake 或 mock。
- 检索排序和 payload 过滤应有单元测试。
- 默认测试不依赖外部网络或真实 API Key。
