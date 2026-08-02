---
name: ima-rag-setup
description: 配置IMA知识库作为Hermes RAG数据源，通过MCP服务器桥接IMA OpenAPI。
version: 1.0.0
tags: [ima, rag, knowledge-base, mcp]
---

# IMA RAG 知识库配置指南

## 概述
将腾讯IMA知识库集成为Hermes Agent的RAG数据源，通过自定义MCP服务器提供搜索、读取、添加内容能力。

## 1. 创建MCP服务器文件

### 位置
`~/.hermes/mcp-servers/ima-knowledge-base/`

### 文件结构
```
ima-knowledge-base/
├── server.js       # Node.js MCP服务器(ESM)
├── package.json    # 依赖: @modelcontextprotocol/sdk
├── run.sh          # Linux/macOS启动脚本
└── run.bat         # Windows启动脚本
```

### server.js 关键功能
- `ima_search_knowledge_base` - 搜索知识库列表
- `ima_get_knowledge_base_info` - 获取知识库详情
- `ima_search_knowledge` - 在知识库中搜索内容
- `ima_list_knowledge_contents` - 浏览知识库内容
- `ima_get_media_info` - 获取媒体访问信息
- `ima_add_url_to_kb` - 添加网页到知识库
- `ima_get_addable_knowledge_bases` - 获取可添加的知识库

### 凭证管理
支持三种方式（优先级从高到低）：
1. `env.IMA_CLIENT_ID` / `env.IMA_API_KEY`（配置在config.yaml中）
2. 环境变量 `IMA_OPENAPI_CLIENTID` / `IMA_OPENAPI_APIKEY`
3. 文件 `~/.config/ima/client_id` / `~/.config/ima/api_key`

## 2. 配置Hermes

在 `~/.hermes/config.yaml` 中添加：

```yaml
mcp_servers:
  ima-knowledge-base:
    command: node
    args:
      - "~/.hermes/mcp-servers/ima-knowledge-base/server.js"
    env:
      IMA_CLIENT_ID: "your_client_id"
      IMA_API_KEY: "your_api_key"
```

或手动设置（避免硬编码敏感信息）：
```bash
mkdir -p ~/.config/ima
echo "your_client_id" > ~/.config/ima/client_id
echo "your_api_key" > ~/.config/ima/api_key
```

## 3. 安装依赖
```bash
cd ~/.hermes/mcp-servers/ima-knowledge-base
npm install @modelcontextprotocol/sdk
```

## 4. 验证
```bash
hermes mcp list  # 确认 ima-knowledge-base 显示为 ✓ enabled
hermes mcp test ima-knowledge-base
```

## 5. 作为RAG源使用

### 方式A: MCP工具调用（新会话自动可用）
重启Hermes后，工具 `mcp__ima-knowledge-base_*` 自动注册，可直接调用搜索、读取等操作。

### 方式B: IMA Skill（现有能力）
- `ima-skills` skill 提供更完整的笔记和知识库管理
- 支持复杂工作流：上传文件、添加URL、批量操作
- 适合需要精细控制的场景

### 推荐使用场景
- **RAG查询**: 使用MCP工具搜索知识库内容
- **内容管理**: 使用Skill进行文件上传、URL导入等写入操作
- **混合使用**: MCP用于只读查询，Skill用于写入维护

## 6. 注意事项
- MCP服务器为stdio传输，需要Node.js环境
- 重启Hermes会话后新MCP工具才可用
- IMA OpenAPI有频率限制，建议缓存搜索结果
- 文件上传（>10MB）建议使用Skill而非MCP

## 相关文件
- `~/.hermes/mcp-servers/ima-knowledge-base/server.js` - MCP服务器
- `~/.claude/skills/ima-skills/` - IMA完整操作skill
- `ima_api.cjs` - IMA OpenAPI调用脚本
