# See what Python files exist
Write-Host "Python files in current directory:"
Get-ChildItem *.py | ForEach-Object { Write-Host "  $($_.Name)" }

Write-Host "`nAll directories:"
Get-ChildItem -Directory | ForEach-Object { Write-Host "  $($_.Name)" }

Write-Host "`nLooking for Flask files in subdirectories:"
Get-ChildItem -Recurse -Filter "*.py" | Where-Object { $_.Name -match "(app|main|server|run)" } | ForEach-Object { Write-Host "  $($_.FullName)" }