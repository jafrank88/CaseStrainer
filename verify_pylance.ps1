#!/usr/bin/env pwsh

Write-Host "🔍 Verifying Pylance Configuration..." -ForegroundColor Cyan

# Check if configuration files exist
$pyrightConfig = "pyrightconfig.json"
$vscodeSettings = ".vscode/settings.json"

if (Test-Path $pyrightConfig) {
    Write-Host "✅ pyrightconfig.json exists" -ForegroundColor Green
    $config = Get-Content $pyrightConfig | ConvertFrom-Json
    Write-Host "  Include: $($config.include -join ', ')" -ForegroundColor White
    Write-Host "  Exclude count: $($config.exclude.Count)" -ForegroundColor White
    
    # Check if archived file is excluded
    if ($config.exclude -contains "**/src/archived_case_name_extraction.py") {
        Write-Host "  ✅ archived_case_name_extraction.py is excluded" -ForegroundColor Green
    } else {
        Write-Host "  ❌ archived_case_name_extraction.py is NOT excluded" -ForegroundColor Red
    }
} else {
    Write-Host "❌ pyrightconfig.json missing!" -ForegroundColor Red
}

if (Test-Path $vscodeSettings) {
    Write-Host "✅ .vscode/settings.json exists" -ForegroundColor Green
} else {
    Write-Host "❌ .vscode/settings.json missing!" -ForegroundColor Red
}

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. In VS Code, press Ctrl+Shift+P" -ForegroundColor White
Write-Host "2. Type: Python: Restart Language Server" -ForegroundColor White
Write-Host "3. Press Enter" -ForegroundColor White
Write-Host "4. Wait for Pylance to reload" -ForegroundColor White
Write-Host "5. Check Problems panel - should show ~335 errors instead of 10K+" -ForegroundColor White

Write-Host "`n🎯 Expected Results:" -ForegroundColor Cyan
Write-Host "- archived_case_name_extraction.py: No Pylance errors" -ForegroundColor White
Write-Host "- app_final_vue.py: No unused import errors" -ForegroundColor White
Write-Host "- citation_extractor.py: No redeclaration errors" -ForegroundColor White 