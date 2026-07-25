import os
import urllib.request
import urllib.parse
import json
from flask import Flask, request, render_template_string

app = Flask(__name__)

# 手动解析 .env 文件 (Manually parse .env file)
def load_env(env_path):
    config = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    val = val.strip().strip('"').strip("'")
                    config[key.strip()] = val
    return config

def get_access_token(client_id, client_secret, refresh_token):
    url = "https://api.amazon.com/auth/o2/token"
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req) as res:
        res_data = json.loads(res.read().decode("utf-8"))
        return res_data["access_token"]

def update_sp_campaigns_v3(access_token, client_id, profile_id, campaigns_list):
    url = "https://advertising-api-eu.amazon.com/sp/campaigns"
    payload = json.dumps({
        "campaigns": campaigns_list
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": client_id,
        "Amazon-Advertising-API-Scope": str(profile_id),
        "Content-Type": "application/vnd.spCampaign.v3+json",
        "Accept": "application/vnd.spCampaign.v3+json"
    }, method="PUT")
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))

# HTML 模板风格 (Premium Responsive HTML Template)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KovaScape 广告调优执行结果</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #f4f7f6;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .card {
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
            width: 90%;
            max-width: 500px;
            padding: 30px;
            text-align: center;
            border-top: 6px solid #064338; /* KovaScape Emerald Green */
        }
        .icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        .success-icon { color: #2ecc71; }
        .error-icon { color: #e74c3c; }
        h2 {
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 10px;
        }
        p {
            color: #7f8c8d;
            font-size: 15px;
            line-height: 1.5;
            margin-bottom: 25px;
        }
        .details-box {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            text-align: left;
            font-family: monospace;
            font-size: 13px;
            color: #34495e;
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #eaedf1;
        }
        .footer {
            margin-top: 25px;
            font-size: 12px;
            color: #bdc3c7;
        }
    </style>
</head>
<body>
    <div class="card">
        {% if success %}
            <div class="icon success-icon">✓</div>
            <h2>执行成功 / Executed Successfully</h2>
            <p>已通过 Amazon Ads API 成功将 WPC 相框广告活动的预算削减一半！</p>
        {% else %}
            <div class="icon error-icon">✗</div>
            <h2>执行失败 / Execution Failed</h2>
            <p>广告预算调整未能成功写入，请检查系统日志。</p>
        {% endif %}
        
        <div class="details-box">
            <strong>接口返回详情 (API Response):</strong><br>
            <pre>{{ response_details }}</pre>
        </div>
        
        <div class="footer">
            KovaScape Brand Automation Center &copy; 2026
        </div>
    </div>
</body>
</html>
"""

@app.route("/amz/execute", methods=["GET"])
def execute_ad_adjustment():
    action = request.args.get("action")
    if action != "wpc_optimize":
        return render_template_string(HTML_TEMPLATE, success=False, response_details="Invalid Action Code")
        
    env_file = "d:/Zero Tools/amazon_ads.env"
    config = load_env(env_file)
    client_id = config.get("AMAZON_ADS_CLIENT_ID")
    client_secret = config.get("AMAZON_ADS_CLIENT_SECRET")
    refresh_token = config.get("AMAZON_ADS_REFRESH_TOKEN")
    profile_id = 562422498717821
    
    # 严格对齐 ID 的修改列表 (Strictly mapped actions by ID)
    update_payload = [
        {
            "campaignId": "227474470153968",  # WPC组合相框-定位
            "budget": {
                "budgetType": "DAILY",
                "budget": 6.25
            }
        },
        {
            "campaignId": "190640779579159",  # WPC组合相框-自动-宽泛
            "budget": {
                "budgetType": "DAILY",
                "budget": 5.0
            }
        },
        {
            "campaignId": "217584089353137",  # WPC组合相框-自动-宽泛-Q73O
            "budget": {
                "budgetType": "DAILY",
                "budget": 5.0
            }
        }
    ]
    
    try:
        access_token = get_access_token(client_id, client_secret, refresh_token)
        api_res = update_sp_campaigns_v3(access_token, client_id, profile_id, update_payload)
        
        # 检查是否成功
        success = len(api_res.get("campaigns", {}).get("error", [])) == 0
        details = json.dumps(api_res, indent=2, ensure_ascii=False)
        return render_template_string(HTML_TEMPLATE, success=success, response_details=details)
        
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, success=False, response_details=f"System Error: {e}")

if __name__ == "__main__":
    # 本地监听 8000 端口
    # Local listener on port 8000
    app.run(host="127.0.0.1", port=8000, debug=True)
