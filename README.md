

---

<!-- PROJECT BADGES -->
<div align="center">
  <img src="https://raw.githubusercontent.com/sharkboot/pkb/main/.github/logo.svg" alt="PKB Logo" width="120" height="120" style="margin-bottom: 20px;"/>

  # PKB - 个人知识管理系统

  *Personal Knowledge Base - 让 AI 成为你的知识管理助手*

  [![GitHub stars](https://img.shields.io/github/stars/sharkboot/pkb?style=flat-square&logo=github)](https://github.com/sharkboot/pkb/stargazers)
  [![GitHub forks](https://img.shields.io/github/forks/sharkboot/pkb?style=flat-square&logo=github)](https://github.com/sharkboot/pkb/network/members)
  [![License](https://img.shields.io/github/license/sharkboot/pkb?style=flat-square)](https://github.com/sharkboot/pkb/blob/main/LICENSE)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)

  <p>
    <a href="#-核心特性">特性</a> •
    <a href="#-快速开始">快速开始</a> •
    <a href="#-项目架构">架构</a> •
    <a href="#-技术栈">技术栈</a> •
    <a href="#-贡献指南">贡献</a> •
    <a href="#-许可证">许可证</a>
  </p>
</div>

---

## 🎯 项目简介

PKB (Personal Knowledge Base) 是一个开源的个人知识管理平台，旨在将碎片化内容沉淀为结构化知识。系统通过 AI 自动完成内容整理、归档、合并与长期管理，让你的知识管理更加智能化。

> *"将碎片化内容沉淀为结构化知识，并通过 AI 自动完成整理、归档、合并与长期管理。"*

---

## ✨ 核心特性

<table>
<tr>
<td valign="top">

### 📸 多模态内容采集
- 支持截图、图片上传
- 文本输入与网页摘录
- PDF 文件解析
- Agent 自动采集

</td>
<td valign="top">

### 🤖 AI 智能处理
- OCR 文字识别
- 自动内容总结
- 智能标签生成
- 知识自动合并

</td>
</tr>
<tr>
<td valign="top">

### 📚 结构化知识管理
- Markdown 文件持久化
- 向量数据库检索
- 知识关系图谱
- 自动归档与去重

</td>
<td valign="top">

### 💬 对话式交互
- 聊天风格 Q&A 界面
- 基于知识库的智能问答
- 多会话管理
- 收藏与分类

</td>
</tr>
</table>

---

## 🚀 快速开始

### 环境要求

| 组件 | 版本要求 |
|------|----------|
| Node.js | ≥ 18.0.0 |
| Python | ≥ 3.10 |
| pnpm | ≥ 8.0 |
| PostgreSQL | ≥ 15 (可选) |

### 1. 克隆项目

```bash
git clone https://github.com/sharkboot/pkb.git
cd pkb
```

### 2. 安装前端依赖

```bash
cd pkm-interface
pnpm install
```

### 3. 安装后端依赖

```bash
cd pkm-service
pip install -r requirements.txt
```

### 4. 启动服务

**启动前端 (开发模式)**

```bash
cd pkm-interface
pnpm dev
```

**启动后端**

```bash
cd pkm-service
python run.py
```

### 5. 访问应用

- 前端地址: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

---

## 🏗️ 项目架构

```
pkb/
├── pkm-interface/          # 前端应用 (React + TypeScript + Vite)
│   ├── src/
│   │   ├── components/     # React 组件
│   │   │   ├── ChatArea.tsx    # 聊天区域
│   │   │   ├── InputArea.tsx   # 输入区域
│   │   │   └── Sidebar.tsx     # 侧边导航
│   │   ├── lib/           # 工具库
│   │   ├── hooks/         # 自定义 Hooks
│   │   └── App.tsx        # 根组件
│   ├── public/            # 静态资源
│   └── package.json
│
├── pkm-service/           # 后端服务 (Python + FastAPI)
│   ├── src/
│   │   ├── api/          # API 路由
│   │   │   ├── ai.py         # AI 任务接口
│   │   │   ├── content.py     # 内容采集接口
│   │   │   ├── knowledge.py   # 知识管理接口
│   │   │   ├── sessions.py    # 会话管理接口
│   │   │   └── files.py       # 文件操作接口
│   │   ├── services/     # 业务逻辑
│   │   ├── models/       # 数据模型
│   │   ├── llm/          # LLM 提供者
│   │   └── main.py       # 应用入口
│   ├── docs/             # 文档
│   ├── knowledge_base/   # 知识库存储
│   └── requirements.txt
│
└── README.md
```

---

## 🛠️ 技术栈

### 前端技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| 框架 | React 18 + TypeScript | UI 框架 |
| 构建 | Vite 6 | 快速构建工具 |
| 样式 | Tailwind CSS 3.4 | 原子化 CSS |
| 组件 | Radix UI | 无状态 UI 组件 |
| 表单 | React Hook Form + Zod | 表单验证 |
| 图标 | Lucide React | 开源图标库 |
| 包管理 | pnpm | 高效包管理 |

### 后端技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| 框架 | FastAPI | 现代 Python Web 框架 |
| 语言 | Python 3.10+ | 高性能后端 |
| 数据库 | PostgreSQL | 关系型数据库 |
| 向量库 | Milvus / Chroma | 向量存储 |
| LLM | OpenAI / Ollama | 大语言模型 |

---

## 📖 API 接口概览

| 模块 | 描述 | 主要端点 |
|------|------|----------|
| 内容采集 | 碎片化内容入口 | `POST /api/v1/content/collect` |
| 会话管理 | 多会话上下文 | `GET/POST /api/v1/sessions` |
| 知识管理 | 知识单元 CRUD | `GET/POST /api/v1/knowledge` |
| AI 任务 | 自动化任务处理 | `POST /api/v1/ai/tasks` |
| 文件管理 | Markdown 持久化 | `GET /api/v1/files/md/{id}` |
| 系统配置 | 系统级配置 | `GET/PUT /api/v1/system/config` |

---

## 🌙 功能预览

<div align="center">
<img src="https://img.shields.io/badge/-深色模式-1a1a2e?style=for-the-badge" alt="Dark Mode"/>
<img src="https://img.shields.io/badge/-响应式设计-4a90d9?style=for-the-badge" alt="Responsive"/>
<img src="https://img.shields.io/badge/-实时协作-50c878?style=for-the-badge" alt="Real-time"/>
</div>

### 主要界面

- **聊天界面**: 支持截图上传、文本输入
- **侧边栏**: 分类导航 (全部/最近/收藏/回收站)
- **知识库**: 结构化知识展示与管理
- **设置**: 深色/浅色模式切换

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

感谢以下开源项目：

- [React](https://react.dev/) - UI 框架
- [Vite](https://vitejs.dev/) - 构建工具
- [FastAPI](https://fastapi.tiangolo.com/) - Python Web 框架
- [Tailwind CSS](https://tailwindcss.com/) - CSS 框架
- [Radix UI](https://www.radix-ui.com/) - UI 组件库
- [Lucide](https://lucide.dev/) - 图标库

---

<div align="center">
  <p>
    <strong>如果这个项目对你有帮助，欢迎 ⭐ Star！</strong>
  </p>

  [![Star History](https://api.star-history.com/svg?repos=sharkboot/pkb&type=Date)](https://github.com/sharkboot/pkb/stargazers)
</div>

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/sharkboot">sharkboot</a>
</p>
