import os
import urllib.request
import urllib.parse
import json

def load_env(env_path):
    """手动解析 .env 文件避免依赖第三方库 (Manually parse .env file to avoid external dependency)"""
    config = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    # 去除引号 (Strip quotes)
                    val = val.strip().strip('"').strip("'")
                    config[key.strip()] = val
    return config

def verify_amazon_ads_connection():
    env_file = "d:/Zero Tools/amazon_ads.env"
    print(f"[INFO] 正在从 {env_file} 加载 API 证书进行鉴权验证...")
    
    config = load_env(env_file)
    client_id = config.get("AMAZON_ADS_CLIENT_ID")
    client_secret = config.get("AMAZON_ADS_CLIENT_SECRET")
    refresh_token = config.get("AMAZON_ADS_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        print("[ERROR] 错误：配置文件中缺少必要的凭证。请检查 AMAZON_ADS_CLIENT_ID、AMAZON_ADS_CLIENT_SECRET 和 AMAZON_ADS_REFRESH_TOKEN 是否配置完整。")
        return False
        
    # 第一步：刷新 Access Token (Step 1: Refresh Access Token)
    print("[INFO] 步骤 1/2: 正在请求 LWA 获取临时 Access Token...")
    token_url = "https://api.amazon.com/auth/o2/token"
    token_data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }).encode("utf-8")
    
    req = urllib.request.Request(token_url, data=token_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            access_token = res_data.get("access_token")
            print("[SUCCESS] Access Token 获取成功！")
    except Exception as e:
        print(f"[ERROR] 步骤 1 失败：获取 Access Token 出错。")
        print(f"    具体错误: {e}")
        return False

    # 第二步：调用 /v2/profiles 跑通鉴权 (Step 2: Call /v2/profiles for Heartbeat Check)
    print("\n[INFO] 步骤 2/2: 发起 /v2/profiles 连通性“心跳”测试...")
    
    # 我们以欧洲大区 (EU) 作为测试目标 (Targeting EU endpoint as test target)
    eu_profiles_url = "https://advertising-api-eu.amazon.com/v2/profiles"
    
    profile_req = urllib.request.Request(eu_profiles_url, headers={
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": client_id,
        "Content-Type": "application/json"
    })
    
    try:
        with urllib.request.urlopen(profile_req) as res:
            profiles = json.loads(res.read().decode("utf-8"))
            print("[SUCCESS] “心跳”验证成功！接口返回正常。")
            print(f"[DATA] 欧洲大区 (EU) 共检测到 {len(profiles)} 个活跃站点：")
            for p in profiles:
                print(f"    - 国家: {p.get('countryCode')} | Profile ID: {p.get('profileId')} | 币种: {p.get('currencyCode')} | 时区: {p.get('timezone')}")
            print("\n[OK] 结论：您配置的 amazon_ads.env 凭证全局有效，连接鉴权完全正常！")
            return True
    except Exception as e:
        print("[ERROR] 步骤 2 失败：“心跳”连通性测试未通过。")
        print(f"    具体错误: {e}")
        return False

if __name__ == "__main__":
    verify_amazon_ads_connection()
