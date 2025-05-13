$url = "https://github.com/ragel/ragel-windows/releases/download/v6.10/ragel.exe"
$output = "$env:USERPROFILE\tools\ragel.exe"

Write-Host "Downloading Ragel..."
Invoke-WebRequest -Uri $url -OutFile $output
Write-Host "Download complete. Ragel has been installed to $output" 