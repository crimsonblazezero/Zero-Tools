# ============================================
# KovaScape Tools - 快速访问全局 Skills 脚本
# Quick Access to Global Skills Folder
# ============================================

# 全局 Skills 路径 / Global Skills Path
$GLOBAL_SKILLS_PATH = "C:\Users\china\.agent\skills"

# 检查路径是否存在 / Check if path exists
if (-not (Test-Path $GLOBAL_SKILLS_PATH)) {
    Write-Host "❌ 错误：全局 Skills 文件夹不存在！" -ForegroundColor Red
    Write-Host "❌ Error: Global Skills folder does not exist!" -ForegroundColor Red
    Write-Host "路径 / Path: $GLOBAL_SKILLS_PATH" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 可能的解决方案 / Possible Solutions:" -ForegroundColor Cyan
    Write-Host "1. 检查用户名是否正确 / Check if username is correct"
    Write-Host "2. 检查是否已安装 Antigravity / Check if Antigravity is installed"
    Write-Host "3. 手动创建文件夹 / Manually create the folder: mkdir '$GLOBAL_SKILLS_PATH'"
    exit 1
}

# 显示菜单 / Display Menu
Write-Host ""
Write-Host "🚀 KovaScape Tools - Skills 管理器" -ForegroundColor Green
Write-Host "🚀 KovaScape Tools - Skills Manager" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "请选择操作 / Please select an action:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  [1] 打开 Skills 文件夹 / Open Skills Folder"
Write-Host "  [2] 列出所有 Skills / List All Skills"
Write-Host "  [3] 搜索 Skill / Search for a Skill"
Write-Host "  [4] 查看 Skill 详情 / View Skill Details"
Write-Host "  [5] 在 VS Code 中打开 / Open in VS Code"
Write-Host "  [0] 退出 / Exit"
Write-Host ""

$choice = Read-Host "输入选项 / Enter choice"

switch ($choice) {
    "1" {
        Write-Host "📂 正在打开文件夹... / Opening folder..." -ForegroundColor Cyan
        explorer $GLOBAL_SKILLS_PATH
    }
    "2" {
        Write-Host ""
        Write-Host "📚 已安装的 Skills / Installed Skills:" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
        $skills = Get-ChildItem -Path $GLOBAL_SKILLS_PATH -Directory | Sort-Object Name
        $count = 0
        foreach ($skill in $skills) {
            $count++
            Write-Host "  [$count] $($skill.Name)" -ForegroundColor Yellow
        }
        Write-Host ""
        Write-Host "✅ 共 $count 个 Skills / Total: $count skills" -ForegroundColor Green
        Write-Host ""
        Read-Host "按回车键继续 / Press Enter to continue"
    }
    "3" {
        $searchTerm = Read-Host "输入搜索关键词 / Enter search term"
        Write-Host ""
        Write-Host "🔍 搜索结果 / Search Results:" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
        $results = Get-ChildItem -Path $GLOBAL_SKILLS_PATH -Directory | Where-Object { $_.Name -like "*$searchTerm*" }
        if ($results.Count -eq 0) {
            Write-Host "  ❌ 未找到匹配的 Skill / No matching skills found" -ForegroundColor Red
        } else {
            foreach ($result in $results) {
                Write-Host "  ✅ $($result.Name)" -ForegroundColor Yellow
            }
        }
        Write-Host ""
        Read-Host "按回车键继续 / Press Enter to continue"
    }
    "4" {
        $skillName = Read-Host "输入 Skill 名称 / Enter skill name"
        $skillPath = Join-Path $GLOBAL_SKILLS_PATH $skillName
        $skillMd = Join-Path $skillPath "SKILL.md"
        
        if (Test-Path $skillMd) {
            Write-Host ""
            Write-Host "📖 Skill 详情 / Skill Details:" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Cyan
            Get-Content $skillMd -Head 20
            Write-Host ""
            Read-Host "按回车键继续 / Press Enter to continue"
        } else {
            Write-Host "❌ 未找到 Skill: $skillName" -ForegroundColor Red
        }
    }
    "5" {
        Write-Host "💻 正在用 VS Code 打开... / Opening in VS Code..." -ForegroundColor Cyan
        code $GLOBAL_SKILLS_PATH
    }
    "0" {
        Write-Host "👋 再见！/ Goodbye!" -ForegroundColor Green
        exit 0
    }
    default {
        Write-Host "❌ 无效选项 / Invalid choice" -ForegroundColor Red
    }
}
