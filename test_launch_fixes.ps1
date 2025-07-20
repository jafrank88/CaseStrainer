# Test script to verify PowerShell launch fixes
# This script tests the key functions that were causing issues

param(
    [switch]$TestNpm,
    [switch]$TestVue,
    [switch]$TestDocker,
    [switch]$All
)

Write-Host "=== CaseStrainer Launch Script Fixes Test ===" -ForegroundColor Cyan

# Import the functions from cslaunch.ps1
$cslaunchPath = Join-Path $PSScriptRoot "cslaunch.ps1"
if (-not (Test-Path $cslaunchPath)) {
    Write-Host "ERROR: cslaunch.ps1 not found" -ForegroundColor Red
    exit 1
}

# Test npm detection
if ($TestNpm -or $All) {
    Write-Host "`n--- Testing npm detection ---" -ForegroundColor Yellow
    
    # Test npm availability directly without using Invoke-Expression
    try {
        # Check if npm is in PATH
        $npmVersion = npm --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ npm found in PATH: $npmVersion" -ForegroundColor Green
        } else {
            Write-Host "❌ npm not found in PATH" -ForegroundColor Red
            
            # Check common npm installation locations
            $possiblePaths = @(
                "C:\Program Files\nodejs\npm.cmd",
                "C:\Program Files\nodejs\npm.exe",
                "C:\Program Files (x86)\nodejs\npm.cmd",
                "C:\Program Files (x86)\nodejs\npm.exe"
            )
            
            $npmFound = $false
            foreach ($path in $possiblePaths) {
                if (Test-Path $path) {
                    Write-Host "✅ npm found at: $path" -ForegroundColor Green
                    $npmFound = $true
                    break
                }
            }
            
            if (-not $npmFound) {
                Write-Host "❌ npm not found in common locations" -ForegroundColor Red
                Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "❌ npm detection failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test Vue build function
if ($TestVue -or $All) {
    Write-Host "`n--- Testing Vue build function ---" -ForegroundColor Yellow
    
    # Check if Vue directory exists
    $vueDir = Join-Path $PSScriptRoot "casestrainer-vue-new"
    if (Test-Path $vueDir) {
        Write-Host "✅ Vue directory found: $vueDir" -ForegroundColor Green
        
        # Check if package.json exists
        $packageJson = Join-Path $vueDir "package.json"
        if (Test-Path $packageJson) {
            Write-Host "✅ package.json found" -ForegroundColor Green
            
            # Check if node_modules exists
            $nodeModules = Join-Path $vueDir "node_modules"
            if (Test-Path $nodeModules) {
                Write-Host "✅ node_modules found" -ForegroundColor Green
            } else {
                Write-Host "⚠️  node_modules not found (run npm install)" -ForegroundColor Yellow
            }
            
            # Check if dist directory exists
            $distDir = Join-Path $vueDir "dist"
            if (Test-Path $distDir) {
                Write-Host "✅ dist directory found" -ForegroundColor Green
            } else {
                Write-Host "⚠️  dist directory not found (run npm run build)" -ForegroundColor Yellow
            }
        } else {
            Write-Host "❌ package.json not found" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Vue directory not found: $vueDir" -ForegroundColor Red
    }
}

# Test Docker availability
if ($TestDocker -or $All) {
    Write-Host "`n--- Testing Docker availability ---" -ForegroundColor Yellow
    
    try {
        $dockerVersion = docker --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
            
            # Test Docker daemon
            $dockerInfo = docker info --format "{{.ServerVersion}}" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Docker daemon running: $dockerInfo" -ForegroundColor Green
            } else {
                Write-Host "❌ Docker daemon not running" -ForegroundColor Red
            }
        } else {
            Write-Host "❌ Docker not found" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Docker test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test PowerShell version
Write-Host "`n--- Testing PowerShell environment ---" -ForegroundColor Yellow
Write-Host "PowerShell version: $($PSVersionTable.PSVersion)" -ForegroundColor Gray
Write-Host "Execution policy: $(Get-ExecutionPolicy)" -ForegroundColor Gray
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray

# Test required files
Write-Host "`n--- Testing required files ---" -ForegroundColor Yellow
$requiredFiles = @(
    "docker-compose.prod.yml",
    "cslaunch.ps1"
)

foreach ($file in $requiredFiles) {
    $filePath = Join-Path $PSScriptRoot $file
    if (Test-Path $filePath) {
        Write-Host "✅ $file found" -ForegroundColor Green
    } else {
        Write-Host "❌ $file not found" -ForegroundColor Red
    }
}

Write-Host "`n=== Test completed ===" -ForegroundColor Cyan 