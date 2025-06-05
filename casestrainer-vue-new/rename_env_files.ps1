# Rename environment files (run as Administrator)
$files = @(
    @{ From = "_env"; To = ".env" },
    @{ From = "_env.development"; To = ".env.development" },
    @{ From = "_env.production"; To = ".env.production" },
    @{ From = "_env.example"; To = ".env.example" }
)

foreach ($file in $files) {
    $from = $file.From
    $to = $file.To
    
    if (Test-Path $from) {
        if (Test-Path $to) {
            Write-Host "Backing up existing $to to ${to}.bak" -ForegroundColor Yellow
            Move-Item -Path $to -Destination "${to}.bak" -Force
        }
        
        Write-Host "Renaming $from to $to" -ForegroundColor Green
        Move-Item -Path $from -Destination $to -Force
    } else {
        Write-Host "Warning: Source file $from not found" -ForegroundColor Yellow
    }
}

Write-Host "`nEnvironment files have been renamed successfully!" -ForegroundColor Green
Write-Host "You can now start your development server." -ForegroundColor Green

# Remove this script if it exists
if (Test-Path $PSCommandPath) {
    Remove-Item -Path $PSCommandPath
}
