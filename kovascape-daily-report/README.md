# KovaScape Daily Report — 项目结构

> 自动生成每日 KovaScape 亚马逊运营日报 · 推送至钉钉 + 生成待办

## 📁 目录结构

```
kovascape-daily-report/
├── config.yaml              # ✅ 已建：所有配置（店铺/阈值/规则/钉钉/归属人）
├── scripts/
│   ├── main.py              # ⏳ 入口：调度 + 串联各模块
│   ├── data_layer.py        # ✅ 数据聚合层（领星 MCP + MockDataSource）
│   ├── rule_engine.py       # ✅ 规则引擎（8 条 P0 + OwnerResolver）
│   ├── html_renderer.py     # ⏳ 渲染 HTML 报告
│   ├── todo_dispatcher.py   # ⏳ dws 待办创建器
│   └── webhook_pusher.py    # ⏳ 钉钉 Action Card 推送
├── output/                  # ✅ 生成的快照和告警归档
│   ├── snapshot-2026-07-26.json
│   └── alerts-2026-07-26.json
├── logs/                    # ⏳ 日志目录
└── README.md                # 本文件
```

## 🚀 进度

- [x] **W1**：HTML 原型 + 版式确认（`outputs/daily-report-mock-*.html`）
- [x] **配置层**：`config.yaml` 已建（含归属人机制 + Listing owner overrides）
- [x] **W2 数据层**：`data_layer.py` ✅ 跑通 mock（15 sid × 多维度聚合）
- [x] **W2 规则层**：`rule_engine.py` ✅ 跑通 mock（8 条 P0 实现，输出 6 个 alerts）
- [x] **钉钉 webhook**：✅ 已验证连通（关键词 "广告"，用 file-based JSON 避免编码问题）
- [x] **dws userId 解析**：✅ 王祎 17566881508928543 / 化一博 17597998065506150
- [ ] **W2 渲染层**：`html_renderer.py` 模板填充
- [ ] **W2 待办层**：`todo_dispatcher.py` dws create_task
- [ ] **W2 推送层**：`webhook_pusher.py` 钉钉 Action Card
- [ ] **W3 部署**：cron 调度 + 自动更新

## 🧪 本地跑通（mock 模式）

```bash
# 1. 数据聚合
D:/AgentSystem/.workbuddy/binaries/python/envs/kovascape/Scripts/python.exe \
  scripts/data_layer.py mock 2026-07-26

# 2. 规则引擎
D:/AgentSystem/.workbuddy/binaries/python/envs/kovascape/Scripts/python.exe \
  scripts/rule_engine.py

# 输出：output/snapshot-2026-07-26.json + output/alerts-2026-07-26.json
```

最新一次跑通触发了 **6 个 P0 alerts**（mock 场景）：
- R01 缺货 × 3（US BLACK-30 / US WALNUT-50 / DE BLACK-40）
- R02 毛利润<0 × 1（US BLACK-30）
- R04 Buybox 丢失 × 1（US BLACK-30）
- R06 退款率异常 × 1（US WALNUT-50）

## ⚙️ 待补的 3 件事

| 项 | 在哪里改 | 怎么查 |
|---|---|---|
| **listing_owner 实际映射** | `config.yaml > lingxing.listing_owner_overrides` | 领星 Listing 列表 → 导出"负责人"字段 |
| **领星 MCP 凭证** | 领星 OpenAPI token（独立运行时需要） | 领星 → 设置 → API → 申请 |
| **关键词 / 加签 secret 验证** | 已确认关键词 = "广告"，无需 secret | — |

## 📖 关联文档

| 文档 | 路径 |
|---|---|
| 预警模板配置手册 v1 | `outputs/KovaScape-预警模板配置手册-v1.md` |
| 批次 1 P0 配置指令 | `outputs/KovaScape-批次1-P0配置指令.md` |
| 日报设计 v1 | `outputs/KovaScape-日报设计-v1.md` |
| 项目基线（IMA） | IMA note_id=7486596249051459 |
| **新：** 钉钉 webhook 推送 | `~/.workbuddy/skills/dingtalk-webhook/SKILL.md` |

## 🔒 安全规则（遵守 Zero 的红线）

1. **不直接写 ADS-API**：所有广告写操作必须 dry-run + Zero 批准
2. **MCP 只读**：领星数据修改只能走 Web UI 手动
3. **dws 写操作需谨慎**：脚本默认 `--yes` 跳过确认，但所有待办创建会先打印清单
4. **Webhook 关键词必须出现在消息正文**：用 file-based JSON 避免 shell 转义问题

## 🎯 验收标准

| 指标 | 目标 |
|---|---|
| 日报生成成功率 | ≥ 99%（失败立刻钉钉告警） |
| 数据延迟 | ≤ 1 小时（13:00 北京 = 美西 04:00 数据） |
| 行动项完成率 | ≥ 80%（dws 待办按期完成） |
| 运营日均操作时间减少 | ≥ 30 分钟/天 |
| 人均管 SKU | 翻倍（化一博单人从 48 ASIN + 30 MSKU 管到 96/60） |