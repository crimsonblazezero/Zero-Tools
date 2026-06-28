import os
import requests
import json

# ==============================================================================
# Agnes AI API 接入与测试脚本
# Agnes AI API Integration & Test Script
# ==============================================================================

# 配置信息 / Configurations
# 官方 Base URL 兼容 OpenAI 格式 / Official Base URL compatible with OpenAI format
BASE_URL = "https://apihub.agnes-ai.com/v1"

# 获取 API Key / Get API Key
# 优先从环境变量获取，如无则使用用户填写的 Key
# Prioritize environment variable, fallback to user-provided key
API_KEY = os.getenv("AGNES_API_KEY", "YOUR_AGNES_API_KEY_HERE")

def test_chat_completion(prompt="Hello, who are you?"):
    """
    测试文本生成模型 (agnes-2.0-flash)
    Test Text Generation Model (agnes-2.0-flash)
    """
    if API_KEY == "YOUR_AGNES_API_KEY_HERE" or not API_KEY:
        print("[警告] 请先在脚本中配置 API_KEY，或设置环境变量 AGNES_API_KEY。")
        print("[WARNING] Please configure API_KEY in the script or set AGNES_API_KEY environment variable.")
        return

    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "agnes-2.0-flash",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    print(f"\n[正在请求文本模型] model: agnes-2.0-flash | Prompt: '{prompt}'")
    print(f"[Requesting Text Model] model: agnes-2.0-flash...")
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print("\n[模型回复内容 / Model Response]:")
            print("-" * 50)
            print(content)
            print("-" * 50)
        else:
            print(f"\n[请求失败 / Request Failed] Status Code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"\n[发生异常 / Exception Occurred]: {str(e)}")

def test_list_models():
    """
    获取支持的模型列表
    Get Supported Models List
    """
    if API_KEY == "YOUR_AGNES_API_KEY_HERE" or not API_KEY:
        return

    url = f"{BASE_URL}/models"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    print(f"\n[正在获取模型列表 / Retrieving Models List]...")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            models = response.json()
            print(json.dumps(models, indent=2, ensure_ascii=False))
        else:
            print(f"[获取失败 / Failed] Status Code: {response.status_code}")
    except Exception as e:
        print(f"[发生异常 / Exception]: {str(e)}")

if __name__ == "__main__":
    # 执行测试 / Execute Tests
    # 如果已配置 Key，可直接运行此脚本进行测试 / Run this script directly if API Key is configured
    print("Agnes AI API Integration Test")
    print("=" * 40)
    print(f"Base URL: {BASE_URL}")
    print(f"Current API Key: {API_KEY[:8]}... (length: {len(API_KEY)})" if API_KEY != "YOUR_AGNES_API_KEY_HERE" else "Current API Key: Not Configured")
    
    # 示例调用
    # test_chat_completion("你好！请简短介绍一下你自己。")
    # test_list_models()
