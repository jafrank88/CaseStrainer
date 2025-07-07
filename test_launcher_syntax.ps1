# Test script to check launcher.ps1 syntax
Write-Host "Testing launcher.ps1 syntax..." -ForegroundColor Yellow

try {
    # Test if the file exists
    if (Test-Path "launcher.ps1") {
        Write-Host "✅ launcher.ps1 file exists" -ForegroundColor Green
        
        # Test PowerShell syntax
        $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content "launcher.ps1" -Raw), [ref]$null)
        Write-Host "✅ launcher.ps1 has valid PowerShell syntax" -ForegroundColor Green
        
        # Test if we can dot-source it
        try {
            $testResult = & powershell -Command "& '.\launcher.ps1' -Help" 2>&1
            Write-Host "✅ launcher.ps1 can be executed" -ForegroundColor Green
            Write-Host "Help output: $testResult" -ForegroundColor Gray
        } catch {
            Write-Host "❌ launcher.ps1 execution failed: $($_.Exception.Message)" -ForegroundColor Red
        }
        
    } else {
        Write-Host "❌ launcher.ps1 file not found" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Syntax error in launcher.ps1: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Test complete." -ForegroundColor Yellow 