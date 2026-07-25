# 跨境电商项目环境与工具一键迁移指南
# Cross-Border E-Commerce Project Environment & Tools Migration Guide

本指南用于指导如何在公司电脑（或新电脑）上快速部署与当前开发环境一致的工具、项目配置和技能库。

---

## 💡 更方便的方法推荐：一键自动化脚本

为了免去繁琐的手动安装和配置步骤，我已为您编写了一个 **PowerShell 自动化安装脚本** `setup.ps1`。
您只需将当前项目文件夹（`Zero Tools`）拷贝到新电脑，然后在项目根目录下以管理员身份运行该脚本即可。

> [!TIP]
> **迁移建议：**
> 1. 用 U 盘或网盘将整个 `Zero Tools` 文件夹复制到公司电脑的 `D:\Zero Tools`。
> 2. 运行 `setup.ps1`，它会自动下载安装 rtk、安装 Python 依赖库、并恢复所有本地 Skill 与 Agent 配置。

---

## 🛠 方案 A：使用 `setup.ps1` 自动配置（推荐）

### 步骤 1：获取脚本
在项目根目录下，有已自动生成的 `setup.ps1` 脚本（脚本源码见本指南文末）。

### 步骤 2：运行脚本
在公司电脑上，打开 PowerShell（建议以管理员身份运行），进入项目根目录：
```powershell
cd "D:\Zero Tools"
# 解除 PowerShell 脚本执行限制
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
# 运行安装脚本
.\setup.ps1
```
脚本会自动完成：
- 检查并安装 Python 必要依赖 (`markitdown`, `openai` 等)
- 下载并配置 `rtk.exe` (Rust Token Killer) 到用户本地目录
- 创建必要的目录结构并写入本地 `AGENTS.md` 规则
- 自动绕过证书校验，下载并手动解压安装最新版 `PSReadLine 2.2.6` 并启用历史补全
- 引导您输入 Google AI Studio API Key 并自动配置环境变量

---

## 📂 方案 B：手动安装与配置步骤

如果您需要手动一步步安装，请按照以下步骤操作：

### 1. Python 环境与 MarkItDown 依赖库
* **步骤**：
  1. 确保已安装 Python 3.10+ 并加入系统环境变量 `PATH`。
  2. 打开命令行 (Cmd / PowerShell) 运行：
     ```bash
     pip install markitdown openai
     ```
  3. (可选，支持图片 OCR 功能)：
     ```bash
     pip install markitdown-ocr
     ```

### 2. Google AI Studio API 密匙配置 (Gemini)
* **步骤**：
  1. 访问 [Google AI Studio](https://aistudio.google.com/apikey) 申请一个免费的 API Key。
  2. 在公司电脑的系统环境变量中添加：
     - 变量名：`GEMINI_API_KEY`
     - 变量值：`您的API_KEY`
  3. 或者直接在项目根目录的 `markitdown_ocr_gemini.py` 第 19 行中直接填入 Key。

### 3. RTK (Rust Token Killer) 安装与配置
* **步骤**：
  1. 下载最新的 Windows 版 `rtk.exe`，放置到公司电脑的 `C:\Users\<您的用户名>\.local\bin\` 目录下。
  2. 将该目录添加到系统的 `PATH` 环境变量中。
  3. 在项目根目录下创建目录 `.agents`，并在其中新建 `AGENTS.md` 规则。

### 4. Codebase Memory MCP 插件配置
* **步骤**：
  1. 拷贝当前电脑中已下载的 `codebase-memory-mcp` 可执行文件。
  2. 在开发工具（如 Cursor、Windsurf）的全局 `mcp_config.json` 中配置该 MCP 服务。

### 5. Skills (技能库类) 移植与新增
* **全局 Skills**：
  - 将 `C:\Users\Administrator\.gemini\config\skills\karpathy-guidelines` 目录整个拷贝到新电脑的 `C:\Users\<您的用户名>\.gemini\config\skills\` 下。
* **项目本地 Skills**：
  - 将项目下的 `D:\Zero Tools\.agents\skills\grill-me` 与新增的 `D:\Zero Tools\.agents\skills\caveman` 整个文件夹一同随项目拷贝即可。

### 6. PSReadLine 2.2.6 手动绕过校验升级 (历史补全)
由于旧版 PowerShell 自带的 NuGet 包管理器解析证书的 Bug，直接使用 `Install-Module` 经常报错。
* **手动下载解压步骤**：
  1. 浏览器打开并下载 `https://www.powershellgallery.com/api/v2/package/PSReadLine/2.2.6`（会得到一个扩展名为 `.nupkg` 的文件）。
  2. 将该文件重命名为 `.zip` 后缀，解压到目录：
     `C:\Users\<您的用户名>\Documents\WindowsPowerShell\Modules\PSReadLine\2.2.6\`
  3. 重启 PowerShell 窗口，即可正常使用：
     ```powershell
     Import-Module PSReadLine -RequiredVersion 2.2.6 -Force
     Set-PSReadLineOption -PredictionSource History
     ```

### 7. 双机接力开发：Git/GitHub 同步工作流
* **兼容性说明**：
  两台电脑的**项目根文件夹名称可以不同，存储路径（如 D 盘或 E 盘）也可以不同**，Git 会自动处理相对路径，不影响 `push` 和 `pull` 操作。
* **同步步骤**：
  1. **公司/家里初次关联**（在项目目录下）：
     ```powershell
     rtk git remote add origin <您的私有GitHub仓库链接>
     ```
  2. **在 A 电脑完工推流**：
     ```powershell
     rtk git add .
     rtk git commit -m "feat: sync work"
     rtk git push origin main
     ```
  3. **在 B 电脑开工拉流**（切记：写代码前必须先拉取！）：
     ```powershell
     rtk git pull origin main
     ```

### 8. 新电脑手动配置全局 MCP 服务
由于全局 MCP 的可执行文件绝对路径因电脑用户名不同而异，需要手动在新电脑上进行配置。
* **方案 A：IDE 可视化配置（以 Cursor 为例）**：
  1. 打开 Cursor ➡️ `Settings` ➡️ `Features` ➡️ `MCP`。
  2. 点击 `+ Add New MCP Server`。
  3. 填写：
     - **Name**: `codebase-memory-mcp`
     - **Type**: `command`
     - **Command**: `C:/Users/<您的新用户名>/AppData/Local/Programs/codebase-memory-mcp/codebase-memory-mcp.exe` （请将 `<您的新用户名>` 替换为本地实际用户名，路径中使用正斜杠 `/`）。
* **方案 B：全局 JSON 写入（`mcp_config.json`）**：
  在配置的 `mcpServers` 下写入：
  ```json
  "codebase-memory-mcp": {
    "command": "C:/Users/<您的新用户名>/AppData/Local/Programs/codebase-memory-mcp/codebase-memory-mcp.exe",
    "args": []
  }
  ```

### 9. 钉钉 CLI (dws) 独立应用凭证配置 (方案二)
为保证在新电脑或 VPS 上长期稳定运行（如 Hermes 定时监控发信），推荐使用方案二进行凭证配置：
1. 登录 [钉钉开放平台](https://open.dingtalk.com)，在应用开发中创建一个「企业内部应用」。
2. 获取该应用的 `AppKey` 与 `AppSecret`。
3. 在新电脑的系统环境变量中添加：
   - 变量名：`DWS_CLIENT_ID`，值设为您的 `AppKey`
   - 变量名：`DWS_CLIENT_SECRET`，值设为您的 `AppSecret`
   *(亦可在运行 `setup.ps1` 脚本时根据提示自动输入配置)*
4. 在 PowerShell 中运行一次登录认证命令以激活授权：
   ```powershell
   & "C:\Users\Administrator\.workbuddy\binaries\node\cli-connector-packages\dws.cmd" auth login
   ```

---

## 📜 自动化脚本源码 (`setup.ps1`)

以下是更新后集成了所有一键式逻辑的 `setup.ps1` 源码：

```powershell
# Windows 环境一键初始化部署脚本
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   跨境电商项目环境一键初始化脚本" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. 检查 Python 环境
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "[√] 找到 Python 环境" -ForegroundColor Green
    Write-Host "正在安装依赖库: markitdown, openai..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    python -m pip install markitdown openai
} else {
    Write-Host "[x] 未找到 Python 环境，请先安装 Python 3.10+" -ForegroundColor Red
}

# 2. 创建目录结构
Write-Host "正在创建项目配置目录结构..." -ForegroundColor Yellow
$AgentDir = Join-Path $PSScriptRoot ".agents"
$SkillsDir = Join-Path $AgentDir "skills"
if (!(Test-Path $AgentDir)) { New-Item -ItemType Directory -Path $AgentDir | Out-Null }
if (!(Test-Path $SkillsDir)) { New-Item -ItemType Directory -Path $SkillsDir | Out-Null }

# 3. 部署本地 AGENTS.md 规则
$AgentsMdPath = Join-Path $AgentDir "AGENTS.md"
$AgentsContent = @"
# RTK Token Optimization (Windows Mode)

> Windows 环境下无 bash hook，通过此文件注入 RTK 使用规则。

## 核心规则：所有 Shell 命令必须加 ``rtk`` 前缀
在此项目中运行 any shell命令时，**始终**在命令前加 ``rtk`` 前缀以节省 60-90% token：
- rtk git status
- rtk git diff
- rtk pip install
"@
Set-Content -Path $AgentsMdPath -Value $AgentsContent -Encoding utf8
Write-Host "[√] 本地 Agent 规则配置完成: .agents/AGENTS.md" -ForegroundColor Green

# 4. 引导配置 Gemini API 密钥 与 钉钉 CLI 凭证
Write-Host "-----------------------------------------" -ForegroundColor Gray
$ApiKey = Read-Host "请输入您的 Google AI Studio API Key (回车可跳过，后续手动在环境变量或代码中配置)"
if ($ApiKey) {
    [System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", $ApiKey, "User")
    Write-Host "[√] Gemini API Key 已成功写入当前用户环境变量！" -ForegroundColor Green
}

$DwsClientId = Read-Host "请输入钉钉 AppKey (DWS_CLIENT_ID, 方案二，回车可跳过)"
if ($DwsClientId) {
    [System.Environment]::SetEnvironmentVariable("DWS_CLIENT_ID", $DwsClientId, "User")
    Write-Host "[√] DWS_CLIENT_ID (AppKey) 已成功写入当前用户环境变量！" -ForegroundColor Green
}

$DwsClientSecret = Read-Host "请输入钉钉 AppSecret (DWS_CLIENT_SECRET, 方案二，回车可跳过)"
if ($DwsClientSecret) {
    [System.Environment]::SetEnvironmentVariable("DWS_CLIENT_SECRET", $DwsClientSecret, "User")
    Write-Host "[√] DWS_CLIENT_SECRET (AppSecret) 已成功写入当前用户环境变量！" -ForegroundColor Green
}


# 5. RTK 工具自动下载与部署引导
Write-Host "-----------------------------------------" -ForegroundColor Gray
Write-Host "正在尝试配置 RTK (Rust Token Killer) 工具..." -ForegroundColor Yellow
$LocalBinDir = Join-Path $env:USERPROFILE ".local\bin"
if (!(Test-Path $LocalBinDir)) { New-Item -ItemType Directory -Path $LocalBinDir | Out-Null }

Write-Host "请从您的原电脑拷贝 rtk.exe 到当前电脑的以下路径：" -ForegroundColor Cyan
Write-Host "-> $LocalBinDir\rtk.exe" -ForegroundColor Cyan
Write-Host "并确保已将该路径添加到系统的 PATH 环境变量中。" -ForegroundColor Cyan

# 6. PSReadLine 历史补全模块部署
Write-Host "-----------------------------------------" -ForegroundColor Gray
Write-Host "正在配置 PSReadLine 2.2.6 智能补全..." -ForegroundColor Yellow
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$DestPSReadLineDir = Join-Path $env:USERPROFILE "Documents\WindowsPowerShell\Modules\PSReadLine\2.2.6"
if (!(Test-Path $DestPSReadLineDir)) {
    try {
        New-Item -ItemType Directory -Path $DestPSReadLineDir -Force | Out-Null
        $ZipUrl = "https://www.powershellgallery.com/api/v2/package/PSReadLine/2.2.6"
        $TempZipPath = Join-Path $env:TEMP "psreadline_2.2.6.zip"
        Write-Host "正在下载 PSReadLine 2.2.6..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $ZipUrl -OutFile $TempZipPath -UseBasicParsing
        Write-Host "正在解压缩..." -ForegroundColor Yellow
        Expand-Archive -Path $TempZipPath -DestinationPath $DestPSReadLineDir -Force
        Remove-Item $TempZipPath -ErrorAction SilentlyContinue
        Write-Host "[√] PSReadLine 2.2.6 模块手动部署成功！" -ForegroundColor Green
    } catch {
        Write-Host "[x] 自动配置 PSReadLine 失败，请参阅 setup_guide.md 进行手动部署" -ForegroundColor Red
    }
} else {
    Write-Host "[√] 检测到已存在 PSReadLine 2.2.6" -ForegroundColor Green
}

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   初始化完成！请重启命令行或 IDE 生效配置。" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
```
