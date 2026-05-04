# PKM 知识管理系统接口文档

> 版本：v2.0.0
> 更新日期：2026-05-03
> 基础路径：`/api/v1`

---

# 一、接口概述

本接口文档定义了 PKM（Personal Knowledge Management）知识管理系统的核心 API。

系统围绕：

* 内容采集（Content Collect）
* 会话管理（Session）
* 知识管理（Knowledge）
* AI任务处理（AI Tasks）
* Markdown 文件持久化（Markdown Files）
* 分类管理（Categories）
* 系统配置（System Config）

展开，而非传统用户中心模式。

系统核心目标：

> 将碎片化内容沉淀为结构化知识，并通过 AI 自动完成整理、归档、合并与长期管理。

---

# 1.1 基础信息

| 项目     | 说明                   |
| ------ | -------------------- |
| 基础 URL | `/api/v1`            |
| 数据格式   | JSON                 |
| 字符编码   | UTF-8                |
| 文件上传   | multipart/form-data  |
| 存储核心   | Markdown + Vector DB |

---

# 1.2 通用响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

| 字段      | 类型     | 说明       |
| ------- | ------ | -------- |
| code    | int    | 状态码，0 成功 |
| message | string | 响应消息     |
| data    | object | 响应数据     |

---

# 1.3 分页响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [],
    "total": 100,
    "page": 1,
    "pageSize": 20
  }
}
```

---

# 1.4 错误码说明

| 错误码   | 说明       |
| ----- | -------- |
| 0     | 成功       |
| 10001 | 参数错误     |
| 20001 | 资源不存在    |
| 20002 | 资源已存在    |
| 30001 | AI任务执行失败 |
| 30002 | 文件处理失败   |
| 50000 | 系统内部错误   |

---

# 二、内容采集接口

内容采集是系统所有知识沉淀的入口。

支持：

* 截图
* 文本输入
* 图片上传
* 网页摘录
* PDF 文件
* 手动记录
* Agent 自动采集

---

## 2.1 内容采集

### 接口路径

`POST /content/collect`

### 功能描述

提交内容进入知识处理流水线。

### 请求参数

| 参数名         | 类型       | 必填 | 说明        |
| ----------- | -------- | -- | --------- |
| sourceType  | string   | 是  | 内容来源类型    |
| content     | string   | 否  | 文本内容      |
| images      | string[] | 否  | 图片 URL 列表 |
| attachments | string[] | 否  | 附件列表      |
| metadata    | object   | 否  | 扩展元信息     |

### sourceType 枚举

* screenshot
* text
* web
* pdf
* image
* manual
* agent

### 请求示例

```json
{
  "sourceType": "screenshot",
  "content": "这是一次截图内容记录",
  "images": ["https://example.com/image.jpg"],
  "attachments": [],
  "metadata": {
    "source": "browser"
  }
}
```

---

# 三、会话接口

用于管理内容处理过程中的上下文会话。

---

## 3.1 获取会话列表

### 接口路径

`GET /sessions`

### 功能描述

获取系统所有会话。

---

## 3.2 创建会话

### 接口路径

`POST /sessions`

### 请求参数

| 参数名   | 类型     | 必填 | 说明   |
| ----- | ------ | -- | ---- |
| title | string | 否  | 会话标题 |

---

## 3.3 删除会话

### 接口路径

`DELETE /sessions/{id}`

### 功能描述

删除会话及关联上下文。

---

# 四、知识管理接口

系统核心模块。

知识单元（Knowledge Unit）不是普通笔记，而是结构化知识对象。

支持：

* 自动总结
* 自动标签
* 自动知识合并
* 自动关系建立
* 长期知识演化

---

## 4.1 获取知识列表

### 接口路径

`GET /knowledge`

### 请求参数

| 参数名      | 类型     | 必填 | 说明    |
| -------- | ------ | -- | ----- |
| category | string | 否  | 分类    |
| keyword  | string | 否  | 搜索关键词 |
| page     | int    | 否  | 页码    |
| pageSize | int    | 否  | 每页数量  |

---

## 4.2 创建知识单元

### 接口路径

`POST /knowledge`

### 请求参数

```json
{
  "title": "React Hooks 最佳实践",
  "summary": "核心知识摘要",
  "content": "完整知识内容",
  "sourceRefs": [],
  "tags": ["React", "Frontend"],
  "relations": [],
  "status": "draft"
}
```

---

## 4.3 获取知识详情

### 接口路径

`GET /knowledge/{id}`

---

## 4.4 更新知识

### 接口路径

`PUT /knowledge/{id}`

---

## 4.5 删除知识

### 接口路径

`DELETE /knowledge/{id}`

---

## 4.6 收藏知识

### 接口路径

`POST /knowledge/{id}/star`

---

## 4.7 恢复知识

### 接口路径

`POST /knowledge/{id}/restore`

---

## 4.8 彻底删除知识

### 接口路径

`DELETE /knowledge/{id}/permanent`

---

# 五、AI任务接口

系统最核心模块。

用于驱动自动化知识处理流程。

没有该模块，系统仅是 CRUD。

有了该模块，系统才是真正 AI Native。

---

## 5.1 创建 AI 任务

### 接口路径

`POST /ai/tasks`

### 支持任务类型

* OCR
* 内容总结
* 自动标签
* 知识合并
* 周总结
* 月总结
* 自动归档
* 向量索引
* 重复内容消解
* Agent 自动执行

### 请求示例

```json
{
  "taskType": "summary",
  "targetId": "knowledge_001",
  "params": {
    "mode": "weekly"
  }
}
```

---

## 5.2 获取任务状态

### 接口路径

`GET /ai/tasks/{id}`

---

## 5.3 获取任务列表

### 接口路径

`GET /ai/tasks`

---

# 六、Markdown 文件接口

系统核心持久化模块。

最终知识以 Markdown 文件形式保存。

不是数据库 CRUD。

而是真实知识资产沉淀。

---

## 6.1 获取 Markdown 文件

### 接口路径

`GET /files/md/{id}`

---

## 6.2 手动触发合并

### 接口路径

`POST /files/md/merge`

### 功能描述

将碎片内容自动合并为结构化 Markdown 文档。

---

## 6.3 导出知识库

### 接口路径

`POST /files/export`

### 功能描述

导出完整本地知识库。

---

# 七、图片上传接口

---

## 7.1 上传图片

### 接口路径

`POST /upload/image`

### 内容类型

`multipart/form-data`

### 请求参数

| 参数名    | 类型     | 必填 | 说明   |
| ------ | ------ | -- | ---- |
| file   | File   | 是  | 图片文件 |
| folder | string | 否  | 上传目录 |

---

# 八、分类管理接口

---

## 8.1 获取分类列表

### 接口路径

`GET /categories`

---

## 8.2 创建分类

### 接口路径

`POST /categories`

---

## 8.3 删除分类

### 接口路径

`DELETE /categories/{id}`

---

# 九、系统配置接口

这里不是用户设置。

而是系统级配置。

包括：

* Markdown 存储路径
* 向量数据库配置
* LLM 模型配置
* Prompt 模板
* 自动合并策略
* 自动总结策略
* Agent 执行策略

---

## 9.1 获取系统配置

### 接口路径

`GET /system/config`

---

## 9.2 更新系统配置

### 接口路径

`PUT /system/config`

### 请求示例

```json
{
  "markdownPath": "/data/pkm/md",
  "vectorStore": "milvus",
  "defaultModel": "gpt-4",
  "autoMerge": true,
  "autoSummary": true
}
```

---

# 十、附录

## 10.1 内容来源类型

| 值          | 说明         |
| ---------- | ---------- |
| screenshot | 截图         |
| text       | 文本         |
| web        | 网页摘录       |
| pdf        | PDF        |
| image      | 图片         |
| manual     | 手动输入       |
| agent      | Agent 自动采集 |

---

## 10.2 知识状态枚举

| 值        | 说明  |
| -------- | --- |
| draft    | 草稿  |
| active   | 已沉淀 |
| archived | 已归档 |
| deleted  | 已删除 |

---

## 10.3 AI任务类型

| 值             | 说明    |
| ------------- | ----- |
| ocr           | OCR识别 |
| summary       | 内容总结  |
| merge         | 知识合并  |
| archive       | 自动归档  |
| vector_index  | 向量索引  |
| deduplication | 去重处理  |

---

