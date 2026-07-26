# 一键 GitHub 双向同步脚本 (Home & Office Sync)
param(
    [string]$CommitMessage = "sync: 自动同步技能与工作区修改"
)

$RepoDir = "d:\Zero Tools"
Set-Location $RepoDir

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "      Zero Tools - GitHub 双向同步工具    " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. 尝试先拉取远程更新
Write-Host "[1/3] 正在拉取 GitHub 远程仓库最新变更..." -ForegroundColor Yellow
git pull --rebase origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] 自动合并遇到冲突，请检查文件冲突处理后再试。" -ForegroundColor Red
    exit 1
}

# 2. 检查本地是否有待提交的修改或新技能
$status = git status --porcelain
if ($status) {
    Write-Host "[2/3] 检测到本地 Agent 新增/修改了技能或代码，正在自动提交..." -ForegroundColor Yellow
    git add .
    git commit -m "$CommitMessage"
    
    # 3. 推送到 GitHub
    Write-Host "[3/3] 正在推送到 GitHub..." -ForegroundColor Yellow
    git push origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[√] 成功将最新技能与修改推送到 GitHub！" -ForegroundColor Green
    } else {
        Write-Host "[x] 推送到 GitHub 失败，请检查网络或 Git 权限。" -ForegroundColor Red
    }
} else {
    Write-Host "[√] 本地没有新增修改，同步完成（当前已是最新状态）！" -ForegroundColor Green
}

Write-Host "=========================================" -ForegroundColor Cyan
