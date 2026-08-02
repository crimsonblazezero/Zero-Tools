---
name: dws-report-entry-submit-pitfalls
description: DWS `report entry submit` 自动化提交模式：contents JSON 格式、contentType/type映射、重复key检查、附件上传流程。
tags: [dws, report, entry-submit, pitfalls]
---

# DWS Report Entry Submit — 自动化提交模式

## 目的
本文件记录通过 `dws report entry submit`（或 CLI wrapper）向钉钉日志模板批量写入内容的正确方法，以及高频坑点。

## 关键规则

### 1. `contentType` 必须与 `type` 匹配
| `type` | 含义 | `contentType` |
|--------|------|---------------|
| `1` | 文本 | `markdown` |
| `2` | 数字 | `origin` |
| `9` | 附件 | `origin` |

**错误示例**: `type: 1, contentType: "origin"` → 被拒绝，报 `business_error`  
**正确示例**: `type: 1, contentType: "markdown"`  
**正确示例**: `type: 2, contentType: "origin"`

### 2. `(key, sort)` 必须唯一
一份 `--contents-file` 中的每项，`key` + `sort` 组合不可重复。如果同一个模板字段出现两遍（例如给两个人各写一份同样的字段名），会报错：
```
[INPUT_INVALID_JSON] contents[18].content must be a string
```
这个错误信息具有误导性——实际原因是模板字段重复，不是内容类型不对。

**对策**: 多人场景请拆分为多个 JSON 文件分别提交，或使用 `--dd-from` / `--to-user-ids` 一次提交一份报告给团队。

### 3. 所有 `content` 值必须是字符串
即使字段是数字类型（`type=2`），`content` 也必须是字符串。提交前统一转义：
```python
item['content'] = str(item['content'])
```

### 4. 模板 `field_type=16` 需降级映射
模板里有些控件的 `field_type=16`（长文本/表格类），`entry submit` 不直接接受该值，会报错：
```
[INPUT_INVALID_JSON] contents[60].type="16" is invalid; use template get field_type
```
**对策**: 将其映射为 `type=1` + `contentType=markdown`

### 5. 上传附件后再提交
如果模板包含附件字段（`field_sort=56`），需要先通过 `dws drive upload --file-name` 上传，拿到 `fileId`，再填入 `content`：
```bash
dws drive upload --file-name "周报.xlsx" --file-path "./周报.xlsx"
# 返回: {"fileId": "pYLaezmVNeXkg99DtPP7gp2bWrMqPxX6", ...}

# JSON 中添加:
# {
#   "key": "附件",
#   "sort": "56",
#   "content": "pYLaezmVNeXkg99DtPP7gp2bWrMqPxX6",
#   "contentType": "origin",
#   "type": "9"
# }
```

## 完整提交流程

```bash
# Step 1: 读取模板结构
dws report template detail --name "运营周复盘（周一9:00前提交）" --format json

# Step 2: 生成 contents JSON（注意上述 1–4 规则）

# Step 3: 如果有附件，先上传获取 fileId
dws drive upload --file-name "运营周会数据收集_王祎.xlsx" \
  --file-path "C:\Users\...\运营周会数据收集_王祎.xlsx"

# Step 4: 验证 JSON
python -m json.tool dws_weekly_contents.json | grep -c '"sort"'  # 检查非空/无重复

# Step 5: 提交
dws report entry submit \
  --template-id <templateId> \
  --contents-file "<jsonPath>" \
  --yes \
  --format json

# 加 --verbose 获取更详细的错误定位
```

## 错误排查速查

| 错误片段 | 实际原因 | 解法 |
|---------|---------|------|
| `content must be a string` | (key, sort) 重复 | 确保 JSON 中每项唯一 |
| `contentType="text" is invalid for type=2` | contentType 和 type 不匹配 | type=1→markdown, type=2/9→origin |
| `type="16" is invalid` | 模板类型不支持 | 映射为 type=1+markdown |
| `success=false ... PARAM_ERROR` | 格式校验失败 | 加 `--verbose` 看具体 contents 位置 |
| `report entry submit` 返回 `business error` | 可能是上面任一原因 | 先验 (key,sort) 唯一性、再验 type/contentType 映射 |
