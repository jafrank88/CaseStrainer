# Container Cleanup for CaseStrainer

## Quick Cleanup Commands

### Remove all stale containers (Created/Exited/Dead status):
```powershell
docker container prune -f
```

### Remove specific stale containers by name:
```powershell
docker ps -a --filter name=casestrainer --filter status=created -q | docker rm -f
```

### View all containers:
```powershell
docker ps -a --filter name=casestrainer --format "table {{.Names}}\t{{.Status}}"
```

## Automated Cleanup

Add this to your scheduled tasks:
```powershell
# Run daily at 2 AM
docker container prune -f
```

## When to Clean Up

- Before running `.\cslaunch.ps1` if you get "container name already in use" errors
- After failed deployments
- When containers show "Created" status but aren't running

## Integration with cslaunch

The cleanup functionality can be added to cslaunch.ps1 as a `-Cleanup` parameter, but for now use the commands above.
