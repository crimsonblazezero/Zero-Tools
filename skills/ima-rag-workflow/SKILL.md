---
name: ima-rag-workflow
description: 基于IMA知识库回答亚马逊广告问题的完整工作流，区分MCP查询和Skill写入。
---

# IMA RAG 工作流：亚马逊广告问答

## 核心原则
- **MCP 用于只读查询**：搜索、浏览、获取原文链接
- **Skill 用于写入操作**：上传文件、添加URL、批量管理

## 快速决策表

| 场景 | 工具 | 原因 |
|-----|------|------|
| 搜索知识库 | MCP | 快速、自动集成 |
| 搜索内容 | MCP | 精准定位 |
| 获取原文 | MCP | 返回访问链接 |
| 上传文件 | Skill | 需要安全门控 |
| 添加URL | Skill | 需要格式校验 |

## 标准调用流程

```
1. 搜索知识库 → ima_search_knowledge_base(query="广告")
2. 获取详情 → ima_get_knowledge_base_info(kb_ids=["..."])
3. 搜索内容 → ima_search_knowledge(query="ACoS", kb_id="...")
4. 获取原文 → ima_get_media_info(media_id="...")
5. 综合回答 + 领星MCP数据验证
```

## 关键示例

### 示例：降低ACoS问题
```
用户: ACoS从20%涨到40%怎么办？

助理:
1. 搜索: ima_search_knowledge(query="ACoS优化")
2. 获取原文: ima_get_media_info(media_id)
3. 领星验证: ad_campaign_report 查看实际数据
4. 综合建议
```

## 工具速查
- `ima_search_knowledge_base`: 搜索知识库列表
- `ima_search_knowledge`: 搜索知识库内容
- `ima_get_media_info`: 获取原文访问信息
- `ima_add_url_to_kb`: 添加网页到知识库（Skill方式）
