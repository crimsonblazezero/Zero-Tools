import urllib.request
import json
import sys

# 提示：在此处配置您内网穿透后的公网代理地址 (e.g. https://xxx.antigravity-proxy.com)
# 如果是本地浏览器同机测试，保持 http://127.0.0.1:8000 即可
CALLBACK_BASE_URL = "http://127.0.0.1:8000"

webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=ba74877458660cee8526c367981821c5493aa0ae0493d205574bc82e8fe620d7"

def send_action_card():
    # 拼接回调地址 (Constructing callback URL)
    target_url = f"{CALLBACK_BASE_URL}/amz/execute?action=wpc_optimize"
    
    # 动作卡片 payload (DingTalk ActionCard Payload)
    payload = {
        "msgtype": "actionCard",
        "actionCard": {
            "title": "WPC 广告预算调整确认",
            "text": """### 📢 欧洲组：英国站 (UK) WPC 广告优化确认卡片

AI 决策大脑建议对以下广告活动的每日预算进行**折半调整**，请点击下方确认按钮直接对接到亚马逊后台生效：

| 📌 广告活动名称 (Campaign Name) | 🆔 广告ID (Campaign ID) | 📊 预算变化 (Budget Change) |
| :--- | :--- | :--- |
| **WPC组合相框-定位** | `227474470153968` | 12.5 ➡ **6.25 GBP** |
| **WPC组合相框-自动-宽泛** | `190640779579159` | 10.0 ➡ **5.0 GBP** |
| **WPC组合相框-自动-宽泛-Q73O** | `217584089353137` | 10.0 ➡ **5.0 GBP** |

---
*安全须知：点击“确认执行”后，系统将自动调用官方 Ads API 进行修改。*""",
            "btnOrientation": "0", 
            "singleTitle": "✔️ 确认执行调整 (Confirm & Execute)",
            "singleURL": target_url
        }
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            response = json.loads(res.read().decode("utf-8"))
            print(f"[SUCCESS] ActionCard 发送成功！ 钉钉返回: {response}")
    except Exception as e:
        print(f"[ERROR] 发送失败: {e}")

if __name__ == "__main__":
    send_action_card()
