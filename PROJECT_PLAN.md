# PKM 笔记助手项目规划

> 版本：v1.0
> 创建日期：2026-05-07
> 负责人：CTO

---

## 一、项目愿景

**目标**：构建一个可持续成长的本地知识操作系统（Second Brain）

**核心价值**：用户负责输入，系统负责组织

**系统能力**：
- 本地优先（Local First）
- Markdown 永久可迁移存储
- LLM 自动理解与结构化
- 向量数据库增强检索（可选）
- 自动知识合并与总结
- 面向 Agent 的长期演进架构

---

## 二、项目结构

```
pkb/
├── pkm-interface/     # React 前端（已存在基础框架）
├── pkm-service/       # FastAPI 后端（已存在基础框架）
└── knowledge_base/    # 知识库存储（运行时创建）
```

---

## 三、当前状态评估

### pkm-interface（前端）
| 模块 | 状态 | 说明 |
|------|------|------|
| 项目框架 | ✅ 完成 | Vite + React + TypeScript + Tailwind |
| 聊天 UI | ✅ 完成 | ChatArea, InputArea, Sidebar |
| 截图上传 | ✅ 完成 | drag-drop, file picker |
| AI 回复 | ⚠️ mock | 随机中文回复，需对接真实 API |
| 知识列表 | ⚠️ 基础 | 仅显示 mock 数据 |
| 移动端适配 | ✅ 完成 | use-mobile hook |

### pkm-service（后端）
| 模块 | 状态 | 说明 |
|------|------|------|
| FastAPI 框架 | ✅ 完成 | 路由已注册 |
| LLM Provider | ✅ 完成 | OpenAI/Ollama 兼容 |
| 内容采集 API | ✅ 完成 | POST /content/collect |
| 知识管理 API | ✅ 完成 | CRUD 已定义 |
| Session 管理 | ✅ 完成 | 会话上下文 |
| Markdown 存储 | ✅ 完成 | 文件系统持久化 |
| AI 任务队列 | ⚠️ 框架 | 需完善任务执行逻辑 |
| Scheduler | ❌ 缺失 | 每日/周/月任务调度 |
| 向量检索 | ❌ 缺失 | Milvus 集成 |

---

## 四、开发阶段规划

### Phase 1：核心功能打通（1-2 周）

**目标**：前后端对接，实现基本的知识采集→处理→存储流程

#### 1.1 前端对接真实后端 API
- 将前端 API base URL 指向本地后端
- 实现 `/content/collect` 接口对接
- 实现 `/knowledge` 列表获取
- 实现知识项详情查看

#### 1.2 后端任务处理完善
- 完善 `/ai/tasks` 任务执行逻辑
- 实现 OCR 任务（截图→文本）
- 实现内容摘要任务
- 实现自动标签任务

#### 1.3 知识生命周期流程
- 实现 Inbox → Permanent → Summary → Archive 流转
- 实现知识评分机制
- 实现知识关联建立

**验收标准**：
- 用户截图或输入文本 → 3-5 秒内完成处理 → 知识入库
- 知识可在前端列表中查看
- 知识包含：标题、摘要、标签、分类

---

### Phase 2：增强功能（2-3 周）

**目标**：实现知识复用、检索增强、定期总结

#### 2.1 检索系统
- 实现全文检索（Markdown 文件搜索）
- 实现 Tag 检索
- 实现 Related Link 检索
- 可选：Milvus 向量检索集成

#### 2.2 知识复用
- 实现知识合并任务（相似内容去重合并）
- 实现重复内容消解任务
- 实现知识关联推荐

#### 2.3 Scheduler 系统
- 每日总结任务
- 每周合并任务
- 每月回顾任务

**验收标准**：
- 可通过关键词搜索找到历史知识
- 相似知识可自动合并
- 系统每日自动生成知识报告

---

### Phase 3：高级特性（长期演进）

**目标**：构建真正的第二大脑系统

#### 3.1 Agent 增强
- 支持 Agent 自动采集内容
- 支持多模态内容理解
- 支持知识问答交互

#### 3.2 知识图谱
- 知识关系可视化
- 知识领域分析
- 知识盲区发现

#### 3.3 生态系统
- 插件系统
- Webhook 集成
- 更多 LLM Provider 支持

---

## 五、技术架构

### 5.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  Chat UI │ Input Area │ Sidebar │ Knowledge List            │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP API
┌────────────────────────────▼────────────────────────────────┐
│                     Backend (FastAPI)                         │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌───────────┐ │
│  │ Content │  │ Knowledge │  │ AI Tasks  │  │ Scheduler │ │
│  │ Collect │  │   API     │  │  Engine   │  │  (APSch)  │ │
│  └────┬────┘  └────┬─────┘  └─────┬─────┘  └─────┬─────┘ │
│       │             │              │               │        │
│  ┌────▼─────────────▼───────────────▼──────────────▼────┐ │
│  │              Service Layer                              │ │
│  │  ContentService │ KnowledgeService │ TaskService      │ │
│  └────┬─────────────┬───────────────○──────────────○────┘ │
│       │             │              │               │        │
│  ┌────▼─────────────▼───────────────▼──────────────▼────┐ │
│  │              Storage Layer                              │ │
│  │  MarkdownStorage  │  VectorStore (Optional Milvus)   │ │
│  └───────────────────────────────────────────────────────┘ │
│                          │                                   │
│  ┌───────────────────────▼───────────────────────────────┐ │
│  │                    LLM Layer                            │ │
│  │  OpenAI/Ollama  │  Vision  │  Embedding              │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 核心数据流

```
用户输入（截图/文本）
       ↓
内容预处理（OCR/清洗）
       ↓
LLM 内容理解（摘要/分类/标签）
       ↓
知识标准化（统一 Frontmatter）
       ↓
Markdown 持久化存储
       ↓
可选：Embedding + 向量索引
       ↓
知识召回（语义/关键词检索）
       ↓
周期性与 AI 任务（合并/总结/归档）
```

### 5.3 Markdown 存储规范

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

### 5.4 目录结构

```
knowledge_base/
├── inbox/              # 临时输入区（未处理）
├── fleeting_notes/      # 快速记录
├── literature_notes/     # 阅读笔记
├── permanent_notes/     # 永久知识
├── project_notes/       # 项目知识
├── summaries/
│   ├── daily/          # 每日总结
│   ├── weekly/         # 每周总结
│   └── monthly/        # 每月总结
└── archive/            # 归档
```

---

## 六、技术选型

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | React 18 + TypeScript | 已有 |
| 前端构建 | Vite | 已有 |
| UI 样式 | Tailwind CSS + Radix UI | 已有 |
| 后端框架 | FastAPI | 已有 |
| LLM | OpenAI API / Ollama | 已有 provider |
| 定时任务 | APScheduler | 待集成 |
| 向量库 | Milvus（可选） | 待集成 |
| 存储 | Markdown + 文件系统 | 已有 |
| OCR | PaddleOCR / Tesseract | 待选型 |

---

## 七、API 核心接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/content/collect` | POST | 内容采集 |
| `/knowledge` | GET/POST | 知识列表/创建 |
| `/knowledge/{id}` | GET/PUT/DELETE | 知识 CRUD |
| `/knowledge/{id}/star` | POST | 收藏 |
| `/ai/tasks` | GET/POST | AI 任务管理 |
| `/sessions` | GET/POST/DELETE | 会话管理 |
| `/categories` | GET/POST/DELETE | 分类管理 |
| `/upload/image` | POST | 图片上传 |
| `/system/config` | GET/PUT | 系统配置 |

---

## 八、非功能需求

### 8.1 性能要求
- 单次知识处理（不含 LLM）：< 5s
- 知识检索响应：< 500ms

### 8.2 稳定性要求
- 先写文件，再更新索引
- Markdown 文件永不丢失

### 8.3 可迁移性要求
- 去掉向量库、LLM、服务端后，Markdown 文件仍完整可用

---

## 九、风险与依赖

| 风险/依赖 | 影响 | 缓解措施 |
|-----------|------|----------|
| LLM API 成本 | 高 | 本地 Ollama 支持 |
| OCR 准确性 | 中 | 多引擎备选 |
| 向量检索复杂度 | 中 | 先实现纯 Markdown 模式 |

---

## 十、后续行动

**立即执行（Phase 1）**：
1. 创建前后端对接子任务
2. 创建 AI 任务处理子任务
3. 创建知识生命周期子任务

**待 Phase 1 完成后**：
4. 创建检索系统子任务
5. 创建 Scheduler 子任务

**长期**：
6. 向量检索集成
7. Agent 增强
