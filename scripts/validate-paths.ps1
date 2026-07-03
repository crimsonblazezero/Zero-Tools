# ============================================
# KovaScape Tools - 路径验证脚本
# Path Validation Script
# ============================================

# 读取配置文件 / Read configuration file
$configPath = "D:\KovaScape Tools\config\paths.json"

if (-not (Test-Path $configPath)) {
    Write-Host "❌ 错误：配置文件不存在！" -ForegroundColor Red
    Write-Host "❌ Error: Configuration file does not exist!" -ForegroundColor Red
    Write-Host "路径 / Path: $configPath" -ForegroundColor Yellow
    exit 1
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json

Write-Host ""
Write-Host "🔍 KovaScape Tools - 路径验证器" -ForegroundColor Green
Write-Host "🔍 KovaScape Tools - Path Validator" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 验证所有路径 / Validate all paths
$allValid = $true
$pathsToCheck = @{
    "全局 Skills / Global Skills" = $config.paths.global_skills
    "项目根目录 / Project Root"      = $config.paths.project_root
    "脚本目录 / Scripts"            = $config.paths.scripts
    "数据目录 / Data"               = $config.paths.data
    "资源目录 / Assets"             = $config.paths.assets
    "源代码目录 / Source"            = $config.paths.src
    "文档目录 / Docs"               = $config.paths.docs
}

foreach ($name in $pathsToCheck.Keys) {
    $path = $pathsToCheck[$name]
    if (Test-Path $path) {
        Write-Host "✅ $name" -ForegroundColor Green
        Write-Host "   $path" -ForegroundColor Gray
    }
    else {
        Write-Host "❌ $name" -ForegroundColor Red
        Write-Host "   $path" -ForegroundColor Yellow
        $allValid = $false
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($allValid) {
    Write-Host "✅ 所有路径验证通过！" -ForegroundColor Green
    Write-Host "✅ All paths validated successfully!" -ForegroundColor Green
}
else {
    Write-Host "⚠️  部分路径不存在，请检查配置！" -ForegroundColor Yellow
    Write-Host "⚠️  Some paths do not exist, please check configuration!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 建议 / Suggestions:" -ForegroundColor Cyan
    Write-Host "1. 检查是否在正确的环境（公司/家里）" -ForegroundColor White
    Write-Host "   Check if in correct environment (company/home)" -ForegroundColor Gray
    Write-Host "2. 更新 config/paths.json 中的路径" -ForegroundColor White
    Write-Host "   Update paths in config/paths.json" -ForegroundColor Gray
    Write-Host "3. 创建缺失的目录" -ForegroundColor White
    Write-Host "   Create missing directories" -ForegroundColor Gray
}

Write-Host ""

# 验证 Skills / Validate Skills
Write-Host "📚 验证已安装的 Skills / Validating Installed Skills" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

if (Test-Path $config.paths.global_skills) {
    $installedSkills = Get-ChildItem -Path $config.paths.global_skills -Directory | Select-Object -ExpandProperty Name
    $configSkills = $config.skills.installed
    
    $missingInConfig = $installedSkills | Where-Object { $_ -notin $configSkills }
    $missingInFolder = $configSkills | Where-Object { $_ -notin $installedSkills }
    
    if ($missingInConfig.Count -eq 0 -and $missingInFolder.Count -eq 0) {
        Write-Host "✅ Skills 配置与实际一致！" -ForegroundColor Green
        Write-Host "✅ Skills configuration matches actual installation!" -ForegroundColor Green
    }
    else {
        if ($missingInConfig.Count -gt 0) {
            Write-Host "⚠️  文件夹中存在但配置中缺失的 Skills:" -ForegroundColor Yellow
            Write-Host "⚠️  Skills in folder but missing in config:" -ForegroundColor Yellow
            foreach ($skill in $missingInConfig) {
                Write-Host "   - $skill" -ForegroundColor Yellow
            }
        }
        if ($missingInFolder.Count -gt 0) {
            Write-Host "⚠️  配置中存在但文件夹中缺失的 Skills:" -ForegroundColor Yellow
            Write-Host "⚠️  Skills in config but missing in folder:" -ForegroundColor Yellow
            foreach ($skill in $missingInFolder) {
                Write-Host "   - $skill" -ForegroundColor Yellow
            }
        }
    }
}
else {
    Write-Host "❌ 无法验证 Skills（全局文件夹不存在）" -ForegroundColor Red
    Write-Host "❌ Cannot validate Skills (global folder does not exist)" -ForegroundColor Red
}

Write-Host ""
