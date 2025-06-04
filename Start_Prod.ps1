# Create the script directory if it doesn't exist
if (-not (Test-Path -Path "C:\Scripts")) {
    New-Item -ItemType Directory -Path "C:\Scripts" -Force
}

# Create the script file
$scriptPath = "C:\Scripts\CaseStrainer-Deploy.ps1"
New-Item -ItemType File -Path $scriptPath -Force

# Open the file in Notepad
notepad $scriptPath