# Run this script as Administrator / 请以管理员身份运行此脚本

# 1. Define Target Base Directory / 定义目标迁移根目录
$targetDrive = "D:"  # Change to your target drive (e.g., E:, F:) / 可改为其他盘符如 E:, F:
$targetBase = "$targetDrive\AgentSystem"

# 2. Resolve Environment Variables / 动态解析系统环境变量
$userProfile = $env:USERPROFILE
$localAppData = $env:LOCALAPPDATA
$appData = $env:APPDATA

# 3. Define source and target mappings / 定义源目录与目标目录映射
$mappings = @{
    # User Profile Folders / 用户目录下的智能体文件夹
    "$userProfile\.gemini" = "$targetBase\.gemini"
    "$userProfile\.codex" = "$targetBase\.codex"
    "$userProfile\.workbuddy" = "$targetBase\.workbuddy"
    "$userProfile\.agents" = "$targetBase\.agents"
    "$userProfile\.cc-switch" = "$targetBase\.cc-switch"
    "$userProfile\.antigravity" = "$targetBase\.antigravity"
    "$userProfile\.antigravity-ide" = "$targetBase\.antigravity-ide"
    "$userProfile\.antigravity_cockpit" = "$targetBase\.antigravity_cockpit"
    "$userProfile\.notebooklm-mcp-cli" = "$targetBase\.notebooklm-mcp-cli"
    
    # Large Development Cache and Dependency Folders / 缓存与大文件目录
    "$userProfile\.cache" = "$targetBase\.cache"
    "$userProfile\node_modules" = "$targetBase\node_modules"
    "$userProfile\WorkBuddy" = "$targetBase\WorkBuddy"
    
    # AppData Local & Roaming Folders / AppData 目录下的智能体文件夹
    "$localAppData\hermes" = "$targetBase\AppData_Local_hermes"
    "$appData\Hermes" = "$targetBase\AppData_Roaming_Hermes"
    "$localAppData\WorkBuddy" = "$targetBase\AppData_Local_WorkBuddy"
    "$localAppData\@genieworkbuddy-desktop-updater" = "$targetBase\AppData_Local_genieworkbuddy-desktop-updater"
    "$localAppData\Programs\antigravity" = "$targetBase\AppData_Local_Programs_antigravity"
    "$localAppData\Programs\codebase-memory-mcp" = "$targetBase\AppData_Local_Programs_codebase-memory-mcp"
    
    # Global Python (Change if your Python is installed in a different path) / 全局 Python 目录（若路径不同请自行修改）
    "C:\Python314" = "$targetBase\Python314"
}

# 4. Check for active agent processes / 自动提示并检查活跃进程
$processNames = @("claude", "codex", "hermes", "workbuddy", "antigravity", "cc-switch", "node", "python")
$activeProcesses = Get-Process | Where-Object { $processNames -contains $_.ProcessName }
if ($activeProcesses) {
    Write-Warning "The following processes are running and may lock files:"
    $activeProcesses | Select-Object ProcessName, Id | Format-Table
    Write-Warning "Please close them before proceeding, or they might cause migration failure."
    Read-Host "Press ENTER to continue once all processes are closed..."
}

# 5. Move folders and create junctions / 移动目录并创建目录联接
foreach ($src in $mappings.Keys) {
    $dest = $mappings[$src]
    if (Test-Path $src) {
        if (-not (Test-Path $dest)) {
            New-Item -ItemType Directory -Force -Path (Split-Path $dest)
            Write-Host "Moving $src to $dest..."
            # Move folder using robocopy to preserve permissions / 使用 robocopy 移动以保留权限
            robocopy $src $dest /E /MOVE /COPYALL /R:1 /W:1
        }
        if (-not (Test-Path $src)) {
            Write-Host "Creating junction from $src to $dest..."
            cmd /c mklink /J "$src" "$dest"
        } else {
            Write-Warning "Source folder $src still exists, skip junction creation."
        }
    }
}

# 6. Create shared skills directory and link / 创建共享 SKILL 目录并建立联接
$sharedSkills = "$targetBase\shared_skills"
if (-not (Test-Path $sharedSkills)) {
    New-Item -ItemType Directory -Force -Path $sharedSkills
}

$skillsFolders = @(
    "$targetBase\.gemini\config\skills",
    "$targetBase\.codex\skills",
    "$targetBase\.workbuddy\skills",
    "$targetBase\AppData_Local_hermes\skills"
)

foreach ($sf in $skillsFolders) {
    if (Test-Path $sf) {
        # Move existing skills to shared directory / 将现有技能移至共享目录
        Get-ChildItem -Path $sf | ForEach-Object {
            $targetPath = Join-Path $sharedSkills $_.Name
            if (-not (Test-Path $targetPath)) {
                Move-Item -Path $_.FullName -Destination $sharedSkills -Force
            }
        }
        Remove-Item -Path $sf -Recurse -Force
    }
    # Create junction for skills / 创建技能目录联接
    cmd /c mklink /J "$sf" "$sharedSkills"
}

Write-Host "Migration complete! / 迁移完成！"
