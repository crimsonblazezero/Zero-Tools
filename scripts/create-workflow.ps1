# Create New Workflow Script
# Quick workflow creation tool

param(
    [Parameter(Mandatory = $true)]
    [string]$WorkflowName,
    
    [Parameter(Mandatory = $false)]
    [string]$Description = "Description for this workflow",
    
    [Parameter(Mandatory = $false)]
    [string]$SkillName = ""
)

$workflowsPath = "D:\KovaScape Tools\.agent\workflows"
$templatePath = Join-Path $workflowsPath "_template.md"
$newWorkflowPath = Join-Path $workflowsPath "$WorkflowName.md"

Write-Host ""
Write-Host "=== Create New Workflow ===" -ForegroundColor Green
Write-Host ""

# Check if workflow already exists
if (Test-Path $newWorkflowPath) {
    Write-Host "[ERROR] Workflow already exists: $WorkflowName.md" -ForegroundColor Red
    Write-Host "Path: $newWorkflowPath" -ForegroundColor Yellow
    Write-Host ""
    $overwrite = Read-Host "Overwrite? (yes/no)"
    if ($overwrite -ne "yes") {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Check if template exists
if (-not (Test-Path $templatePath)) {
    Write-Host "[ERROR] Template not found: _template.md" -ForegroundColor Red
    Write-Host "Path: $templatePath" -ForegroundColor Yellow
    exit 1
}

# If skill name not provided, use workflow name
if ($SkillName -eq "") {
    $SkillName = $WorkflowName
}

# Read template
$template = Get-Content $templatePath -Raw

# Replace placeholders
$content = $template -replace '\[一句话描述这个 workflow 的用途\]', $Description
$content = $content -replace 'workflow-name', $WorkflowName
$content = $content -replace '\[skill-name\]', $SkillName

# Write new workflow file
$content | Out-File -FilePath $newWorkflowPath -Encoding UTF8

Write-Host "[SUCCESS] Workflow created!" -ForegroundColor Green
Write-Host ""
Write-Host "Workflow name: $WorkflowName" -ForegroundColor Cyan
Write-Host "File path: $newWorkflowPath" -ForegroundColor Gray
Write-Host "Skill: $SkillName" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit the workflow file:" -ForegroundColor White
Write-Host "   code `"$newWorkflowPath`"" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Fill in the details:" -ForegroundColor White
Write-Host "   - Update description" -ForegroundColor Gray
Write-Host "   - Add usage steps" -ForegroundColor Gray
Write-Host "   - Provide examples" -ForegroundColor Gray
Write-Host "   - Add best practices" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Test the workflow:" -ForegroundColor White
Write-Host "   Type in conversation: /$WorkflowName" -ForegroundColor Gray
Write-Host ""

# Ask if user wants to open the file
$open = Read-Host "Open in VS Code now? (yes/no)"
if ($open -eq "yes") {
    code $newWorkflowPath
}
