# Enhanced Docker Monitoring Setup
# Installs comprehensive Docker health monitoring with auto-recovery

Write-Host "🚀 Setting up Enhanced Docker Monitoring..." -ForegroundColor Cyan

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
    Write-Host "✅ Created logs directory" -ForegroundColor Green
}

# Test the health check script
Write-Host "`n🔍 Testing Docker health check..." -ForegroundColor Cyan
try {
    & .\docker_health_check.ps1 -DeepDiagnostics
    Write-Host "✅ Health check script is working" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check script failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Install the scheduled task
Write-Host "`n📅 Installing scheduled task..." -ForegroundColor Cyan
& .\docker_monitor_auto.ps1 -InstallScheduledTask -CheckIntervalMinutes 5

# Test the monitoring system
Write-Host "`n🧪 Testing monitoring system..." -ForegroundColor Cyan
& .\docker_monitor_auto.ps1

Write-Host "`n🎉 Enhanced Docker Monitoring Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 What was installed:" -ForegroundColor Cyan
Write-Host "   • Enhanced health check with deep diagnostics" -ForegroundColor Gray
Write-Host "   • Auto-recovery capabilities" -ForegroundColor Gray
Write-Host "   • Scheduled task (runs every 5 minutes)" -ForegroundColor Gray
Write-Host "   • Comprehensive logging" -ForegroundColor Gray
Write-Host ""
Write-Host "🔧 Available commands:" -ForegroundColor Cyan
Write-Host "   • .\cslaunch.ps1 -HealthCheck     # Manual health check with auto-recovery" -ForegroundColor Gray
Write-Host "   • .\docker_monitor_auto.ps1       # Show monitoring status" -ForegroundColor Gray
Write-Host "   • .\docker_monitor_auto.ps1 -TestMode  # Run continuous monitoring" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 Monitoring will:" -ForegroundColor Cyan
Write-Host "   • Check Docker health every 5 minutes" -ForegroundColor Gray
Write-Host "   • Automatically restart Docker if unresponsive" -ForegroundColor Gray
Write-Host "   • Collect diagnostic logs when issues occur" -ForegroundColor Gray
Write-Host "   • Log all recoveries to logs\docker_recovery.log" -ForegroundColor Gray 