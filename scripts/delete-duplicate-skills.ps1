# Delete Duplicate Skills Folder
# This script will attempt to delete the duplicate skills folder

$targetPath = "C:\Users\china\.gemini\antigravity\skills"

Write-Host ""
Write-Host "=== Delete Duplicate Skills Folder ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "Target: $targetPath" -ForegroundColor Cyan
Write-Host ""

# Check if folder exists
if (-not (Test-Path $targetPath)) {
    Write-Host "[OK] Folder does not exist. Nothing to delete." -ForegroundColor Green
    exit 0
}

# Show folder size
$size = (Get-ChildItem -Path $targetPath -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Folder size: $([math]::Round($size, 2)) MB" -ForegroundColor Gray
Write-Host ""

# Confirm deletion
Write-Host "WARNING: This will delete the duplicate skills folder." -ForegroundColor Red
Write-Host "The main skills folder at C:\Users\china\.agent\skills will NOT be affected." -ForegroundColor Green
Write-Host ""
$confirm = Read-Host "Type 'YES' to confirm deletion"

if ($confirm -ne "YES") {
    Write-Host "Deletion cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Attempting to delete..." -ForegroundColor Cyan

# Try to delete
try {
    # First, try to unlock files
    Get-ChildItem -Path $targetPath -Recurse -File | ForEach-Object {
        try {
            $_.IsReadOnly = $false
        }
        catch {
            # Ignore errors
        }
    }
    
    # Delete the folder
    Remove-Item -Path $targetPath -Recurse -Force -ErrorAction Stop
    
    Write-Host ""
    Write-Host "[SUCCESS] Duplicate skills folder deleted!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Remaining skills folders:" -ForegroundColor Cyan
    Write-Host "  1. C:\Users\china\.agent\skills (MAIN - 18 skills)" -ForegroundColor Green
    Write-Host "  2. C:\Users\china\superpowers\skills (Workflows - 14 skills)" -ForegroundColor Yellow
    
}
catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to delete folder" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Possible solutions:" -ForegroundColor Cyan
    Write-Host "  1. Close Antigravity and try again" -ForegroundColor White
    Write-Host "  2. Restart your computer" -ForegroundColor White
    Write-Host "  3. Manually delete the folder in File Explorer" -ForegroundColor White
    Write-Host "     Path: $targetPath" -ForegroundColor Gray
    exit 1
}
