# IMA RAG 查询脚本

## 快速查询工具

`ima_query.js` 是一个命令行工具，用于快速搜索 IMA 知识库。

### 用法

```bash
# 搜索知识库中的内容
node ima_query.js "ACoS优化" 广告

# 搜索其他关键词
node ima_query.js "新品推广" 亚马逊
```

### 参数

- `query`: 搜索关键词
- `kb_name`: 知识库名称（用于搜索）

### 输出

- 显示匹配的知识库信息
- 显示前10条搜索结果
- 包含媒体ID，可用于后续获取原文

## 在 Hermes 中使用

重启 Hermes 后，MCP 工具将自动可用：

```
mcp__ima-knowledge-base_ima_search_knowledge_base(query="广告", limit=20)
mcp__ima-knowledge-base_ima_search_knowledge(query="ACoS", kb_id="知识库ID")
mcp__ima-knowledge-base_ima_get_media_info(media_id="媒体ID")
```
