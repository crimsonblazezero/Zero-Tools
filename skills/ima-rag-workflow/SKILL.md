---
name: ima-rag-workflow
description: 基于IMA知识库回答亚马逊广告问题的完整工作流，区分MCP和Skill的使用场景。
---

# IMA RAG 工作流：亚马逊广告问答

## 核心原则

**MCP 用于只读查询，Skill 用于写入操作**

| 操作类型 | 工具 | 原因 |
|---------|------|------|
| 搜索知识库/内容 | MCP | 快速、自动、集成到对话流 |
| 读取媒体信息 | MCP | 获取原文访问链接 |
| 上传文件/添加URL | Skill | 需要安全门控、重名检查、COS上传 |
| 批量操作 | Skill | 有专门的脚本和错误处理 |

---

## 工作流架构

```
用户提问（亚马逊广告相关）
    │
    ├─→ 1. 搜索知识库（MCP）
    │       mcp__ima-knowledge-base_ima_search_knowledge_base(query="ACoS")
    │
    ├─→ 2. 获取知识库信息（MCP）
    │       mcp__ima-knowledge-base_ima_get_knowledge_base_info(kb_ids=["Oz8mTK0..."])
    │
    ├─→ 3. 搜索知识库内容（MCP）
    │       mcp__ima-knowledge-base_ima_search_knowledge(query="ACoS优化", kb_id="Oz8mTK0...")
    │
    ├─→ 4. 获取原文内容（MCP + Skill）
    │       MCP: mcp__ima-knowledge-base_ima_get_media_info(media_id="...")
    │       Skill: 读取笔记内容或下载PDF
    │
    └─→ 5. 综合回答 + 现实数据验证
            结合 IMA 知识库 + 领星MCP 广告数据
```

---

## Step 1: 搜索知识库（发现阶段）

**触发条件**: 用户提问涉及亚马逊广告概念、策略、问题诊断

**MCP 调用**:
```
mcp__ima-knowledge-base_ima_search_knowledge_base(
  query="广告",
  limit=20
)
```

**返回示例**:
```json
{
  "info_list": [
    {
      "kb_name": "亚马逊广告最全知识库",
      "kb_id": "Oz8mTK0umBKnPPkSawK7vj9URb1UaMVveqR7x3JX4Vs=",
      "content_count": 1884,
      "role_type": "普通成员"
    }
  ]
}
```

**处理逻辑**:
- 如果找到相关知识库 → 记录 kb_id 用于后续搜索
- 如果没有 → 搜索具体关键词："ACoS"、"SP广告"、"新品推广"
- 如果有多个 → 选择内容最多的或最近更新的

---

## Step 2: 搜索知识库内容（精准检索）

**触发条件**: 已知 kb_id，需要查找具体答案

**MCP 调用**:
```
mcp__ima-knowledge-base_ima_search_knowledge(
  query="ACoS过高怎么办",
  kb_id="Oz8mTK0umBKnPPkSawK7vj9URb1UaMVveqR7x3JX4Vs=",
  cursor=""
)
```

**优化策略**:
- 使用用户提问中的核心关键词
- 如果结果太多（>50条），使用更具体的词
- 关注搜索结果中的 `highlight_content` 字段

---

## Step 3: 获取原文内容

**触发条件**: 需要引用具体文章的内容

### 方式A: 微信公众号文章（media_type=6）

**MCP 调用**:
```
mcp__ima-knowledge-base_ima_get_media_info(
  media_id="wechatarticle_xxx_xxx"
)
```

**返回**: 包含原文 URL，可直接访问或总结

### 方式B: 笔记类型（media_type=11）

**MCP 调用**:
```
mcp__ima-knowledge-base_ima_get_media_info(
  media_id="note_xxx"
)
```

**返回**: `notebook_id` → 需要使用 notes 模块获取内容

**Skill 调用**:
```bash
ima_api "openapi/note/v1/get_doc_content" '{"note_id":"<notebook_id>","target_content_format":0}'
```

### 方式C: 文件类型（PDF/Word）

**MCP 调用**:
```
mcp__ima-knowledge-base_ima_get_media_info(
  media_id="media_xxx"
)
```

**返回**: 文件下载 URL → 使用 `browser_navigate` 或 `curl` 下载并分析

---

## Step 4: 现实数据验证（可选但推荐）

IMA 知识库提供理论/经验，领星 MCP 提供现实数据

**组合使用场景**:
1. 用户问："我的ACoS从20%涨到40%怎么办？"
2. IMA 搜索：找到"ACoS飙升原因分析"相关文章
3. 领星 MCP 验证：`ad_campaign_report` 查看当前广告表现
4. 综合回答：理论分析 + 实际数据建议

---

## 实际调用示例

### 示例1: 新手问"如何降低ACoS"

```
用户: 我的SP广告ACoS太高了，有什么优化方法？

助理:
1. 搜索知识库：
   mcp__ima-knowledge-base_ima_search_knowledge(query="ACoS优化", kb_id="...")
   
2. 找到相关文章：
   - "日均10-20单但利润都被广告吃掉了！如何快速降低广告占比？"
   - "告别'白烧钱'，亚马逊AMC为你送上广告降本增效爆单密码"

3. 获取原文：
   mcp__ima-knowledge-base_ima_get_media_info(media_id="...")

4. 综合领星数据（如有）：
   ad_campaign_report 查看当前广告表现

5. 回答：
   根据知识库和您的广告数据，建议：
   - 暂停高ACoS低转化的关键词
   - 优化出价策略（使用建议竞价）
   - 检查广告位加成是否合理
   - 参考具体操作方案...
```

### 示例2: 老手问"展示型推广怎么做"

```
用户: 展示型推广（SD）应该怎么搭建？

助理:
1. 搜索：
   mcp__ima-knowledge-base_ima_search_knowledge(query="展示型推广", kb_id="...")
   
2. 找到：
   - "亚马逊广告高阶'组合技'，为你揭开展示型推广的流量密码！"
   - "高出价≠高曝光！破解亚马逊新品广告三大迷思"

3. 回答策略：
   - 引用知识库内容
   - 结合您的店铺实际投放情况
   - 提供分阶段搭建建议
```

---

## 工具选择决策树

```
用户提问亚马逊广告问题
        │
        ▼
   需要理论知识/经验？
        │
   ┌────┴────┐
   │         │
  是        否
   │         │
   ▼         ▼
IMA知识库   直接回答
   │         │
   ▼         │
搜索知识库   │
   │         │
   ▼         │
获取原文   结束
   │         │
   └────┬────┘
        ▼
  需要验证现实数据？
        │
   ┌────┴────┐
   │         │
  是        否
   │         │
   ▼         ▼
领星MCP    综合回答
 查询      + IMA 引用
   │
   ▼
  最终回答
```

---

## 高级技巧

### 1. 缓存策略

```python
# 在skill中实现知识库缓存
cache = {
    "kb_id": "Oz8mTK0...",
    "search_results": {...},  # 最近搜索的结果
    "last_updated": timestamp
}
```

避免重复搜索相同的知识库

### 2. 上下文增强

将 IMA 搜索结果作为 context 注入回答：

```
根据「亚马逊广告最全知识库」中的内容：
- 文章《...》提到...
- 文章《...》建议...

结合您的实际情况（领星数据）...
```

### 3. 多知识库协作

用户可能有多个知识库：
- 亚马逊广告最全知识库（理论）
- 视频号营销知识库（引流）
- 跨境电商知识库（选品）

**策略**: 按问题类型选择最相关的知识库

---

## 命令速查表

| 操作 | MCP 工具 | 参数 |
|-----|---------|------|
| 搜索知识库 | `ima_search_knowledge_base` | query, limit |
| 获取知识库详情 | `ima_get_knowledge_base_info` | kb_ids |
| 搜索内容 | `ima_search_knowledge` | query, kb_id |
| 浏览内容 | `ima_list_knowledge_contents` | kb_id, folder_id |
| 获取原文 | `ima_get_media_info` | media_id |
| 添加URL | `ima_add_url_to_kb` | kb_id, urls |

---

## 注意事项

1. **凭证管理**: MCP 服务器已配置，无需手动传递
2. **频率限制**: IMA API 有频率限制，避免频繁调用
3. **内容时效**: 知识库内容可能有时间滞后，重要决策需结合现实数据
4. **版权注意**: 引用内容注明来源，不要直接复制全文

---

## 总结

**MCP 适合**:
- 搜索和查询
- 快速获取原文链接
- 自动化工作流

**Skill 适合**:
- 文件上传
- 复杂写入操作
- 批量管理

**最佳实践**:
- MCP 查询 → 结合领星数据 → 综合回答
- 理论 + 现实数据 = 最有价值的建议
