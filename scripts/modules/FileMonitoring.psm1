# FileMonitoring.psm1 - File change detection and hash monitoring

$script:CacheDir = Join-Path $PSScriptRoot "..\..\..\.cslaunch_cache"

function Initialize-FileMonitoring {
    <#
    .SYNOPSIS
    Initialize file monitoring system
    
    .DESCRIPTION
    Creates cache directory and initializes hash storage
    
    .OUTPUTS
    Boolean - $true if successful
    #>
    
    [CmdletBinding()]
    param()
    
    try {
        if (-not (Test-Path $script:CacheDir)) {
            New-Item -ItemType Directory -Path $script:CacheDir -Force | Out-Null
            Write-Verbose "Created cache directory: $script:CacheDir"
        }
        return $true
    } catch {
        Write-Warning "Failed to initialize file monitoring: $($_.Exception.Message)"
        return $false
    }
}

function Get-StoredHash {
    <#
    .SYNOPSIS
    Get stored hash for a file
    
    .PARAMETER FilePath
    Path to the file
    
    .OUTPUTS
    String - Stored hash or $null if not found
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$FilePath
    )
    
    try {
        $hashFile = Join-Path $script:CacheDir "$($FilePath -replace '[\\\/:]', '_').hash"
        if (Test-Path $hashFile) {
            return Get-Content $hashFile -Raw
        }
        return $null
    } catch {
        Write-Verbose "Error getting stored hash: $($_.Exception.Message)"
        return $null
    }
}

function Set-StoredHash {
    <#
    .SYNOPSIS
    Store hash for a file
    
    .PARAMETER FilePath
    Path to the file
    
    .PARAMETER Hash
    Hash value to store
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$FilePath,
        
        [Parameter(Mandatory)]
        [string]$Hash
    )
    
    try {
        Initialize-FileMonitoring | Out-Null
        $hashFile = Join-Path $script:CacheDir "$($FilePath -replace '[\\\/:]', '_').hash"
        Set-Content -Path $hashFile -Value $Hash -Force
        Write-Verbose "Stored hash for: $FilePath"
    } catch {
        Write-Verbose "Error storing hash: $($_.Exception.Message)"
    }
}

function Test-FileChanged {
    <#
    .SYNOPSIS
    Check if file has changed since last check
    
    .PARAMETER FilePath
    Path to the file to check
    
    .OUTPUTS
    Boolean - $true if file changed, $false otherwise
    #>
    
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$FilePath
    )
    
    try {
        if (-not (Test-Path $FilePath)) {
            Write-Verbose "File not found: $FilePath"
            return $false
        }
        
        $currentHash = (Get-FileHash $FilePath -Algorithm MD5).Hash
        $storedHash = Get-StoredHash $FilePath
        
        if (-not $storedHash) {
            # First time seeing this file - store hash and return false
            Set-StoredHash $FilePath $currentHash
            Write-Verbose "First time monitoring: $FilePath"
            return $false
        }
        
        if ($currentHash -ne $storedHash) {
            # File changed - update hash and return true
            Set-StoredHash $FilePath $currentHash
            Write-Verbose "File changed: $FilePath"
            return $true
        }
        
        Write-Verbose "File unchanged: $FilePath"
        return $false
        
    } catch {
        Write-Warning "Error checking file: $($_.Exception.Message)"
        return $false
    }
}

function Get-ChangedFiles {
    <#
    .SYNOPSIS
    Get list of changed files categorized by type
    
    .DESCRIPTION
    Checks predefined list of important files and categorizes changes
    
    .OUTPUTS
    Hashtable with categories: Frontend, Backend, Dependencies, All
    #>
    
    [CmdletBinding()]
    param()
    
    $rootDir = Join-Path $PSScriptRoot "..\..\"
    
    # Define file categories
    # NOTE: Only include files that actually require a rebuild when changed
    # Config files (package.json) should NOT trigger automatic rebuilds
    $frontendFiles = @(
        "casestrainer-vue-new\src\views\HomeView.vue",
        "casestrainer-vue-new\src\stores\progressStore.js",
        "casestrainer-vue-new\src\views\EnhancedValidator.vue",
        "casestrainer-vue-new\src\components\CitationList.vue",
        "casestrainer-vue-new\src\App.vue",
        "casestrainer-vue-new\src\main.js"
        # Deliberately excluding package.json - config changes don't require rebuild
    )
    
    $backendFiles = @(
        "src\unified_citation_processor_v2.py",
        "src\unified_case_name_extractor_v2.py",
        "src\unified_citation_clustering.py",
        "src\vue_api_endpoints_updated.py",
        "src\progress_manager.py"
    )
    
    $dependencyFiles = @(
        "requirements.txt",
        "package.json",
        "docker-compose.prod.yml",
        "Dockerfile"
    )
    
    $results = @{
        Frontend = @()
        Backend = @()
        Dependencies = @()
        All = @()
    }
    
    # Check frontend files
    foreach ($file in $frontendFiles) {
        $fullPath = Join-Path $rootDir $file
        if (Test-FileChanged $fullPath) {
            $results.Frontend += $file
            $results.All += $file
        }
    }
    
    # Check backend files
    foreach ($file in $backendFiles) {
        $fullPath = Join-Path $rootDir $file
        if (Test-FileChanged $fullPath) {
            $results.Backend += $file
            $results.All += $file
        }
    }
    
    # Check dependency files
    foreach ($file in $dependencyFiles) {
        $fullPath = Join-Path $rootDir $file
        if (Test-FileChanged $fullPath) {
            $results.Dependencies += $file
            $results.All += $file
        }
    }
    
    return $results
}

function Clear-FileMonitoringCache {
    <#
    .SYNOPSIS
    Clear all stored file hashes
    
    .DESCRIPTION
    Removes the cache directory and all stored hashes
    Useful for resetting monitoring state
    #>
    
    [CmdletBinding()]
    param()
    
    try {
        if (Test-Path $script:CacheDir) {
            Remove-Item $script:CacheDir -Recurse -Force
            Write-Host "File monitoring cache cleared" -ForegroundColor Green
        } else {
            Write-Host "No cache to clear" -ForegroundColor Gray
        }
    } catch {
        Write-Warning "Failed to clear cache: $($_.Exception.Message)"
    }
}

# Export functions
Export-ModuleMember -Function @(
    'Initialize-FileMonitoring',
    'Get-StoredHash',
    'Set-StoredHash',
    'Test-FileChanged',
    'Get-ChangedFiles',
    'Clear-FileMonitoringCache'
)
