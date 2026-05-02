# API 设计

## 设计原则

- API route 只负责 HTTP 语义，不承载核心业务逻辑。
- 所有请求和响应都使用 Pydantic schema。
- 每个新增 API 必须配套 service/tool 逻辑和 pytest 测试。
- 外部模型、Qdrant 和数据库调用应封装在明确的模块边界内。

## 当前接口

### 健康检查

```http
GET /health
```

用途：验证 FastAPI 应用已启动，并返回当前应用名称和环境。

响应示例：

```json
{
  "status": "ok",
  "app_name": "JobPilot-Agent",
  "environment": "local"
}
```

## 规划接口

### JD 分析

```http
POST /jd/analyze
```

输入：岗位 JD 文本。

输出：岗位职责、硬性要求、软性要求、关键词、风险提示和结构化岗位画像。

### 简历匹配

```http
POST /resume/match
```

输入：JD 信息、简历文本或简历文档引用。

输出：匹配分、匹配证据、缺口证据、优化建议。

### 简历优化

```http
POST /resume/optimize
```

输入：JD 信息、简历内容、目标岗位方向。

输出：优化后的 bullet 建议、改写理由和注意事项。

### 面试问题生成

```http
POST /interview/questions
```

输入：JD、简历、匹配结果。

输出：技术问题、项目深挖问题、行为面问题和参考回答方向。

### 投递记录管理

```http
GET /applications
POST /applications
PATCH /applications/{application_id}
```

用途：管理公司、岗位、投递状态、时间线和备注。

## 错误响应

后续统一错误响应建议包含：

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request payload is invalid.",
  "detail": {}
}
```

错误处理应集中在 `app/core/`，避免在 route 中散落重复异常逻辑。
