#!/usr/bin/env node
/**
 * IMA Knowledge Base MCP Server
 * 提供腾讯IMA知识库的搜索、读取、上传能力
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs";
import path from "path";

const BASE_URL = "https://ima.qq.com";
const DEFAULT_CREDENTIALS_PATH = path.join(process.env.HOME || process.env.USERPROFILE || ".", ".config", "ima");

// 凭证加载
function loadCredentials() {
  const clientId =
    process.env.IMA_CLIENT_ID ||
    process.env.IMA_OPENAPI_CLIENTID ||
    fs.readFileSync(path.join(DEFAULT_CREDENTIALS_PATH, "client_id"), "utf8").trim();
  const apiKey =
    process.env.IMA_API_KEY ||
    process.env.IMA_OPENAPI_APIKEY ||
    fs.readFileSync(path.join(DEFAULT_CREDENTIALS_PATH, "api_key"), "utf8").trim();
  return { clientId, apiKey };
}

// API 调用
async function imaApi(apiPath, body, credentials) {
  const res = await fetch(`${BASE_URL}/${apiPath}`, {
    method: "POST",
    headers: {
      "ima-openapi-clientid": credentials.clientId,
      "ima-openapi-apikey": credentials.apiKey,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return await res.json();
}

// 工具定义
const TOOLS = [
  {
    name: "ima_search_knowledge_base",
    description: "搜索IMA知识库列表，支持按名称搜索",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "搜索关键词，空字符串返回全部" },
        cursor: { type: "string", description: "分页游标，首次传空字符串" },
        limit: { type: "number", description: "返回数量限制，1-20" },
      },
      required: ["query"],
    },
  },
  {
    name: "ima_get_knowledge_base_info",
    description: "获取指定知识库的详细信息",
    inputSchema: {
      type: "object",
      properties: {
        kb_ids: {
          type: "array",
          items: { type: "string" },
          description: "知识库ID列表（1-20个）",
        },
      },
      required: ["kb_ids"],
    },
  },
  {
    name: "ima_search_knowledge",
    description: "在指定知识库中搜索内容",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "搜索关键词" },
        kb_id: { type: "string", description: "知识库ID" },
        cursor: { type: "string", description: "分页游标，首次传空字符串" },
      },
      required: ["query", "kb_id"],
    },
  },
  {
    name: "ima_list_knowledge_contents",
    description: "列出知识库中的内容（支持文件夹浏览）",
    inputSchema: {
      type: "object",
      properties: {
        kb_id: { type: "string", description: "知识库ID" },
        folder_id: { type: "string", description: "文件夹ID，省略则列根目录" },
        cursor: { type: "string", description: "分页游标，首次传空字符串" },
        limit: { type: "number", description: "返回数量限制，1-50" },
      },
      required: ["kb_id"],
    },
  },
  {
    name: "ima_get_media_info",
    description: "获取媒体内容的访问信息（用于查看/下载原文）",
    inputSchema: {
      type: "object",
      properties: {
        media_id: { type: "string", description: "媒体ID" },
      },
      required: ["media_id"],
    },
  },
  {
    name: "ima_add_url_to_kb",
    description: "添加网页或微信公众号文章到知识库",
    inputSchema: {
      type: "object",
      properties: {
        kb_id: { type: "string", description: "知识库ID" },
        urls: {
          type: "array",
          items: { type: "string" },
          description: "URL列表（1-10个）",
        },
        folder_id: { type: "string", description: "目标文件夹ID，省略则添加到根目录" },
      },
      required: ["kb_id", "urls"],
    },
  },
  {
    name: "ima_get_addable_knowledge_bases",
    description: "获取当前用户有权限添加内容的知识库列表",
    inputSchema: {
      type: "object",
      properties: {
        cursor: { type: "string", description: "分页游标，首次传空字符串" },
        limit: { type: "number", description: "返回数量限制，1-50" },
      },
    },
  },
];

async function main() {
  const credentials = loadCredentials();
  
  const server = new Server(
    {
      name: "ima-knowledge-base",
      version: "1.0.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // 工具列表
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return { tools: TOOLS };
  });

  // 工具调用
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      switch (name) {
        case "ima_search_knowledge_base": {
          const result = await imaApi(
            "openapi/wiki/v1/search_knowledge_base",
            {
              query: args.query,
              cursor: args.cursor || "",
              limit: args.limit || 20,
            },
            credentials
          );
          return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
        }

        case "ima_get_knowledge_base_info": {
          const result = await imaApi(
            "openapi/wiki/v1/get_knowledge_base",
            { ids: args.kb_ids },
            credentials
          );
          return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
        }

        case "ima_search_knowledge": {
          const result = await imaApi(
            "openapi/wiki/v1/search_knowledge",
            {
              query: args.query,
              knowledge_base_id: args.kb_id,
              cursor: args.cursor || "",
            },
            credentials
          );
          return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
        }

        case "ima_list_knowledge_contents": {
          const result = await imaApi(
            "openapi/wiki/v1/get_knowledge_list",
            {
              knowledge_base_id: args.kb_id,
              folder_id: args.folder_id,
              cursor: args.cursor || "",
              limit: args.limit || 20,
            },
            credentials
          );
          return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
        }

        case "ima_get_media_info": {
          const result = await imaApi(
            "openapi/wiki/v1/get_media_info",
            { media_id: args.media_id },
            credentials
          );
          return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
        }

        case "ima_add_url_to_kb": {
          const result = await imaApi(
            "openapi/wiki/v1/import_urls",
            {
              knowledge_base_id: args.kb_id,
              urls: args.urls,
              folder_id: args.folder_id,
            },
            credentials
          );
          return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
        }

        case "ima_get_addable_knowledge_bases": {
          const result = await imaApi(
            "openapi/wiki/v1/get_addable_knowledge_base_list",
            {
              cursor: args.cursor || "",
              limit: args.limit || 20,
            },
            credentials
          );
          return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
        }

        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      return {
        content: [{ type: "text", text: `Error: ${error.message}` }],
        isError: true,
      };
    }
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("Failed to start server:", error);
  process.exit(1);
});
