# 亚马逊图片链接批量提取工具标准作业程序 (SOP - Standard Operating Procedure)

本工具用于从亚马逊各站点商品详情页批量提取高清主图 1-8 的链接并导出为 Excel 表格。本程序利用 **Playwright 模拟真实浏览器 (Browser Emulation)** 避开防爬限制，并支持 **人机协同过验证码** 机制。

---

## 1. 运行环境配置 (Environment Setup)

如果您将此工具发送给没有配置过运行环境的同事，请先让其执行以下步骤配置依赖：

### 第一步：安装 Python
确保电脑已安装 Python 3.8 或以上版本。可以在命令行中输入以下命令进行验证：
```bash
python --version
```

### 第二步：安装相关 Python 依赖库 (Install Dependencies)
在主程序同级目录下打开命令行（如 CMD、PowerShell 或终端），运行以下命令一键安装所需的第三方依赖库：
```bash
pip install pandas openpyxl playwright playwright-stealth
```
*(如果随附发送了 `requirements.txt` 文件，亦可运行 `pip install -r requirements.txt`)*

### 第三步：安装浏览器内核 (Install Browser Kernel)
依赖库安装成功后，**必须**运行以下命令，下载 Playwright 运行时所需的专属 Chromium 浏览器内核：
```bash
playwright install chromium
```

---

## 2. 批量抓取图片具体操作步骤 (Execution Steps)

```text
【准备数据】             【运行脚本】               【人机过验证】             【获取结果】
编辑 Excel 输入  ===>  在终端运行 Python  ===>  如遇验证码手动滑过  ===>  打开 Excel 提取链接
```

### 第一步：准备输入 ASIN 数据
1.  双击打开输入文件 `asin_list.xlsx`。
    *   *注：如果是首次运行程序，同级目录下没有此文件，可直接运行第二步，脚本会自动生成一个带样例数据的 `asin_list.xlsx` 模板。*
2.  在表格中配置您要抓取的 ASIN 列表：
    *   **Site 列**：站点代码。支持 `US` (美国)、`DE` (德国)、`JP` (日本)、`UK` (英国)、`FR` (法国)、`IT` (意大利)、`ES` (西班牙)、`CA` (加拿大)。
    *   **ASIN 列**：商品的 10 位 ASIN 编码。
3.  保存并关闭 Excel 文件。

### 第二步：运行提取脚本
在脚本所在路径下打开终端，执行以下命令启动程序：
```bash
python amazon_image_extractor.py
```
*(注：如果保留了原有的分级目录，也可以在项目根目录运行 `python src/amazon_image_extractor.py`)*

此时，桌面上会弹出一个 Chromium 浏览器窗口，显示亚马逊详情页的自动跳转过程。**请勿手动关闭此弹窗。**

### 第三步：人机协同过验证 (Captcha Solving)
1.  **自动检测**：当遇到亚马逊验证码时，命令行窗口会输出高亮的 `[WARNING] 检测到亚马逊安全验证码！` 警报并自动暂停。
2.  **手动输入**：请立刻在**弹出的浏览器窗口中**，手动滑过滑动验证码或输入字符验证码。
3.  **自愈恢复**：验证通过并成功加载详情页的一瞬间，程序会自动检测到跳转，并在控制台输出 `[SUCCESS] 验证码通过` 随后**自动恢复向下运行**。

### 第四步：检查输出结果
1.  所有 ASIN 处理完毕后，浏览器会自动关闭，控制台提示 `[FINISH] 任务全部完成！`。
2.  打开生成的 `amazon_images_result.xlsx` 结果表即可提取主图 1-8 的**无损高清大图链接**。

---

## 3. 常见异常处理 (Troubleshooting)

| 异常现象 (Issues) | 根本原因 (Causes) | 解决方案 (Solutions) |
| :--- | :--- | :--- |
| 运行提示 `ModuleNotFoundError` | 尚未安装某 Python 第三方包 | 重新执行第一节的 `pip install` 安装对应依赖。 |
| 运行提示 `Playwright initialization error` | 未安装 Playwright 专用浏览器内核 | 在终端执行 `playwright install chromium`。 |
| 所有 ASIN 全部显示 `Dog / Unavailable` | 本地 IP 被亚马逊封锁或验证码未能成功通过 | 重新运行并确保在遇到验证码时能及时在弹窗中滑过；大批量提取建议分批次运行。 |
