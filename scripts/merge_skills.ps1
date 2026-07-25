$TargetDir = "d:\Zero Tools\skills"
if (-not (Test-Path -Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force
}

$Source1 = "d:\Zero Tools\.agents\skills"
if (Test-Path -Path $Source1) {
    Get-ChildItem -Path $Source1 -Directory | ForEach-Object {
        $destItem = Join-Path $TargetDir $_.Name
        if (-not (Test-Path -Path $destItem)) {
            Write-Host "Copying $($_.Name) from .agents/skills to skills..."
            Copy-Item -Path $_.FullName -Destination $destItem -Recurse -Force
        }
    }
}

$Source2 = "D:\AgentSystem\shared_skills"
if (Test-Path -Path $Source2) {
    Get-ChildItem -Path $Source2 -Directory | ForEach-Object {
        $skillMd = Join-Path $_.FullName "SKILL.md"
        if (Test-Path -Path $skillMd) {
            $destItem = Join-Path $TargetDir $_.Name
            if (-not (Test-Path -Path $destItem)) {
                Write-Host "Copying $($_.Name) from shared_skills to skills..."
                Copy-Item -Path $_.FullName -Destination $destItem -Recurse -Force
            }
        }
    }
}

Write-Host "Skill merge complete!" -ForegroundColor Green
