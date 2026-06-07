import os
import re
import time
import random
import sys
import socket
import urllib.request
import json
import pandas as pd
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

# Force clear Python process proxy env vars to ensure local loopback CDP connection bypasses VPN/system proxy.
# This prevents Clash/VPN from hijacking the local loopback 127.0.0.1:9222 connection.
for env_var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    if env_var in os.environ:
        del os.environ[env_var]
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

# Get directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Smart adaptive path resolution (Prioritize current working directory)
if os.path.exists("asin_list.xlsx"):
    INPUT_FILE = os.path.abspath("asin_list.xlsx")
    OUTPUT_FILE = os.path.abspath("amazon_images_result.xlsx")
elif os.path.exists(os.path.join("data", "asin_list.xlsx")):
    INPUT_FILE = os.path.abspath(os.path.join("data", "asin_list.xlsx"))
    OUTPUT_FILE = os.path.abspath(os.path.join("data", "amazon_images_result.xlsx"))
elif os.path.exists(os.path.join(SCRIPT_DIR, "asin_list.xlsx")):
    INPUT_FILE = os.path.join(SCRIPT_DIR, "asin_list.xlsx")
    OUTPUT_FILE = os.path.join(SCRIPT_DIR, "amazon_images_result.xlsx")
elif os.path.exists(os.path.join(SCRIPT_DIR, "data", "asin_list.xlsx")):
    INPUT_FILE = os.path.join(SCRIPT_DIR, "data", "asin_list.xlsx")
    OUTPUT_FILE = os.path.join(SCRIPT_DIR, "data", "amazon_images_result.xlsx")
else:
    INPUT_FILE = os.path.abspath("asin_list.xlsx")
    OUTPUT_FILE = os.path.abspath("amazon_images_result.xlsx")

SITE_DOMAINS = {
    "US": "amazon.com",
    "UK": "amazon.co.uk",
    "DE": "amazon.de",
    "FR": "amazon.fr",
    "IT": "amazon.it",
    "ES": "amazon.es",
    "JP": "amazon.co.jp",
    "CA": "amazon.ca",
}

def initialize_directories_and_templates():
    parent_dir = os.path.dirname(INPUT_FILE)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
        print(f"[INFO] Created data directory: {parent_dir}")

    if not os.path.exists(INPUT_FILE):
        sample_data = {
            "Site": ["US", "US", "US"],
            "ASIN": ["B0CHWRXH8B", "B0CX254FDM", "B091G3FLL7"]
        }
        df = pd.DataFrame(sample_data)
        df.to_excel(INPUT_FILE, index=False)
        print(f"[INFO] Sample input file generated at: {INPUT_FILE}")
        print("[INFO] Please edit it with your own Site and ASIN list.")

def check_port_active(host="127.0.0.1", port=9222):
    """
    Check if a local TCP port is active and accepting connections.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def get_chrome_ws_url(host="127.0.0.1", port=9222):
    """
    Fetch webSocketDebuggerUrl from Chrome debug endpoint and ensure it uses 127.0.0.1
    to completely bypass Playwright's IPv6 DNS resolution issues.
    """
    url = f"http://{host}:{port}/json/version"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
            ws_url = data.get("webSocketDebuggerUrl")
            if ws_url:
                # Force IPv4 127.0.0.1 instead of localhost or standard domain names
                ws_url = ws_url.replace("ws://localhost", "ws://127.0.0.1")
                return ws_url
    except Exception as e:
        print(f"[DEBUG] Failed to fetch debugger version info: {str(e)}")
    return None

def clean_amazon_image_url(url):
    """
    Clean Amazon image URL - strip resize suffixes to get original HD image.
    Example: .../I/21fBDZCm5QL._AC_SR38.jpg -> .../I/21fBDZCm5QL.jpg
    """
    if not url:
        return ""
    match = re.search(r'(https://.*?/images/[IG]/)([^/]+)', url)
    if not match:
        return url
    prefix = match.group(1)
    filename = match.group(2)
    dot_idx = filename.find('.')
    ext_idx = filename.rfind('.')
    if dot_idx != -1 and ext_idx != -1 and dot_idx != ext_idx:
        base = filename[:dot_idx]
        ext = filename[ext_idx:]
        return prefix + base + ext
    return url

def check_captcha_and_wait(page, timeout_seconds=300):
    """Human-in-the-loop CAPTCHA detection and wait"""
    title = page.title()
    url = page.url
    is_captcha = (
        "Robot Check" in title or
        "validateCaptcha" in url or
        page.locator("input#captchacharacters").is_visible() or
        "api-services-support@amazon.com" in page.content() or
        "Enter the characters you see below" in page.content()
    )
    if is_captcha:
        print("\n" + "="*70)
        print("[WARNING] CAPTCHA detected!")
        print("Please resolve the CAPTCHA in the browser window.")
        print("Script will resume automatically after you pass the check.")
        print("="*70 + "\n")
        for _ in range(3):
            sys.stdout.write('\a')
            sys.stdout.flush()
            time.sleep(0.5)

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                if page.locator("#productTitle").is_visible():
                    print("[SUCCESS] CAPTCHA Solved! Resuming...")
                    return True
                current_title = page.title()
                current_url = page.url
                is_still_captcha = (
                    "Robot Check" in current_title or
                    "validateCaptcha" in current_url or
                    page.locator("input#captchacharacters").is_visible() or
                    "Enter the characters you see below" in page.content()
                )
                if not is_still_captcha:
                    # Give a small 2-second buffer for page transition/redirection
                    time.sleep(2.0)
                    current_title = page.title()
                    current_url = page.url
                    is_still_captcha_double = (
                        "Robot Check" in current_title or
                        "validateCaptcha" in current_url or
                        page.locator("input#captchacharacters").is_visible() or
                        "Enter the characters you see below" in page.content()
                    )
                    if not is_still_captcha_double:
                        if page.locator("#dogImage").is_visible() or "Page Not Found" in current_title:
                            print("[INFO] CAPTCHA solved but product unavailable (dog page).")
                        else:
                            print("[SUCCESS] CAPTCHA solved/bypassed (Not in CAPTCHA page). Resuming...")
                        return True
            except Exception:
                pass
            time.sleep(1.0)
        print("[ERROR] CAPTCHA waiting timeout. Skipping this ASIN.")
        return False
    return True

def parse_images_from_html(html):
    """Extract colorImages block via brace-matching, then regex parse image URLs"""
    try:
        pos = html.find("'colorImages'")
        if pos == -1:
            pos = html.find('"colorImages"')
        color_images_block = ""
        if pos != -1:
            start_idx = html.find('{', pos)
            if start_idx != -1:
                brace_count = 0
                for i in range(start_idx, len(html)):
                    char = html[i]
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            color_images_block = html[start_idx:i+1]
                            break
        urls = []
        if color_images_block:
            raw_urls = re.findall(
                r'https://[a-zA-Z0-9.-]*media-amazon\.com/images/[IG]/[a-zA-Z0-9%_.,-]+',
                color_images_block
            )
            for url in raw_urls:
                clean_url = clean_amazon_image_url(url)
                if clean_url.endswith('.'):
                    clean_url = clean_url[:-1]
                if not re.search(r'\.(jpg|jpeg|png|gif)$', clean_url, re.I):
                    match_ext = re.search(r'\.(jpg|jpeg|png|gif)', url, re.I)
                    if match_ext:
                        clean_url += match_ext.group(0)
                    else:
                        clean_url += ".jpg"
                if "play-button-overlay" not in clean_url and clean_url not in urls:
                    urls.append(clean_url)
        return urls
    except Exception as e:
        print(f"[DEBUG] HTML parsing failed: {str(e)}")
        return []

def main():
    print("==================================================")
    print("  Amazon Image Extractor")
    print("==================================================")

    initialize_directories_and_templates()

    try:
        df_input = pd.read_excel(INPUT_FILE)
    except Exception as e:
        print(f"[FATAL] Failed to read {INPUT_FILE}: {str(e)}")
        input("Press Enter to exit...")
        sys.exit(1)

    if df_input.empty or "ASIN" not in df_input.columns or "Site" not in df_input.columns:
        print(f"[ERROR] Input file {INPUT_FILE} must contain 'Site' and 'ASIN' columns.")
        input("Press Enter to exit...")
        sys.exit(1)

    print(f"[INFO] Loaded {len(df_input)} ASIN tasks.")
    
    # Try to load existing processed ASINs to support Append & Deduplicate mode
    processed_asins = set()
    existing_df = None
    if os.path.exists(OUTPUT_FILE):
        try:
            existing_df = pd.read_excel(OUTPUT_FILE)
            if not existing_df.empty and "ASIN" in existing_df.columns and "Status" in existing_df.columns:
                for _, row in existing_df.iterrows():
                    site = str(row.get("Site", "")).strip().upper()
                    asin = str(row.get("ASIN", "")).strip()
                    status = str(row.get("Status", "")).strip()
                    # Only skip if status contains 'success'
                    if "success" in status.lower():
                        processed_asins.add((site, asin))
                print(f"[INFO] Found {len(processed_asins)} already processed ASIN(s) in existing result sheet.")
        except Exception as e:
            print(f"[WARN] Failed to read existing results for deduplication: {str(e)}")
            
    results = []

    # ================================================================
    # CDP Mode: Connect to local Chrome debug port 9222
    # run.bat will launch Chrome with --remote-debugging-port=9222
    # before running this script.
    # ================================================================
    with sync_playwright() as p:
        print("[INFO] Checking local Chrome debug port 9222...")
        use_cdp = False
        browser = None
        context = None
        page = None

        if check_port_active("127.0.0.1", 9222):
            print("[INFO] Port 9222 is open. Fetching WebSocket Debugger URL...")
            ws_url = get_chrome_ws_url("127.0.0.1", 9222)
            if ws_url:
                print(f"[INFO] Connecting to CDP: {ws_url}")
                try:
                    browser = p.chromium.connect_over_cdp(ws_url)
                    use_cdp = True
                except Exception as e:
                    print(f"[WARN] Connect over CDP failed: {str(e)}")
            else:
                print("[WARN] Port is open but failed to retrieve WebSocket URL.")
        else:
            print("[WARN] Port 9222 is closed. Chrome debug mode is not running on 9222.")

        if use_cdp:
            try:
                if len(browser.contexts) > 0:
                    context = browser.contexts[0]
                else:
                    context = browser.new_context()
                page = context.new_page()
                print("[SUCCESS] Connected to local Chrome via CDP!")
            except Exception as e:
                print(f"[WARN] Failed to initialize page on CDP: {str(e)}")
                use_cdp = False

        if not use_cdp:
            print("\n" + "="*70)
            print("[WARNING] 调试端口 (CDP) 连接失败，已触发【排查与自愈引导 SOP】：")
            print("1. 请确认您是否双击运行了 run.bat 并让它拉起了 Chrome？")
            print("2. 若您运行了 run.bat 选择【模式一】（接管日常 Chrome）而报错：")
            print("   - 请先手动【关闭所有已打开的 Chrome 窗口】（确保任务管理器中无 chrome.exe 残留）。")
            print("   - 重新双击 run.bat 并输入 1 启动。")
            print("3. 若您想保持日常 Chrome 打开，无需强杀：")
            print("   - 请重新运行 run.bat 并输入【2】选择【免冲突独立调试模式】。")
            print("4. 若您开启了 VPN 的全局或 TUN 模式：")
            print("   - 请临时关闭 VPN，或在代理软件的 Bypass/排除列表中加入 127.0.0.1 绕过本地连接。")
            print("="*70)
            print("\n[INFO] 正在尝试降级启动独立的 Standalone 浏览器（无日常 Cookies，可能需要处理验证码）...")
            try:
                browser = p.chromium.launch(
                    headless=False,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized",
                    ]
                )
                context = browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="en-US",
                )
                page = context.new_page()
                stealth_cfg = Stealth()
                stealth_cfg.apply_stealth_sync(page)
                print("[SUCCESS] Standalone Chromium 浏览器启动成功！")
            except Exception as launch_err:
                print(f"[FATAL] 无法拉起任何浏览器: {str(launch_err)}")
                input("请按回车键退出...")
                sys.exit(1)

        # Iterate ASIN tasks
        for index, row in df_input.iterrows():
            site = str(row["Site"]).strip().upper()
            asin = str(row["ASIN"]).strip()
            
            # Smart deduplication: skip successfully processed ASINs
            if (site, asin) in processed_asins:
                print(f"\n[{index+1}/{len(df_input)}] Skipping: Site={site}, ASIN={asin} (Already successfully parsed)")
                continue
                
            print(f"\n[{index+1}/{len(df_input)}] Processing: Site={site}, ASIN={asin}...")
            domain = SITE_DOMAINS.get(site, "amazon.com")
            url = f"https://www.{domain}/dp/{asin}"
            res_dict = {
                "Site": site, "ASIN": asin, "Status": "Success",
                "Image 1": "", "Image 2": "", "Image 3": "", "Image 4": "",
                "Image 5": "", "Image 6": "", "Image 7": "", "Image 8": "",
            }

            # Retry loop for network jitter
            success = False
            for retry in range(3):
                try:
                    delay = random.uniform(2.0, 5.0)
                    print(f"  Cooldown {delay:.2f}s...")
                    time.sleep(delay)
                    page.goto(url, timeout=30000)
                    success = True
                    break
                except Exception as e:
                    print(f"  [RETRY] Failed [{retry+1}/3]: {str(e)}")

            if not success:
                print(f"  [FAIL] Failed to load page: {url}")
                res_dict["Status"] = "Page Load Timeout"
                results.append(res_dict)
                continue

            # CAPTCHA check
            if not check_captcha_and_wait(page):
                res_dict["Status"] = "CAPTCHA Timeout"
                results.append(res_dict)
                continue

            # Dog page check
            if page.locator("#dogImage").is_visible() or "Page Not Found" in page.title():
                print(f"  [DOG] Product unavailable / Dog page")
                res_dict["Status"] = "Dog / Unavailable"
                results.append(res_dict)
                continue

            # Wait for product title
            try:
                page.wait_for_selector("#productTitle", timeout=10000)
            except Exception:
                pass

            html_content = page.content()
            images = parse_images_from_html(html_content)

            # Fallback: altImages DOM extraction
            if not images:
                print("  [INFO] colorImages not found, falling back to altImages DOM...")
                try:
                    dom_imgs = page.locator("#altImages img").all()
                    for img in dom_imgs:
                        src = img.get_attribute("src")
                        if src:
                            clean_src = clean_amazon_image_url(src)
                            if "play-button-overlay" not in clean_src and clean_src not in images:
                                images.append(clean_src)
                except Exception:
                    pass

            if images:
                print(f"  [SUCCESS] Extracted {len(images)} image(s).")
                for idx, img_url in enumerate(images[:8]):
                    res_dict[f"Image {idx+1}"] = img_url
            else:
                print("  [FAIL] No images extracted.")
                res_dict["Status"] = "No Images Found"

            results.append(res_dict)

        browser.close()
        print("\n[INFO] Browser closed.")

    # Save results to Excel with Append & Merge logic
    df_new = pd.DataFrame(results)
    columns_order = [
        "Site", "ASIN", "Status",
        "Image 1", "Image 2", "Image 3", "Image 4",
        "Image 5", "Image 6", "Image 7", "Image 8",
    ]
    
    if not df_new.empty:
        df_new = df_new[columns_order]
        # Merge with existing file if it exists and is valid
        if existing_df is not None and not existing_df.empty:
            try:
                # Align columns of existing_df to match our order
                for col in columns_order:
                    if col not in existing_df.columns:
                        existing_df[col] = ""
                existing_df = existing_df[columns_order]
                
                # Combine both
                df_combined = pd.concat([existing_df, df_new], ignore_index=True)
                # Deduplicate by Site & ASIN, keep the latest run
                df_combined.drop_duplicates(subset=["Site", "ASIN"], keep="last", inplace=True)
                df_output = df_combined
                print(f"[INFO] Merged {len(df_new)} new result(s) with existing {len(existing_df)} rows.")
            except Exception as merge_err:
                print(f"[WARN] Merge failed, falling back to new results only. Error: {str(merge_err)}")
                df_output = df_new
        else:
            df_output = df_new
    else:
        # If no new results were captured (all skipped), just keep the existing data
        if existing_df is not None:
            df_output = existing_df
        else:
            df_output = pd.DataFrame(columns=columns_order)

    try:
        df_output.to_excel(OUTPUT_FILE, index=False)
        print(f"\n==================================================")
        print(f"[FINISH] All tasks completed!")
        print(f"[OUTPUT] Results saved to: {OUTPUT_FILE}")
        print(f"==================================================")
        
        # Pop up standard Windows alert dialog to remind the user
        try:
            import ctypes
            msg_text = f"恭喜！所有亚马逊商品主图链接抓取完毕。\n\n结果已保存至：\n{OUTPUT_FILE}"
            ctypes.windll.user32.MessageBoxW(0, msg_text, "任务完成 (Task Finished)", 64) # 64 is MB_OK | MB_ICONINFORMATION
        except Exception:
            pass
            
    except Exception as e:
        print(f"\n[ERROR] Failed to save Excel: {str(e)}")
        csv_file = OUTPUT_FILE.replace(".xlsx", ".csv")
        try:
            df_output.to_csv(csv_file, index=False, encoding="utf-8-sig")
            print(f"[WARN] Fallback CSV saved: {csv_file}")
            
            # Pop up fallback warning alert dialog
            try:
                import ctypes
                msg_text = f"抓取完毕，但 Excel 写入失败。\n已降级保存为 CSV 文件：\n{csv_file}"
                ctypes.windll.user32.MessageBoxW(0, msg_text, "任务完成但有警告 (Finished with Warnings)", 48) # 48 is MB_ICONWARNING
            except Exception:
                pass
                
        except Exception as csv_err:
            print(f"[FATAL] Failed to save CSV fallback: {str(csv_err)}")

if __name__ == "__main__":
    main()
