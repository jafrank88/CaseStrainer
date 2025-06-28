# Deploy Vue Build Files to Static Directories
# This script copies the built Vue files to the correct static directories for serving

Write-Host "Building Vue application..." -ForegroundColor Green
cd casestrainer-vue-new
npm run build
cd ..

Write-Host "Copying built files to static directories..." -ForegroundColor Green

# Create directories if they don't exist
New-Item -ItemType Directory -Force -Path "static/vue" | Out-Null
New-Item -ItemType Directory -Force -Path "static/css" | Out-Null
New-Item -ItemType Directory -Force -Path "static/js" | Out-Null

# Copy main HTML file
Copy-Item "casestrainer-vue-new/dist/index.html" "static/vue/index.html" -Force

# Copy CSS files
Copy-Item "casestrainer-vue-new/dist/css/*.css" "static/css/" -Force

# Copy JS files
Copy-Item "casestrainer-vue-new/dist/js/*.js" "static/js/" -Force

Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "Files are now available at:" -ForegroundColor Yellow
Write-Host "  - /casestrainer/vue/index.html" -ForegroundColor Cyan
Write-Host "  - /casestrainer/css/" -ForegroundColor Cyan
Write-Host "  - /casestrainer/js/" -ForegroundColor Cyan 