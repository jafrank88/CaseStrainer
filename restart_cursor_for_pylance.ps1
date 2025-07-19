#!/usr/bin/env pwsh

Write-Host "🔄 Restarting Cursor to reload Pylance configuration..." -ForegroundColor Cyan

# Stop any running Cursor processes
Write-Host "Stopping Cursor processes..." -ForegroundColor Yellow
try {
    Get-Process -Name "Cursor" -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "✅ Cursor processes stopped" -ForegroundColor Green
} catch {
    Write-Host "ℹ️  No Cursor processes found running" -ForegroundColor Blue
}

# Wait a moment for processes to fully stop
Start-Sleep -Seconds 2

# Start Cursor
Write-Host "Starting Cursor..." -ForegroundColor Yellow
try {
    Start-Process "Cursor"
    Write-Host "✅ Cursor started successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to start Cursor. Please start it manually." -ForegroundColor Red
}

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Wait for Cursor to fully load" -ForegroundColor White
Write-Host "2. Check the Problems panel" -ForegroundColor White
Write-Host "3. You should see significantly fewer Pylance errors" -ForegroundColor White
Write-Host "4. Expected: ~50-100 errors instead of 150+ errors" -ForegroundColor White

Write-Host "`n🎯 Expected Results:" -ForegroundColor Cyan
Write-Host "- Import errors: Should be minimal" -ForegroundColor White
Write-Host "- Type annotation errors: Should be suppressed" -ForegroundColor White
Write-Host "- Attribute access errors: Should be reduced" -ForegroundColor White
Write-Host "- Overall error count: Should drop significantly" -ForegroundColor White

Write-Host "`n✅ Pylance configuration updated with:" -ForegroundColor Green
Write-Host "- Enhanced type checking suppressions" -ForegroundColor White
Write-Host "- Untyped code suppressions" -ForegroundColor White
Write-Host "- Attribute access suppressions" -ForegroundColor White
Write-Host "- Import error suppressions" -ForegroundColor White 