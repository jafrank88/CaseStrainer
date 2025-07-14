#Requires -Version 5.1

<#
.SYNOPSIS
    Adaptive Learning Pipeline for Citation Extraction
.DESCRIPTION
    Orchestrates the adaptive learning pipeline that learns from failed extractions
    to continuously improve the citation extraction tool.
.PARAMETER BriefsDir
    Directory containing brief PDFs to process
.PARAMETER OutputDir
    Output directory for results
.PARAMETER LearningDataDir
    Directory for learning data persistence
.PARAMETER SkipDownload
    Skip the download phase and use existing briefs
.PARAMETER MaxBriefs
    Maximum number of briefs to process
#>

param(
    [string]$BriefsDir = "wa_briefs",
    [string]$OutputDir = "adaptive_results",
    [string]$LearningDataDir = "learning_data",
    [switch]$SkipDownload,
    [int]$MaxBriefs = 50
)

# Color output function
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $colorMap = @{
        "Red" = "Red"
        "Green" = "Green"
        "Yellow" = "Yellow"
        "Cyan" = "Cyan"
        "White" = "White"
    }
    
    $selectedColor = $colorMap[$Color]
    Write-Host $Message -ForegroundColor $selectedColor
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

# Function to check and install required packages
function Test-RequiredPackages {
    Write-ColorOutput "Checking required packages..." "Yellow"
    
    $requiredPackages = @("beautifulsoup4", "requests", "lxml")
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
        [int]$MaxBriefs
    )

    Write-ColorOutput "`n=== STARTING SCRAPING PHASE ===" "Cyan"
    Write-ColorOutput "Output directory: $OutputDir" "White"
    Write-ColorOutput "Maximum briefs: $MaxBriefs" "White"

    if ($PSCmdlet.ShouldProcess("Scraping phase", "Start")) {
        $scrapingScript = Join-Path $PSScriptRoot "scrape_wa_briefs.py"

        if (-not (Test-Path $scrapingScript)) {
            Write-ColorOutput "Scraping script not found: $scrapingScript" "Red"
            return $false
        }

        try {
            Write-ColorOutput "Running scraping script..." "Yellow"
            python $scrapingScript --output-dir $OutputDir --max-briefs $MaxBriefs

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

# Function to run adaptive learning phase
function Start-AdaptiveLearningPhase {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$BriefsDir,
        [string]$OutputDir,
        [string]$LearningDataDir
    )

    Write-ColorOutput "`n=== STARTING ADAPTIVE LEARNING PHASE ===" "Cyan"
    Write-ColorOutput "Briefs directory: $BriefsDir" "White"
    Write-ColorOutput "Results directory: $OutputDir" "White"
    Write-ColorOutput "Learning data directory: $LearningDataDir" "White"

    if ($PSCmdlet.ShouldProcess("Adaptive learning phase", "Start")) {
        $adaptiveScript = Join-Path $PSScriptRoot "adaptive_learning_pipeline.py"

        if (-not (Test-Path $adaptiveScript)) {
            Write-ColorOutput "Adaptive learning script not found: $adaptiveScript" "Red"
            return $false
        }

        try {
            Write-ColorOutput "Running adaptive learning pipeline..." "Yellow"
            python $adaptiveScript --briefs-dir $BriefsDir --output-dir $OutputDir --learning-data-dir $LearningDataDir

            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "Adaptive learning completed successfully" "Green"
                return $true
            }
            else {
                Write-ColorOutput "Adaptive learning failed with exit code: $LASTEXITCODE" "Red"
                return $false
            }
        }
        catch {
            Write-ColorOutput "Error during adaptive learning: $($_.Exception.Message)" "Red"
            return $false
        }
    }
    return $true
}

# Function to run enhanced processing phase
function Start-EnhancedProcessingPhase {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$BriefsDir,
        [string]$OutputDir,
        [string]$LearningDataDir
    )

    Write-ColorOutput "`n=== STARTING ENHANCED PROCESSING PHASE ===" "Cyan"
    Write-ColorOutput "Briefs directory: $BriefsDir" "White"
    Write-ColorOutput "Results directory: $OutputDir" "White"
    Write-ColorOutput "Learning data directory: $LearningDataDir" "White"

    if ($PSCmdlet.ShouldProcess("Enhanced processing phase", "Start")) {
        $enhancedScript = Join-Path $PSScriptRoot "enhanced_adaptive_processor.py"

        if (-not (Test-Path $enhancedScript)) {
            Write-ColorOutput "Enhanced processor script not found: $enhancedScript" "Red"
            return $false
        }

        try {
            Write-ColorOutput "Running enhanced adaptive processor..." "Yellow"
            python $enhancedScript

            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "Enhanced processing completed successfully" "Green"
                return $true
            }
            else {
                Write-ColorOutput "Enhanced processing failed with exit code: $LASTEXITCODE" "Red"
                return $false
            }
        }
        catch {
            Write-ColorOutput "Error during enhanced processing: $($_.Exception.Message)" "Red"
            return $false
        }
    }
    return $true
}

# Function to display learning summary
function Show-LearningSummary {
    param(
        [string]$OutputDir,
        [string]$LearningDataDir
    )

    Write-ColorOutput "`n=== ADAPTIVE LEARNING SUMMARY ===" "Cyan"

    # Check for learning summary file
    $summaryFile = Join-Path $OutputDir "learning_summary.json"
    if (Test-Path $summaryFile) {
        try {
            $summary = Get-Content $summaryFile | ConvertFrom-Json
            
            Write-ColorOutput "Learning Progress:" "White"
            Write-ColorOutput "  Total briefs processed: $($summary.total_processed)" "White"
            Write-ColorOutput "  Total improvements made: $($summary.total_improvements)" "Green"
            Write-ColorOutput "  Learned patterns: $($summary.learned_patterns)" "White"
            Write-ColorOutput "  Failed extractions analyzed: $($summary.failed_extractions)" "Yellow"
            Write-ColorOutput "  Case name database entries: $($summary.case_name_database_size)" "White"
            
            # Show failure analysis if available
            if ($summary.failure_analysis) {
                $failureAnalysis = $summary.failure_analysis
                Write-ColorOutput "`nFailure Analysis:" "White"
                Write-ColorOutput "  Total failures: $($failureAnalysis.total_failures)" "Yellow"
                
                if ($failureAnalysis.error_types) {
                    Write-ColorOutput "  Error types:" "White"
                    foreach ($errorType in $failureAnalysis.error_types.PSObject.Properties) {
                        Write-ColorOutput "    $($errorType.Name): $($errorType.Value)" "White"
                    }
                }
                
                if ($failureAnalysis.suggested_improvements) {
                    Write-ColorOutput "  Suggested improvements:" "White"
                    foreach ($improvement in $failureAnalysis.suggested_improvements) {
                        $priorityColor = if ($improvement.priority -eq "high") { "Red" } else { "Yellow" }
                        Write-ColorOutput "    - $($improvement.description) (Priority: $($improvement.priority))" $priorityColor
                    }
                }
            }
        }
        catch {
            Write-ColorOutput "Error reading learning summary: $($_.Exception.Message)" "Red"
        }
    }
    else {
        Write-ColorOutput "Learning summary file not found: $summaryFile" "Yellow"
    }

    # Check for learning data files
    $learningDataPath = Join-Path $PSScriptRoot $LearningDataDir
    if (Test-Path $learningDataPath) {
        Write-ColorOutput "`nLearning Data Files:" "White"
        $learningFiles = Get-ChildItem $learningDataPath -File
        foreach ($file in $learningFiles) {
            $size = [math]::Round($file.Length / 1KB, 2)
            Write-ColorOutput "  $($file.Name): $size KB" "White"
        }
    }
}

# Function to display results summary
function Show-ResultsSummary {
    param(
        [string]$OutputDir
    )

    Write-ColorOutput "`n=== RESULTS SUMMARY ===" "Cyan"

    $resultsFile = Join-Path $OutputDir "adaptive_processing_results.json"
    if (Test-Path $resultsFile) {
        try {
            $results = Get-Content $resultsFile | ConvertFrom-Json
            
            $totalBriefs = $results.Count
            $totalCitations = ($results | Measure-Object -Property citations_count -Sum).Sum
            $avgCitations = if ($totalBriefs -gt 0) { [math]::Round($totalCitations / $totalBriefs, 1) } else { 0 }
            
            Write-ColorOutput "Processing Results:" "White"
            Write-ColorOutput "  Total briefs processed: $totalBriefs" "White"
            Write-ColorOutput "  Total citations extracted: $totalCitations" "White"
            Write-ColorOutput "  Average citations per brief: $avgCitations" "White"
            
            # Show learning improvements
            $totalImprovements = ($results | Measure-Object -Property 'learning_info.improvements' -Sum).Sum
            Write-ColorOutput "  Total learning improvements: $totalImprovements" "Green"
            
        }
        catch {
            Write-ColorOutput "Error reading results: $($_.Exception.Message)" "Red"
        }
    }
    else {
        Write-ColorOutput "Results file not found: $resultsFile" "Yellow"
    }
}

# Main execution
try {
    Write-ColorOutput "Adaptive Learning Pipeline for Citation Extraction" "Cyan"
    Write-ColorOutput "=================================================" "Cyan"

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
    $briefsDir = $BriefsDir
    $resultsDir = $OutputDir
    $learningDataDir = $LearningDataDir

    if (-not $SkipDownload) {
        New-Item -ItemType Directory -Path $briefsDir -Force | Out-Null
        Write-ColorOutput "Created briefs directory: $briefsDir" "Green"
    }

    New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null
    Write-ColorOutput "Created results directory: $resultsDir" "Green"

    New-Item -ItemType Directory -Path $learningDataDir -Force | Out-Null
    Write-ColorOutput "Created learning data directory: $learningDataDir" "Green"

    # Run scraping phase
    $scrapingSuccess = $true
    if (-not $SkipDownload) {
        $scrapingSuccess = Start-ScrapingPhase -OutputDir $briefsDir -MaxBriefs $MaxBriefs
    }
    else {
        Write-ColorOutput "`nSkipping download phase as requested" "Yellow"
    }

    if (-not $scrapingSuccess) {
        Write-ColorOutput "Scraping phase failed. Stopping pipeline." "Red"
        exit 1
    }

    # Run adaptive learning phase
    $learningSuccess = Start-AdaptiveLearningPhase -BriefsDir $briefsDir -OutputDir $resultsDir -LearningDataDir $learningDataDir

    if (-not $learningSuccess) {
        Write-ColorOutput "Adaptive learning phase failed. Stopping pipeline." "Red"
        exit 1
    }

    # Run enhanced processing phase
    $enhancedSuccess = Start-EnhancedProcessingPhase -BriefsDir $briefsDir -OutputDir $resultsDir -LearningDataDir $learningDataDir

    if (-not $enhancedSuccess) {
        Write-ColorOutput "Enhanced processing phase failed." "Red"
    }

    # Display summaries
    Show-LearningSummary -OutputDir $resultsDir -LearningDataDir $learningDataDir
    Show-ResultsSummary -OutputDir $resultsDir

    Write-ColorOutput "`n=== PIPELINE COMPLETION ===" "Cyan"
    Write-ColorOutput "Adaptive learning pipeline completed!" "Green"
    Write-ColorOutput "Briefs directory: $briefsDir" "White"
    Write-ColorOutput "Results directory: $resultsDir" "White"
    Write-ColorOutput "Learning data directory: $learningDataDir" "White"
    Write-ColorOutput "`nThe system has learned from failed extractions and improved its patterns." "Green"
    Write-ColorOutput "Run the pipeline again to see continued improvements!" "Cyan"

}
catch {
    Write-ColorOutput "Pipeline failed with error: $($_.Exception.Message)" "Red"
    exit 1
} 