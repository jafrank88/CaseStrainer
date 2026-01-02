# Monitor extraction logs in real-time
# Run this WHILE your document is processing

Write-Host "Monitoring extraction logs..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Follow logs from all workers
docker logs -f casestrainer-rqworker1-prod 2>&1 | Select-String -Pattern "SPECIAL-FORMATS|MASTER_EXTRACT|CLEAN-PIPELINE|548 P.3d|831 F.2d|2019 WL|31 Wn. App"
