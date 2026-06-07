# 亚马逊图片链接批量提取工具交付文档 (Amazon Image Link Extractor Walkthrough)

本工具已开发完毕并经过本地真实数据测试，能够完美支持 **CDP 模式（接管日常浏览器）** 与 **独立调试模式**。工具具有强大的自愈和诊断能力，能够自动绕过 Windows 系统下的 IPv6 `ECONNREFUSED` 报错，并提供极高的稳定性。

此外，工具已升级支持**增量抓取与智能追加去重模式 (Incremental & Append Mode)**，能极大保护运营历史数据并节约运行时间。

---

## 1. 核心改进与自愈细节 (Key Implementations & Self-Healing)

1. **增量抓取与智能追加 (Incremental Scraping & Auto-Append)**：
   - 启动时会自动读取现有的结果文件 `data/amazon_images_result.xlsx`。
   - 提取其中所有状态为 `Success`（成功）的 ASIN 任务并自动在主循环中**跳过 (Skip)**，防止重复向亚马逊发送请求，保护账号并大幅缩短提取时间。
   - 提取结束后，将本次新抓取的结果与历史旧结果自动进行**合并 (Merge)**，并在 `[Site, ASIN]` 维度下进行**去重 (Deduplicate)**，且以最新的抓取状态为准，彻底保证以往的数据不被覆写或丢失。
2. **绕过 IPv6 & 纯 IP 握手 (IPv6 Bypass via Pure IP Handshake)**：
   - 脚本不再通过容易引起域名解析混乱的 `http://localhost:9222` 连接 Playwright。
   - 升级为：先通过 Python 原生 HTTP 请求读取 `http://127.0.0.1:9222/json/version`，解析出调试专用的 WebSocket 链接（`webSocketDebuggerUrl`）。
   - 将链接中的 `localhost` 强制替换为纯 IP `127.0.0.1`，直接使用此 WebSocket 链接（例如 `ws://127.0.0.1:9222/devtools/browser/...`）进行连接。这彻底杜绝了 Playwright 底层由于 IPv6 解析偏好触发 of `ECONNREFUSED ::1:9222` 连接问题。
3. **精准验证码识别与自愈跳转 (Precise CAPTCHA & Auto-Redirection Check)**：
   - 将验证码页面的元素特征由容易误判正常页面顶部搜索栏的 `field-keywords` 升级为专用的 **`input#captchacharacters`** 以及验证码页面文字特征。
   - 挂起等待时，不再死等商品详情页标题，只要检测到浏览器**已经脱离了验证码/登录校验页面**（哪怕跳转到了亚马逊首页或登录成功页），就会自动解密挂起并进入主循环，由主循环重新自动加载目标 ASIN 详情页，实现真正的免死锁无人值守。
4. **免冲突独立调试模式 (Conflict-free Isolated Debug Profile)**：
   - 在 `run.bat` 中提供了两种 Chrome 启动模式选项，完美解决“日常 Chrome 占用端口”的痛点：
     * **[1] 模式一：接管日常 Chrome**（强杀残留进程，复用日常历史 Cookies，亚马逊验证码出现率极低）。
     * **[2] 模式二：免冲突独立调试模式**（无需关闭您平常正在使用的 Chrome 窗口，使用隔离的 Profile 目录拉起一个新的调试浏览器，相互之间没有任何冲突。仅需在首次运行时登录一次亚马逊）。

---

## 2. 验证与测试结果 (Verification Results)

我们已在您的本地环境中成功模拟并运行了自愈和抓取流程：
* **端口未开启状态**：系统成功拦截并打印出完整的排查 SOP，随后顺畅降级至 Standalone 独立模式。
* **增量功能验证**：重复运行脚本时，已成功的 ASIN 会被秒级自动跳过，新加入的 ASIN 被精准提取并成功合并追加进 Excel。

---

## 3. 使用说明 (User Guide)

最新优化的脚本与批处理文件已同步更新至您的**桌面文件夹 `Amazon Image Extractor`**。您只需按照以下步骤运行：

### 第一步：准备输入 ASIN 列表
1. 打开桌面的 `Amazon Image Extractor` 目录。
2. 编辑 `data/asin_list.xlsx` 文件：
   * `Site` 列：填入国家站点代码（如 `US`, `DE`, `JP`, `UK`, `FR` 等）。
   * `ASIN` 列：填入您需要提取图片的商品编码。
3. 保存并关闭文件。*(您可以直接在原有基础上追加新 ASIN，不需要清空之前已抓取的内容)*。

### 第二步：运行与选择模式
1. 双击运行桌面目录下的 **`run.bat`**。
2. 此时控制台将弹出模式选择菜单：
   * **输入 1 (回车默认)**：如果您当前可以关闭全部 Chrome 浏览器。脚本会强杀后台进程并接管您的日常 Chrome（推荐，因为带日常 Cookies 体验最好）。
   * **输入 2**：如果您当前有日常网页正开着，不想关闭浏览器。脚本会为您多开一个干净的、互不影响的独立调试 Chrome。
3. 随后，批处理脚本将自动拉起调试 Chrome，并在 4 秒后由 Python 接管，开始自动化提取。

### 第三步：人机协作与导出
1. 观察弹出的 Chrome 窗口：
   * **若直接正常跳转**：程序会依次提取所有图片的超清无损大图，并去重。
   * **若弹出亚马逊验证码**：程序将发出蜂鸣警报，此时请手动滑过验证码，或在浏览器中登录您的亚马逊账号。检测到页面跳转后，程序会自动恢复向下运行。
2. 运行完毕后，浏览器自动关闭，您可以在桌面目录下的 **`data/amazon_images_result.xlsx`** 中获取到排版整洁且合并去重完毕的图片链接结果！
