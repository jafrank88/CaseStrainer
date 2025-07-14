#Requires -Version 5.1

<#
.SYNOPSIS
    Washington State Courts Briefs Pipeline
.DESCRIPTION
    Orchestrates the scraping and processing of WA briefs for citation extraction testing.
    Downloads substantial briefs and processes them through the citation extraction pipeline.
.PARAMETER OutputDir
    Directory to store downloaded briefs and results
.PARAMETER MinPages
    Minimum pages required for a brief to be considered substantial
.PARAMETER MaxBriefs
    Maximum number of briefs to download
.PARAMETER SkipDownload
    Skip the download phase and process existing briefs
.PARAMETER SkipProcessing
    Skip the processing phase and only download briefs
.PARAMETER SkipYearValidation
    Skip the year extraction validation phase
.EXAMPLE
    .\wa_briefs_pipeline.ps1 -OutputDir "wa_briefs_test" -MinPages 15 -MaxBriefs 25
.EXAMPLE
    .\wa_briefs_pipeline.ps1 -SkipDownload -OutputDir "existing_briefs"
#>

param(
    [string]$OutputDir = "wa_briefs",
    [int]$MinPages = 10,
    [int]$MaxBriefs = 50,
    [switch]$SkipDownload,
    [switch]$SkipProcessing,
    [switch]$SkipYearValidation
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to check if Python is available
function Test-PythonAvailable {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "Python found: $pythonVersion" "Green"
            return $true
        }
    }
    catch {
        Write-ColorOutput "Python not found in PATH" "Red"
        return $false
    }
    return $false
}

# Function to check if required Python packages are installed
function Test-RequiredPackages {
    $requiredPackages = @("requests", "beautifulsoup4", "pathlib")
    $missingPackages = @()

    foreach ($package in $requiredPackages) {
        try {
            python -c "import $package" 2>$null
            if ($LASTEXITCODE -ne 0) {
                $missingPackages += $package
            }
        }
        catch {
            $missingPackages += $package
        }
    }

    if ($missingPackages.Count -gt 0) {
        Write-ColorOutput "Missing required packages: $($missingPackages -join ', ')" "Yellow"
        Write-ColorOutput "Installing missing packages..." "Yellow"

        foreach ($package in $missingPackages) {
            Write-ColorOutput "Installing $package..." "Yellow"
            pip install $package
            if ($LASTEXITCODE -ne 0) {
                Write-ColorOutput "Failed to install $package" "Red"
                return $false
            }
        }
    }

    Write-ColorOutput "All required packages are available" "Green"
    return $true
}

# Function to run scraping phase
function Start-ScrapingPhase {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$OutputDir,
        [int]$MinPages,
        [int]$MaxBriefs
    )

    Write-ColorOutput "`n=== STARTING SCRAPING PHASE ===" "Cyan"
    Write-ColorOutput "Output directory: $OutputDir" "White"
    Write-ColorOutput "Minimum pages: $MinPages" "White"
    Write-ColorOutput "Maximum briefs: $MaxBriefs" "White"

    if ($PSCmdlet.ShouldProcess("Scraping phase", "Start")) {
        $scrapingScript = Join-Path $PSScriptRoot "scrape_wa_briefs.py"

        if (-not (Test-Path $scrapingScript)) {
            Write-ColorOutput "Scraping script not found: $scrapingScript" "Red"
            return $false
        }

        try {
            Write-ColorOutput "Running scraping script..." "Yellow"
            python $scrapingScript --output-dir $OutputDir --min-pages $MinPages --max-briefs $MaxBriefs

            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "Scraping completed successfully" "Green"
                return $true
            }
            else {
                Write-ColorOutput "Scraping failed with exit code: $LASTEXITCODE" "Red"
                return $false
            }
        }
        catch {
            Write-ColorOutput "Error during scraping: $($_.Exception.Message)" "Red"
            return $false
        }
    }
    return $true
}

# Function to run processing phase
function Start-ProcessingPhase {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$BriefsDir,
        [string]$OutputDir
    )

    Write-ColorOutput "`n=== STARTING PROCESSING PHASE ===" "Cyan"
    Write-ColorOutput "Briefs directory: $BriefsDir" "White"
    Write-ColorOutput "Results directory: $OutputDir" "White"

    if ($PSCmdlet.ShouldProcess("Processing phase", "Start")) {
        $processingScript = Join-Path $PSScriptRoot "process_wa_briefs.py"

        if (-not (Test-Path $processingScript)) {
            Write-ColorOutput "Processing script not found: $processingScript" "Red"
            return $false
        }

        try {
            Write-ColorOutput "Running processing script..." "Yellow"
            python $processingScript --briefs-dir $BriefsDir --output-dir $OutputDir

            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "Processing completed successfully" "Green"
                return $true
            }
            else {
                Write-ColorOutput "Processing failed with exit code: $LASTEXITCODE" "Red"
                return $false
            }
        }
        catch {
            Write-ColorOutput "Error during processing: $($_.Exception.Message)" "Red"
            return $false
        }
    }
    return $true
}

# Function to run year extraction validation
function Start-YearValidation {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$OutputDir
    )

    Write-ColorOutput "`n=== STARTING YEAR EXTRACTION VALIDATION ===" "Cyan"

    if ($PSCmdlet.ShouldProcess("Year validation", "Start")) {
        $validationScript = Join-Path $PSScriptRoot "validate_year_extraction.py"

        if (-not (Test-Path $validationScript)) {
            Write-ColorOutput "Year validation script not found: $validationScript" "Red"
            return $false
        }

        try {
            Write-ColorOutput "Running year extraction validation..." "Yellow"
            $validationOutput = Join-Path $OutputDir "year_extraction_validation.json"
            python $validationScript --output $validationOutput --detailed

            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "Year validation completed successfully" "Green"
                return $true
            }
            else {
                Write-ColorOutput "Year validation failed with exit code: $LASTEXITCODE" "Red"
                return $false
            }
        }
        catch {
            Write-ColorOutput "Error during year validation: $($_.Exception.Message)" "Red"
            return $false
        }
    }
    return $true
}

# Function to display results summary
function Show-ResultsSummary {
    param(
        [string]$ResultsDir
    )

    Write-ColorOutput "`n=== RESULTS SUMMARY ===" "Cyan"

    $summaryFile = Join-Path $ResultsDir "processing_summary.json"
    if (Test-Path $summaryFile) {
        try {
            $summary = Get-Content $summaryFile | ConvertFrom-Json
            $stats = $summary.processing_summary

            Write-ColorOutput "Total files processed: $($stats.total_files)" "White"
            Write-ColorOutput "Successfully processed: $($stats.processed_successfully)" "Green"
            Write-ColorOutput "Failed: $($stats.failed)" "Red"
            Write-ColorOutput "Total citations extracted: $($stats.total_citations)" "White"
            Write-ColorOutput "Total clusters created: $($stats.total_clusters)" "White"
            Write-ColorOutput "Total citations with years: $($stats.total_citations_with_years)" "White"
            Write-ColorOutput "Year extraction rate: $([math]::Round($stats.year_extraction_rate * 100, 1))%" "White"
            Write-ColorOutput "Average citations per brief: $([math]::Round($stats.average_citations_per_brief, 1))" "White"
            Write-ColorOutput "Average clusters per brief: $([math]::Round($stats.average_clusters_per_brief, 1))" "White"
        }
        catch {
            Write-ColorOutput "Error reading summary file: $($_.Exception.Message)" "Red"
        }
    }
    else {
        Write-ColorOutput "Summary file not found: $summaryFile" "Yellow"
    }

    # Show analysis report if available
    $analysisFile = Join-Path $ResultsDir "analysis_report.txt"
    if (Test-Path $analysisFile) {
        Write-ColorOutput "`nAnalysis report available: $analysisFile" "Green"
    }

    # Show year validation results if available
    $yearValidationFile = Join-Path $ResultsDir "year_extraction_validation.json"
    if (Test-Path $yearValidationFile) {
        Write-ColorOutput "Year validation results available: $yearValidationFile" "Green"
    }
}

# Main execution
try {
    Write-ColorOutput "Washington State Courts Briefs Pipeline" "Cyan"
    Write-ColorOutput "=====================================" "Cyan"

    # Check prerequisites
    Write-ColorOutput "`nChecking prerequisites..." "Yellow"

    if (-not (Test-PythonAvailable)) {
        Write-ColorOutput "Python is required but not found. Please install Python and add it to PATH." "Red"
        exit 1
    }

    if (-not (Test-RequiredPackages)) {
        Write-ColorOutput "Failed to install required packages." "Red"
        exit 1
    }

    # Create output directories
    $briefsDir = $OutputDir
    $resultsDir = "${OutputDir}_results"

    if (-not $SkipDownload) {
        New-Item -ItemType Directory -Path $briefsDir -Force | Out-Null
        Write-ColorOutput "Created briefs directory: $briefsDir" "Green"
    }

    if (-not $SkipProcessing) {
        New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null
        Write-ColorOutput "Created results directory: $resultsDir" "Green"
    }

    # Run scraping phase
    $scrapingSuccess = $true
    if (-not $SkipDownload) {
        $scrapingSuccess = Start-ScrapingPhase -OutputDir $briefsDir -MinPages $MinPages -MaxBriefs $MaxBriefs
    }
    else {
        Write-ColorOutput "`nSkipping download phase as requested" "Yellow"
    }

    # Run processing phase
    $processingSuccess = $true
    if (-not $SkipProcessing) {
        if ($scrapingSuccess -or $SkipDownload) {
            $processingSuccess = Start-ProcessingPhase -BriefsDir $briefsDir -OutputDir $resultsDir
        }
        else {
            Write-ColorOutput "Skipping processing due to scraping failure" "Red"
            $processingSuccess = $false
        }
    }
    else {
        Write-ColorOutput "`nSkipping processing phase as requested" "Yellow"
    }

    # Run year validation phase
    $yearValidationSuccess = $true
    if (-not $SkipYearValidation -and $processingSuccess) {
        $yearValidationSuccess = Start-YearValidation -OutputDir $resultsDir
    }
    else {
        if ($SkipYearValidation) {
            Write-ColorOutput "`nSkipping year validation phase as requested" "Yellow"
        }
        else {
            Write-ColorOutput "`nSkipping year validation due to processing failure" "Red"
        }
    }

    # Show results
    if ($processingSuccess -and -not $SkipProcessing) {
        Show-ResultsSummary -ResultsDir $resultsDir
    }

    # Final status
    Write-ColorOutput "`n=== PIPELINE COMPLETION ===" "Cyan"
    if ($scrapingSuccess -and $processingSuccess -and $yearValidationSuccess) {
        Write-ColorOutput "Pipeline completed successfully!" "Green"
        Write-ColorOutput "Briefs directory: $briefsDir" "White"
        Write-ColorOutput "Results directory: $resultsDir" "White"
    }
    else {
        Write-ColorOutput "Pipeline completed with errors" "Red"
        if (-not $scrapingSuccess) {
            Write-ColorOutput "- Scraping phase failed" "Red"
        }
        if (-not $processingSuccess) {
            Write-ColorOutput "- Processing phase failed" "Red"
        }
        if (-not $yearValidationSuccess -and -not $SkipYearValidation) {
            Write-ColorOutput "- Year validation phase failed" "Red"
        }
        exit 1
    }
}
catch {
    Write-ColorOutput "Pipeline failed with error: $($_.Exception.Message)" "Red"
    exit 1
}
