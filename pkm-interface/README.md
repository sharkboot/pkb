# PKM Interface

> PKM 知识管理系统的前端界面

## 技术栈

| 技术 | 说明 |
|------|------|
| React 18 | UI 框架 |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| Tailwind CSS | 样式框架 |
| Radix UI | UI 组件库 |
| Lucide React | 图标库 |

## 快速开始

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 生产构建
pnpm build

# 代码检查
pnpm lint

# 预览构建
pnpm preview

# 清洁安装
pnpm clean
```

## 项目结构

```
src/
├── components/       # React 组件
│   ├── ChatArea.tsx    # 聊天区域
│   ├── InputArea.tsx   # 输入区域
│   ├── Sidebar.tsx     # 侧边栏
│   └── ErrorBoundary.tsx
├── hooks/           # 自定义 Hooks
│   └── use-mobile.tsx
├── lib/             # 工具函数
│   └── utils.ts
├── App.tsx          # 根组件
└── main.tsx        # 入口文件
```

## 主要功能

- **截图上传**：支持拖拽或文件选择器上传截图/图片
- **文本记录**：支持分类的文本笔记输入
- **聊天式问答**：基于 AI 助手的问答界面（需对接后端 API）
- **深色/浅色模式**：主题切换
- **移动端适配**：响应式侧边栏导航
- **知识组织**：收藏、最近访问、分类管理

## 开发说明

### 组件结构

- `App.tsx` - 根组件，管理全局状态（消息、深色模式、移动端菜单）
- `ChatArea.tsx` - 显示聊天消息，支持复制和反馈操作
- `InputArea.tsx` - 双面板输入：截图上传区 + 文本输入
- `Sidebar.tsx` - 分类导航（全部、最近、收藏、回收站）和最近项目

### 状态流

`App.tsx` 持有顶层状态并将回调传递给子组件：
- `messages` 状态传递给 `ChatArea` 显示
- `InputArea` 中的 `handleSend` 回调触发消息创建

### 路径别名

```typescript
"@": path.resolve(__dirname, "./src")
```

所有导入可使用 `@/` 前缀替代相对路径。

## 待完成

- [ ] 对接真实后端 API
- [ ] 知识列表真实数据展示
- [ ] AI 回复真实调用

## 参考

- [项目主 README](../README.md)
- [CLAUDE.md](./CLAUDE.md) - Claude Code 开发指南
