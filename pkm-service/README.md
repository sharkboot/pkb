# PKM Service

> PKM 知识管理系统的后端 API 服务

## 技术栈

| 技术 | 说明 |
|------|------|
| FastAPI | 高性能 API 框架 |
| Python 3.10+ | 后端语言 |
| Pydantic | 数据验证 |
| APScheduler | 定时任务调度 |
| python-frontmatter | Markdown 解析 |
| OpenAI SDK | LLM 集成 |

## 快速开始

```bash
# 进入目录
cd pkm-service

# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env  # 或手动创建 .env 文件

# 启动服务
python -m uvicorn src.main:app --reload --port 8000
```

服务启动后：
- API 地址：http://localhost:8000
- Swagger 文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc

## 项目结构

```
src/
├── api/                 # API 路由
│   ├── __init__.py     # 路由聚合
│   ├── content.py      # 内容采集接口
│   ├── sessions.py     # 会话管理接口
│   ├── knowledge.py    # 知识管理接口
│   ├── ai.py           # AI 任务接口
│   ├── files.py        # 文件操作接口
│   ├── categories.py   # 分类管理接口
│   └── system.py       # 系统配置接口
├── core/
│   └── config.py       # 配置管理
├── models/
│   ├── enums.py        # 枚举定义
│   ├── schemas.py      # Pydantic 模型
│   └── exceptions.py   # 自定义异常
├── services/           # 业务逻辑层
│   ├── content_service.py
│   ├── session_service.py
│   ├── knowledge_service.py
│   ├── task_service.py
│   ├── category_service.py
│   ├── file_service.py
│   └── system_service.py
├── storage/            # 存储层
│   ├── base_storage.py
│   └── markdown_storage.py
├── llm/
│   └── provider.py     # LLM 提供者抽象
└── main.py            # 应用入口
```

## API 接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/v1/content/collect` | POST | 内容采集 |
| `/api/v1/knowledge` | GET/POST | 知识列表/创建 |
| `/api/v1/knowledge/{id}` | GET/PUT/DELETE | 知识 CRUD |
| `/api/v1/knowledge/{id}/star` | POST | 收藏知识 |
| `/api/v1/knowledge/{id}/restore` | POST | 恢复知识 |
| `/api/v1/knowledge/{id}/permanent` | DELETE | 彻底删除 |
| `/api/v1/ai/tasks` | GET/POST | AI 任务管理 |
| `/api/v1/ai/tasks/{id}` | GET | 获取任务状态 |
| `/api/v1/sessions` | GET/POST | 会话列表/创建 |
| `/api/v1/sessions/{id}` | DELETE | 删除会话 |
| `/api/v1/categories` | GET/POST | 分类列表/创建 |
| `/api/v1/categories/{id}` | DELETE | 删除分类 |
| `/api/v1/files/md/{id}` | GET | 获取 Markdown 文件 |
| `/api/v1/files/md/merge` | POST | 合并 Markdown |
| `/api/v1/files/export` | POST | 导出知识库 |
| `/api/v1/upload/image` | POST | 上传图片 |
| `/api/v1/system/config` | GET/PUT | 系统配置 |

详细文档见 [docs/API接口文档.md](docs/API接口文档.md)

## 配置说明

在项目根目录创建 `.env` 文件：

```env
# 服务器配置
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true

# 知识库路径
KNOWLEDGE_BASE_PATH=./knowledge_base
MARKDOWN_PATH=./knowledge_base

# LLM 配置
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4

# Vision 模型（OCR）
VISION_API_KEY=your-api-key
VISION_BASE_URL=https://api.openai.com/v1
VISION_MODEL_NAME=gpt-4o

# 向量存储（可选）
VECTOR_STORE_ENABLED=false
VECTOR_STORE_TYPE=milvus
VECTOR_STORE_HOST=localhost
VECTOR_STORE_PORT=19530

# 自动任务
AUTO_MERGE=true
AUTO_SUMMARY=true
```

## AI 任务类型

| 任务类型 | 说明 |
|----------|------|
| ocr | OCR 文字识别 |
| summary | 内容总结 |
| tag | 自动标签 |
| merge | 知识合并 |
| archive | 自动归档 |
| vector_index | 向量索引 |
| deduplication | 重复内容消解 |
| weekly_summary | 周总结 |
| monthly_summary | 月总结 |

## Markdown 存储格式

```markdown
---
id: UUID
title: 知识标题
tags:
  - 标签1
  - 标签2
category: Permanent Note
source: screenshot|text|web|pdf|image|manual|agent
created_at: 2026-05-07
updated_at: 2026-05-07
score: 0.92
related:
  - 关联知识1
  - 关联知识2
status: draft|active|archived|deleted
---

# 知识标题

正文内容...
```

## 开发说明

### 路由注册

所有路由在 `src/api/__init__.py` 中聚合：

```python
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(content_router)
api_router.include_router(sessions_router)
api_router.include_router(knowledge_router)
api_router.include_router(ai_router)
api_router.include_router(files_router)
api_router.include_router(categories_router)
api_router.include_router(system_router)
```

### 新增 API 步骤

1. 在对应模块创建路由文件（如 `api/knowledge.py`）
2. 在 `services/` 下创建业务逻辑
3. 在 `src/api/__init__.py` 中注册路由

## 参考

- [项目主 README](../README.md)
- [项目说明](docs/项目说明.txt)
- [API 接口文档](docs/API接口文档.md)
