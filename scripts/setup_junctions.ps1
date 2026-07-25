param()

$MasterPath = "d:\Zero Tools\skills"

function New-JunctionLink {
    param(
        [string]$LinkPath,
        [string]$TargetPath
    )
    if (Test-Path $LinkPath) {
        Write-Host "Removing old link at $LinkPath"
        Remove-Item -Path $LinkPath -Recurse -Force -ErrorAction SilentlyContinue
        if (Test-Path $LinkPath) {
            cmd /c rmdir /s /q "$LinkPath"
        }
    }
    Write-Host "Creating Junction: $LinkPath -> $TargetPath"
    cmd /c mklink /J "$LinkPath" "$TargetPath"
}

New-JunctionLink -LinkPath "d:\Zero Tools\.agents\skills" -TargetPath $MasterPath
New-JunctionLink -LinkPath "D:\AgentSystem\.gemini\config\skills" -TargetPath $MasterPath
New-JunctionLink -LinkPath "D:\AgentSystem\.codex\skills" -TargetPath $MasterPath
New-JunctionLink -LinkPath "D:\AgentSystem\.workbuddy\skills" -TargetPath $MasterPath
New-JunctionLink -LinkPath "D:\AgentSystem\AppData_Local_hermes\skills" -TargetPath $MasterPath

Write-Host "All junctions created successfully!" -ForegroundColor Green
