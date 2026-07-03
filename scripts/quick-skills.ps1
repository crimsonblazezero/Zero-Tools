# KovaScape Tools - Quick Skills Access
# Run: powershell -ExecutionPolicy Bypass -File .\scripts\quick-skills.ps1

$GLOBAL_SKILLS = "C:\Users\china\.agent\skills"

Write-Host ""
Write-Host "=== KovaScape Tools - Skills Manager ===" -ForegroundColor Green
Write-Host ""

if (-not (Test-Path $GLOBAL_SKILLS)) {
    Write-Host "[ERROR] Global skills folder not found!" -ForegroundColor Red
    Write-Host "Path: $GLOBAL_SKILLS" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1] Open Skills Folder" -ForegroundColor Cyan
Write-Host "[2] List All Skills" -ForegroundColor Cyan
Write-Host "[3] Open in VS Code" -ForegroundColor Cyan
Write-Host "[4] Validate Paths" -ForegroundColor Cyan
Write-Host "[0] Exit" -ForegroundColor Cyan
Write-Host ""

$choice = Read-Host "Select option"

switch ($choice) {
    "1" {
        Write-Host "Opening folder..." -ForegroundColor Green
        explorer $GLOBAL_SKILLS
    }
    "2" {
        Write-Host ""
        Write-Host "=== Installed Skills ===" -ForegroundColor Green
        $skills = Get-ChildItem -Path $GLOBAL_SKILLS -Directory | Sort-Object Name
        $count = 0
        foreach ($skill in $skills) {
            $count++
            Write-Host "  [$count] $($skill.Name)" -ForegroundColor Yellow
        }
        Write-Host ""
        Write-Host "Total: $count skills" -ForegroundColor Green
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    "3" {
        Write-Host "Opening in VS Code..." -ForegroundColor Green
        code $GLOBAL_SKILLS
    }
    "4" {
        Write-Host ""
        Write-Host "=== Path Validation ===" -ForegroundColor Green
        Write-Host ""
        
        $paths = @{
            "Global Skills" = "C:\Users\china\.agent\skills"
            "Project Root"  = "D:\KovaScape Tools"
            "Scripts"       = "D:\KovaScape Tools\scripts"
            "Config"        = "D:\KovaScape Tools\config"
        }
        
        $allValid = $true
        foreach ($name in $paths.Keys) {
            $path = $paths[$name]
            if (Test-Path $path) {
                Write-Host "[OK] $name" -ForegroundColor Green
                Write-Host "     $path" -ForegroundColor Gray
            }
            else {
                Write-Host "[FAIL] $name" -ForegroundColor Red
                Write-Host "       $path" -ForegroundColor Yellow
                $allValid = $false
            }
        }
        
        Write-Host ""
        if ($allValid) {
            Write-Host "All paths validated successfully!" -ForegroundColor Green
        }
        else {
            Write-Host "Some paths are missing. Please check configuration." -ForegroundColor Yellow
        }
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
    "0" {
        Write-Host "Goodbye!" -ForegroundColor Green
        exit 0
    }
    default {
        Write-Host "Invalid choice" -ForegroundColor Red
    }
}
