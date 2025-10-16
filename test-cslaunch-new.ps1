# test-cslaunch-new.ps1 - Test the refactored cslaunch script

Write-Host "`n=== Testing Refactored cslaunch ===" -ForegroundColor Cyan
Write-Host "This script tests all modules and functions" -ForegroundColor Gray

$modulePath = Join-Path $PSScriptRoot "scripts\modules"
$testsPassed = 0
$testsFailed = 0

function Test-Module {
    param(
        [string]$ModuleName,
        [string[]]$ExpectedFunctions
    )
    
    Write-Host "`nTesting $ModuleName..." -ForegroundColor Yellow
    
    try {
        $modulePath = Join-Path $PSScriptRoot "scripts\modules\$ModuleName"
        Import-Module $modulePath -Force -ErrorAction Stop
        
        Write-Host "  ✓ Module loaded" -ForegroundColor Green
        $script:testsPassed++
        
        # Check exported functions
        $module = Get-Module $ModuleName.Replace('.psm1', '')
        $exportedFunctions = $module.ExportedFunctions.Keys
        
        foreach ($func in $ExpectedFunctions) {
            if ($exportedFunctions -contains $func) {
                Write-Host "  ✓ Function exported: $func" -ForegroundColor Green
                $script:testsPassed++
            } else {
                Write-Host "  ✗ Function missing: $func" -ForegroundColor Red
                $script:testsFailed++
            }
        }
        
    } catch {
        Write-Host "  ✗ Failed to load module: $($_.Exception.Message)" -ForegroundColor Red
        $script:testsFailed++
    }
}

# Test VueBuild module
Test-Module "VueBuild.psm1" @(
    'Test-VueBuildNeeded',
    'Start-VueBuild',
    'Copy-VueDistToStatic',
    'Update-VueFrontend'
)

# Test HealthCheck module
Test-Module "HealthCheck.psm1" @(
    'Test-DockerHealth',
    'Test-FrontendHealth',
    'Test-BackendHealth',
    'Test-ApplicationHealth',
    'Test-ComprehensiveHealth'
)

# Test FileMonitoring module
Test-Module "FileMonitoring.psm1" @(
    'Initialize-FileMonitoring',
    'Get-StoredHash',
    'Set-StoredHash',
    'Test-FileChanged',
    'Get-ChangedFiles',
    'Clear-FileMonitoringCache'
)

# Test Deployment module
Test-Module "Deployment.psm1" @(
    'Start-QuickDeployment',
    'Start-FastDeployment',
    'Start-FullDeployment',
    'Start-FrontendDeployment',
    'Start-BackendDeployment',
    'Start-SmartDeployment'
)

# Test main script exists
Write-Host "`nTesting main script..." -ForegroundColor Yellow
if (Test-Path "cslaunch-new.ps1") {
    Write-Host "  ✓ cslaunch-new.ps1 exists" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "  ✗ cslaunch-new.ps1 not found" -ForegroundColor Red
    $testsFailed++
}

# Test help works
Write-Host "`nTesting help..." -ForegroundColor Yellow
try {
    $helpOutput = & .\cslaunch-new.ps1 -Help 2>&1
    if ($helpOutput -match "CaseStrainer Deployment Tool") {
        Write-Host "  ✓ Help displays correctly" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  ✗ Help output unexpected" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "  ✗ Help failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test function calls
Write-Host "`nTesting function calls..." -ForegroundColor Yellow

try {
    Import-Module (Join-Path $PSScriptRoot "scripts\modules\VueBuild.psm1") -Force
    $buildNeeded = Test-VueBuildNeeded
    Write-Host "  ✓ Test-VueBuildNeeded: $buildNeeded" -ForegroundColor Green
    $testsPassed++
} catch {
    Write-Host "  ✗ Test-VueBuildNeeded failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

try {
    Import-Module (Join-Path $PSScriptRoot "scripts\modules\HealthCheck.psm1") -Force
    $dockerHealthy = Test-DockerHealth
    Write-Host "  ✓ Test-DockerHealth: $dockerHealthy" -ForegroundColor Green
    $testsPassed++
} catch {
    Write-Host "  ✗ Test-DockerHealth failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

try {
    Import-Module (Join-Path $PSScriptRoot "scripts\modules\FileMonitoring.psm1") -Force
    $initialized = Initialize-FileMonitoring
    Write-Host "  ✓ Initialize-FileMonitoring: $initialized" -ForegroundColor Green
    $testsPassed++
} catch {
    Write-Host "  ✗ Initialize-FileMonitoring failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Tests Passed: $testsPassed" -ForegroundColor Green
Write-Host "Tests Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { 'Green' } else { 'Red' })

if ($testsFailed -eq 0) {
    Write-Host "`n✓ All tests passed! Ready to use cslaunch-new.ps1" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "  1. Run: .\cslaunch-new.ps1" -ForegroundColor White
    Write-Host "  2. Test different modes" -ForegroundColor White
    Write-Host "  3. If everything works, replace old cslaunch.ps1" -ForegroundColor White
} else {
    Write-Host "`n✗ Some tests failed. Please fix issues before using." -ForegroundColor Red
}
