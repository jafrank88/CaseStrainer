# PowerShell script to update the D:\CaseStrainer Git repository
# This script should be run with administrator privileges

# Navigate to the repository
Set-Location -Path "D:\CaseStrainer"

# Stage all changes
Write-Host "Staging changes..."
git add .

# Commit changes
Write-Host "Committing changes..."
git commit -m "Update repository with latest changes from D drive deployment"

# Push changes to GitHub
Write-Host "Pushing changes to GitHub..."
git push origin main

Write-Host "Done! The D:\CaseStrainer repository is now your primary working directory and is synchronized with GitHub."
