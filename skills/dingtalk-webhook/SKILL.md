---
name: dingtalk-webhook
description: Send messages to DingTalk (钉钉) custom robots via webhook. Handles keyword mode and sign mode (加签), Chinese JSON escaping pitfalls, and message type variants (text/markdown/action card/feed).
---

# DingTalk Webhook 推送

## 何时使用
- 给钉钉群机器人发消息（Action Card / 文本 / Markdown）
- 测试自定义机器人是否连通
- 关键词模式 / 加签模式 / IP 白名单 三种安全设置的请求构造
- **关键陷阱**：内含中文的 JSON 必须用文件 payload，不能用 shell 内联

## 关键陷阱：中文 JSON 必须用文件

**❌ 内联 `--data-raw '{...中文...}'` 会失败**：

```bash
# shell 会把中文字符错误转义或编码
curl -X POST "$URL" --data-raw '{"msgtype":"text","text":{"content":"[日报] 关键词命中"}}'
# → 中文变成乱码 / 400 错误 / 关键词过滤失败
```

**✅ 用文件 + `--data-binary`**：

```bash
# 1. 写文件
echo '{"msgtype":"text","text":{"content":"广告 关键词命中"}}' > /tmp/msg.json

# 2. 用 --data-binary @file 发送
curl -X POST "$URL" \
  -H 'Content-Type: application/json; charset=utf-8' \
  --data-binary @/tmp/msg.json
```

**Node.js 替代方案**（更可靠）：

```javascript
const fs = require('fs');
fetch(WEBHOOK_URL, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json; charset=utf-8' },
  body: fs.readFileSync('/tmp/msg.json', 'utf8')
});
```

## 关键词模式探测

当 `errcode: 310000, errmsg: "关键词不匹配"` 时，说明机器人开了关键词过滤：

1. **先去群设置看**（群 → 智能群助手 → 机器人 → 安全设置 → 自定义关键词）
2. **批量探测脚本**：把候选关键词写到不同文件，循环 post 看哪个返回 `errcode: 0`
3. **可能同时启用加签**：如果所有关键词都失败但确认已配置，去看是否有加签 secret

## 加签模式（sign mode）

签名 URL 构造：

```python
import time, hmac, hashlib, base64, urllib.parse

def sign_url(webhook_url: str, secret: str) -> str:
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(secret.encode(), string_to_sign.encode(), digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return f"{webhook_url}&timestamp={timestamp}&sign={sign}"
```

## 支持的消息类型

| msgtype | 用途 |
|---|---|
| `text` | 纯文本 |
| `markdown` | Markdown 渲染 |
| `link` | 单条链接卡片 |
| `actionCard` | 多按钮行动卡片（日报摘要最常用） |
| `feedCard` | 多链接卡片 |

## Action Card 示例（含跳转链接）

```json
{
  "msgtype": "actionCard",
  "actionCard": {
    "title": "KovaScape 日报 2026-07-26",
    "text": "## 业绩\n销售额 $32,847 (↓3%)\n订单 1,205\n毛利 $9,856\n毛利率 30%\nTACoS 26% ⚠\n\n## 异常\nP0 × 6\n- 缺货 3 条\n- 毛利<0 1 条\n- Buybox 丢失 1 条\n- 退款率异常 1 条",
    "singleTitle": "查看完整日报",
    "singleURL": "https://kovascape.example.com/daily/2026-07-26.html",
    "btnOrientation": "0"
  }
}
```

## 速率限制

- 每分钟最多 20 条（`errcode: 660026, errmsg: "sending too many messages per minute"`）
- 批量测试时**每次循环 sleep 3-5 秒**或退避
- 一次失败不要立即重试，先 sleep 30+ 秒

## 完整 Python 封装示例

```python
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
from pathlib import Path
import requests


class DingTalkWebhook:
    def __init__(self, webhook_url: str, secret: str = "", keyword: str = ""):
        self.base_url = webhook_url
        self.secret = secret
        self.keyword = keyword

    def _signed_url(self) -> str:
        if not self.secret:
            return self.base_url
        ts = str(round(time.time() * 1000))
        s = f"{ts}\n{self.secret}"
        h = hmac.new(self.secret.encode(), s.encode(), hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(h))
        return f"{self.base_url}&timestamp={ts}&sign={sign}"

    def _prepend_keyword(self, payload: dict) -> dict:
        """关键词模式：消息正文里塞关键词

        ⚠️ Action Card 必须同时在 title 和 text 中都含关键词，
            否则 API 返回 errcode:310000 关键词不匹配
        """
        if not self.keyword:
            return payload
        mt = payload.get("msgtype")
        if mt == "text":
            payload["text"]["content"] = f"{self.keyword} {payload['text']['content']}"
        elif mt == "markdown":
            payload["markdown"]["text"] = f"**{self.keyword}**\n{payload['markdown']['text']}"
        elif mt == "actionCard":
            # ⚠️ 关键词必须同时在 title 和 text 中
            if self.keyword not in payload["actionCard"].get("title", ""):
                payload["actionCard"]["title"] = f"{self.keyword} · {payload['actionCard']['title']}"
            payload["actionCard"]["text"] = f"**{self.keyword}**\n{payload['actionCard']['text']}"
        return payload

    def send(self, payload: dict) -> dict:
        payload = self._prepend_keyword(payload)
        url = self._signed_url()
        # ⚠️ 用 json.dumps(ensure_ascii=False) + data 参数，不要用 json= 参数
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        r = requests.post(url, data=body,
                          headers={"Content-Type": "application/json; charset=utf-8"})
        return r.json()
```

## 常见错误码

| errcode | 含义 | 处理 |
|---|---|---|
| 0 | 成功 | — |
| 310000 | 关键词不匹配 | 检查消息正文是否含关键词 |
| 660026 | 频率过高 | sleep 30+ 秒重试 |
| 40001 | 时间戳过期（加签） | 重新生成 timestamp |
| 43004 | 加签错误 | 检查 secret 是否正确 |

## 调试清单

1. ✅ Webhook URL 完整（包括 access_token）
2. ✅ 消息正文含**关键词**（在群设置 → 安全设置查看）
3. ✅ 加签模式下，URL 含 `timestamp` 和 `sign` 参数
4. ✅ 消息类型字段名正确（msgtype / text / markdown / actionCard）
5. ✅ 中文字符用文件 payload 或 Python requests（不要 shell 内联）
6. ✅ 不在 IP 白名单时考虑切换机器人配置