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
在此项目中运行 any shell 命令时，**始终**在命令前加 ``rtk`` 前缀以节省 60-90% token：
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
