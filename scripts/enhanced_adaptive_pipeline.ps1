# Enhanced Adaptive Learning Pipeline for CaseStrainer
# PowerShell script for orchestrating enhanced case name extraction with adaptive learning

param(
    [string]$BriefsDir = "wa_briefs",
    [string]$OutputDir = "enhanced_results",
    [string]$LearningDataDir = "learning_data",
    [int]$MaxBriefs = 10,
    [bool]$MonitorPerformance = $true
)

# Function to write colored output
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
        "Magenta" = "Magenta"
    }

    $selectedColor = $colorMap[$Color]
    Write-Host $Message -ForegroundColor $selectedColor
}

# Function to check if Python is available
function Test-PythonAvailable {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput -Message "Python found: $pythonVersion" -Color "Green"
            return $true
        }
    }
    catch {
        Write-ColorOutput -Message "Python not found in PATH" -Color "Red"
        return $false
    }
    return $false
}

# Function to check and install required packages
function Test-RequiredPackages {
    $requiredPackages = @("psutil", "pathlib", "dataclasses", "fuzzywuzzy")

    foreach ($package in $requiredPackages) {
        try {
            python -c "import $package" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput -Message "✓ $package is available" -Color "Green"
            } else {
                Write-ColorOutput -Message "Installing $package..." -Color "Yellow"
                pip install $package
                if ($LASTEXITCODE -eq 0) {
                    Write-ColorOutput -Message "✓ $package installed successfully" -Color "Green"
                } else {
                    Write-ColorOutput -Message "✗ Failed to install $package" -Color "Red"
                    return $false
                }
            }
        }
        catch {
            Write-ColorOutput -Message "✗ Error checking/installing $package" -Color "Red"
            return $false
        }
    }
    return $true
}

# Function to create directories
function Initialize-Directories {
    param(
        [string]$BriefsDir,
        [string]$OutputDir,
        [string]$LearningDataDir
    )

    $directories = @($BriefsDir, $OutputDir, $LearningDataDir)

    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-ColorOutput -Message "Created directory: $dir" -Color "Green"
        } else {
            Write-ColorOutput -Message "Directory exists: $dir" -Color "Cyan"
        }
    }
}

# Function to run enhanced adaptive learning
function Start-EnhancedAdaptiveLearning {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$BriefsDir,
        [string]$OutputDir,
        [string]$LearningDataDir,
        [int]$MaxBriefs,
        [bool]$MonitorPerformance
    )

    Write-ColorOutput -Message "`n🚀 Starting Enhanced Adaptive Learning Pipeline" -Color "Magenta"
    Write-ColorOutput -Message "=" * 60 -Color "Cyan"

    # Create the enhanced processing script
    $scriptContent = @"
#!/usr/bin/env python3
"""
Enhanced Adaptive Learning Pipeline with Performance Monitoring
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def main():
    try:
        from enhanced_adaptive_processor import EnhancedAdaptiveProcessor
    except ImportError:
        # Try importing from src directory
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        try:
            from enhanced_adaptive_processor import EnhancedAdaptiveProcessor
        except ImportError:
            print("Error: enhanced_adaptive_processor not available")
            return False
    
    try:
        from performance_monitor import PerformanceMonitor
    except ImportError:
        print("Warning: performance_monitor not available, monitoring disabled")
        PerformanceMonitor = None
    
    try:
        from document_processing_unified import extract_text_from_file
    except ImportError:
        print("Error: document_processing_unified not available")
        return False

    # Initialize components
    processor = EnhancedAdaptiveProcessor("$LearningDataDir")
    monitor = PerformanceMonitor("$OutputDir/performance_data") if $MonitorPerformance and PerformanceMonitor else None

    # Get brief files
    briefs_dir = Path("$BriefsDir")
    pdf_files = list(briefs_dir.glob("*.pdf"))[:$MaxBriefs]

    if not pdf_files:
        print("No PDF files found to process")
        return

    print(f"Processing {len(pdf_files)} PDF files with enhanced adaptive learning...")

    results = []
    total_start_time = time.time()

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\\n📄 Processing {i}/{len(pdf_files)}: {pdf_path.name}")

        # Start monitoring if enabled
        operation_id = f"brief_{i}"
        if monitor:
            monitor.start_operation(operation_id, pdf_path.name, pdf_path.stat().st_size)

        try:
            # Extract text
            text = extract_text_from_file(str(pdf_path))
            if not text or len(text.strip()) < 100:
                print(f"  ⚠️  Skipped: Text too short")
                if monitor:
                    monitor.end_operation(operation_id, error="Text too short")
                continue

            # Process with enhanced adaptive processor
            start_time = time.time()
            citations, learning_info = processor.process_text_optimized(text, pdf_path.name)
            processing_time = time.time() - start_time

            # Update monitoring
            if monitor:
                monitor.end_operation(
                    operation_id,
                    text_length=len(text),
                    citations_found=len(citations),
                    clusters_created=len(learning_info.get('clusters', [])),
                    cache_hits=learning_info.get('performance_metrics', {}).get('cache_hits', 0),
                    cache_misses=learning_info.get('performance_metrics', {}).get('cache_misses', 0)
                )

            # Store results
            result = {
                'filename': pdf_path.name,
                'citations_count': len(citations),
                'processing_time': processing_time,
                'text_length': len(text),
                'learning_info': learning_info,
                'timestamp': time.time()
            }
            results.append(result)

            print(f"  ✅ Extracted {len(citations)} citations in {processing_time:.2f}s")
            print(f"  🧠 Learning: {learning_info.get('learning_result', {}).get('new_patterns_learned', 0)} new patterns")

            # Performance warnings
            if processing_time > 30:
                print(f"  ⚠️  Slow processing: {processing_time:.2f}s")

        except Exception as e:
            print(f"  ❌ Error processing {pdf_path.name}: {e}")
            if monitor:
                monitor.end_operation(operation_id, error=str(e))

    # Calculate summary
    total_time = time.time() - total_start_time
    total_citations = sum(r['citations_count'] for r in results)
    avg_time = sum(r['processing_time'] for r in results) / len(results) if results else 0

    print(f"\\n📊 Processing Summary:")
    print(f"  Total files: {len(results)}")
    print(f"  Total citations: {total_citations}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Average time per file: {avg_time:.2f}s")

    # Save results
    results_file = Path("$OutputDir") / "enhanced_processing_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    # Save performance summary if monitoring enabled
    if monitor:
        performance_summary = processor.get_performance_summary()
        summary_file = Path("$OutputDir") / "performance_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(performance_summary, f, indent=2, default=str)

        monitor.print_summary()

    print(f"\\n✅ Enhanced adaptive learning completed!")
    print(f"Results saved to: $OutputDir")
    return True

if __name__ == "__main__":
    main()
"@

    # Write the script to a temporary file
    $scriptPath = "enhanced_adaptive_runner.py"
    $scriptContent | Out-File -FilePath $scriptPath -Encoding UTF8

    try {
        # Run the enhanced adaptive learning
        Write-ColorOutput -Message "Running enhanced adaptive learning..." -Color "Yellow"
        python $scriptPath

        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput -Message "✅ Enhanced adaptive learning completed successfully!" -Color "Green"
            return $true
        } else {
            Write-ColorOutput -Message "❌ Enhanced adaptive learning failed!" -Color "Red"
            return $false
        }
    }
    finally {
        # Clean up temporary script
        if (Test-Path $scriptPath) {
            Remove-Item $scriptPath
        }
    }
}

# Function to display results summary
function Show-ResultsSummary {
    param([string]$OutputDir)

    $resultsFile = Join-Path $OutputDir "enhanced_processing_results.json"
    $performanceFile = Join-Path $OutputDir "performance_summary.json"

    Write-ColorOutput -Message "`n📊 Results Summary" -Color "Magenta"
    Write-ColorOutput -Message "=" * 40 -Color "Cyan"

    if (Test-Path $resultsFile) {
        $results = Get-Content $resultsFile | ConvertFrom-Json
        Write-ColorOutput -Message "Files Processed: $($results.Count)" -Color "Green"

        if ($results.Count -gt 0) {
            $totalCitations = ($results | Measure-Object -Property citations_count -Sum).Sum
            $avgTime = ($results | Measure-Object -Property processing_time -Average).Average
            Write-ColorOutput -Message "Total Citations: $totalCitations" -Color "Green"
            Write-ColorOutput -Message "Average Processing Time: $([math]::Round($avgTime, 2))s" -Color "Green"
        }
    }

    if (Test-Path $performanceFile) {
        $performance = Get-Content $performanceFile | ConvertFrom-Json
        Write-ColorOutput -Message "`nPerformance Metrics:" -Color "Yellow"
        Write-ColorOutput -Message "Cache Hit Rate: $([math]::Round($performance.cache_performance.hit_rate * 100, 1))%" -Color "Cyan"
        Write-ColorOutput -Message "Average Time per Citation: $([math]::Round($performance.processing_performance.avg_time_per_citation, 3))s" -Color "Cyan"
        Write-ColorOutput -Message "Early Terminations: $($performance.processing_performance.early_terminations)" -Color "Cyan"
    }
}

# Main execution
try {
    Write-ColorOutput -Message "Enhanced Adaptive Learning Pipeline" -Color "Magenta"
    Write-ColorOutput -Message "Performance-Optimized Brief Processing" -Color "Cyan"
    Write-ColorOutput -Message "=" * 60 -Color "Cyan"

    # Check Python availability
    if (-not (Test-PythonAvailable)) {
        Write-ColorOutput -Message "Python is required but not found. Please install Python and try again." -Color "Red"
        exit 1
    }

    # Check and install required packages
    if (-not (Test-RequiredPackages)) {
        Write-ColorOutput -Message "Failed to install required packages." -Color "Red"
        exit 1
    }

    # Initialize directories
    Initialize-Directories -BriefsDir $BriefsDir -OutputDir $OutputDir -LearningDataDir $LearningDataDir

    # Run enhanced adaptive learning
    $success = Start-EnhancedAdaptiveLearning -BriefsDir $BriefsDir -OutputDir $OutputDir -LearningDataDir $LearningDataDir -MaxBriefs $MaxBriefs -MonitorPerformance $MonitorPerformance

    if ($success) {
        # Display results summary
        Show-ResultsSummary -OutputDir $OutputDir

        Write-ColorOutput -Message "`n🎉 Enhanced adaptive learning pipeline completed successfully!" -Color "Green"
        Write-ColorOutput -Message "Check the results in: $OutputDir" -Color "Cyan"
    } else {
        Write-ColorOutput -Message "`n❌ Enhanced adaptive learning pipeline failed!" -Color "Red"
        exit 1
    }
}
catch {
    Write-ColorOutput -Message "`n❌ Error in enhanced adaptive learning pipeline: $($_.Exception.Message)" -Color "Red"
    Write-ColorOutput -Message "Stack trace: $($_.ScriptStackTrace)" -Color "Red"
    exit 1
}
