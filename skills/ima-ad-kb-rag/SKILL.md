---
name: ima-ad-kb-rag
description: 基于绯炎零的知识库（亚马逊广告+运营+AI提效）回答亚马逊广告问题的RAG工作流。
---

# IMA RAG 工作流：亚马逊广告知识库

## 知识库信息

| 属性 | 值 |
|-----|-----|
| 名称 | 绯炎零的知识库 |
| ID | `r10NZMjSyXNElF2hzzw3cQT4h8c80oUVFYUqKNMv8b8=` |
| 角色 | **创建者**（完全权限） |
| 总内容 | 1,645 条 |
| 广告文件夹 | `folder_7353712292939323` |
| 文件夹名称 | 亚马逊广告+运营+AI提效 |

### 子文件夹结构

```
绯炎零的知识库/
└── 亚马逊广告+运营+AI提效/
    ├── AMZ那些事/
    ├── 跨境随想/
    ├── 跨境AI入门指南/
    ├── 跨境电商策/
    ├── 从宇宙大爆炸到PPC/
    ├── (直接内容)
    │   ├── 亚马逊广告培训.pdf
    │   ├── 5000字深度解析亚马逊广告全链路
    │   ├── ACoS很高应从哪些方面找原因？
    │   └── ...
    └── ...
```

---

## 核心工具调用

### Step 1: 搜索知识库内容

```bash
# 使用 ima_api.cjs
ima_api "openapi/wiki/v1/search_knowledge" '{
  "query": "ACoS优化",
  "knowledge_base_id": "r10NZMjSyXNElF2hzzw3cQT4h8c80oUVFYUqKNMv8b8=",
  "cursor": ""
}'
```

### Step 2: 浏览特定文件夹

```bash
# 获取"亚马逊广告+运营+AI提效"文件夹内容
ima_api "openapi/wiki/v1/get_knowledge_list" '{
  "knowledge_base_id": "r10NZMjSyXNElF2hzzw3cQT4h8c80oUVFYUqKNMv8b8=",
  "folder_id": "folder_7353712292939323",
  "cursor": "",
  "limit": 50
}'
```

### Step 3: 获取原文内容

```bash
# 获取微信公众号文章原文
ima_api "openapi/wiki/v1/get_media_info" '{
  "media_id": "wechatarticle_bc1e4c42c50a5e48768f347af345e17e_8eaf0890fbb0cf681446e6fc97afcf98"
}'
```

---

## RAG 问答流程

### 场景：用户问"如何降低ACoS"

```
1. 搜索相关内容
   → ima_search_knowledge(query="ACoS优化", kb_id="r10NZMjSyX...")

2. 获取相关文档
   → 找到: "ACOS很高应从哪些方面找原因？又该如何降低？"
   → media_id: wechatarticle_bc1e4c42...8eaf0890fbb0cf681446e6fc97afcf98

3. 获取原文
   → ima_get_media_info(media_id="wechatarticle_bc1e4c42...")
   → 返回文章 URL

4. 综合分析
   → 结合领星MCP广告数据验证
   → 给出个性化建议
```

---

## 高频问题主题映射

| 用户问题 | 搜索关键词 | 预期返回 |
|---------|-----------|---------|
| ACoS优化 | "ACoS优化" | 20+篇相关文章 |
| 关键词选择 | "关键词" | 50+篇关键词策略 |
| 新品推广 | "新品广告" | 冷启动策略 |
| 广告架构 | "广告架构" | SP/SB/SD搭建 |
| 预算分配 | "预算" | 资金管理 |
| 否词技巧 | "否词" | 精准投放 |

---

## MCP 工具速查

| 工具 | 用途 | 参数 |
|-----|------|------|
| `ima_search_knowledge` | 搜索内容 | query, kb_id |
| `ima_get_media_info` | 获取原文 | media_id |
| `ima_list_knowledge_contents` | 浏览文件夹 | kb_id, folder_id |
| `ima_get_knowledge_base_info` | 获取详情 | kb_ids |

---

## 与领星MCP结合

IMA知识库提供**理论/经验**，领星MCP提供**现实数据**：

```
用户: 我的ACoS从20%涨到40%怎么办？

助理:
1. IMA搜索: "ACoS飙升原因" → 找到诊断方法论
2. 领星查询: ad_campaign_report → 查看实际数据
3. 综合建议: 理论框架 + 数据验证
```

---

## 快速查询脚本

```bash
# 搜索ACoS相关内容
cd /c/Users/Administrator/.hermes/mcp-servers/ima-knowledge-base
node ima_query.cjs "ACoS" 绯炎零
```

---

## 注意事项

1. **凭证安全**: 已配置在 `~/.config/ima/`，无需重复传递
2. **频率限制**: IMA API 有频率限制，避免频繁调用
3. **内容时效**: 知识库内容为历史经验，需结合现实数据验证
4. **版权注意**: 引用内容注明来源，不直接复制全文

---

## 重启后生效

重启 Hermes 后，以下工具自动可用：
- `mcp__ima-knowledge-base_ima_search_knowledge`
- `mcp__ima-knowledge-base_ima_get_media_info`
- `mcp__ima-knowledge-base_ima_list_knowledge_contents`
