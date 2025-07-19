# Fix trailing whitespace in enhanced_adaptive_pipeline.ps1
$content = Get-Content 'scripts/enhanced_adaptive_pipeline.ps1'
$fixedContent = $content | ForEach-Object { $_.TrimEnd() }
$fixedContent | Set-Content 'scripts/enhanced_adaptive_pipeline.ps1' -Encoding UTF8
Write-Host "Trailing whitespace removed from enhanced_adaptive_pipeline.ps1" 