#!/usr/bin/env node
/**
 * IMA RAG 快速查询脚本
 * 用法: node ima_query.js "ACoS优化"
 */

const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://ima.qq.com';
const CRED_PATH = path.join(process.env.HOME || process.env.USERPROFILE || '.', '.config', 'ima');

function loadCredentials() {
  const clientId = fs.readFileSync(path.join(CRED_PATH, 'client_id'), 'utf8').trim();
  const apiKey = fs.readFileSync(path.join(CRED_PATH, 'api_key'), 'utf8').trim();
  return { clientId, apiKey };
}

async function searchKB(query, limit = 20) {
  const res = await fetch(`${BASE_URL}/openapi/wiki/v1/search_knowledge_base`, {
    method: 'POST',
    headers: {
      'ima-openapi-clientid': process.env.IMA_CLIENT_ID || loadCredentials().clientId,
      'ima-openapi-apikey': process.env.IMA_API_KEY || loadCredentials().apiKey,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query, cursor: '', limit })
  });
  return await res.json();
}

async function searchContent(query, kbId) {
  const res = await fetch(`${BASE_URL}/openapi/wiki/v1/search_knowledge`, {
    method: 'POST',
    headers: {
      'ima-openapi-clientid': process.env.IMA_CLIENT_ID || loadCredentials().clientId,
      'ima-openapi-apikey': process.env.IMA_API_KEY || loadCredentials().apiKey,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query, knowledge_base_id: kbId, cursor: '' })
  });
  return await res.json();
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.log('用法: node ima_query.js <query> <kb_name>');
    console.log('示例: node ima_query.js "ACoS优化" 广告');
    return;
  }

  const [query, kbName] = args;

  // Step 1: 搜索知识库
  console.log(`\n🔍 搜索知识库: "${kbName}"`);
  const kbResult = await searchKB(kbName);
  if (kbResult.code !== 0 || !kbResult.data?.info_list?.length) {
    console.log('❌ 未找到相关知识库');
    return;
  }

  const kb = kbResult.data.info_list[0];
  console.log(`✅ 找到: ${kb.kb_name} (内容数: ${kb.content_count})\n`);

  // Step 2: 搜索内容
  console.log(`🔎 搜索内容: "${query}"\n`);
  const contentResult = await searchContent(query, kb.kb_id);
  if (contentResult.code !== 0 || !contentResult.data?.info_list?.length) {
    console.log('❌ 未找到相关内容');
    return;
  }

  console.log('📄 搜索结果:');
  contentResult.data.info_list.slice(0, 10).forEach((item, i) => {
    console.log(`${i + 1}. ${item.title}`);
    if (item.highlight_content) {
      console.log(`   ${item.highlight_content.substring(0, 100)}...`);
    }
    console.log(`   ID: ${item.media_id}`);
    console.log('');
  });

  console.log(`共找到 ${contentResult.data.info_list.length} 条结果`);
}

main().catch(console.error);
