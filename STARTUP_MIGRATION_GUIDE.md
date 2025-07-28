# CaseStrainer Startup Migration Guide

## 🚀 New Preferred Startup Method

**Use `cslaunch.ps1` for all CaseStrainer deployments.**

```powershell
.\cslaunch.ps1
```

## 📋 Quick Start Options

### Interactive Menu (Recommended)
```powershell
.\cslaunch.ps1
```
Then select from the menu options.

### Direct Commands
```powershell
# Quick production start
.\cslaunch.ps1 -MenuOption 1

# Full production start with rebuild
.\cslaunch.ps1 -MenuOption 2

# Force rebuild everything
.\cslaunch.ps1 -MenuOption 3

# Diagnostics mode
.\cslaunch.ps1 -Mode Diagnostics

# Test mode
.\cslaunch.ps1 -Mode Test
```

## 🗂️ Deprecated Scripts

The following scripts have been moved to `deprecated_scripts/` and should no longer be used:

### Root Directory (Deprecated)
- ~~`start_casestrainer.bat`~~ → Use `cslaunch.ps1`
- ~~`start_dev.ps1`~~ → Use `cslaunch.ps1 -Mode Debug`
- ~~`start_dev.bat`~~ → Use `cslaunch.ps1 -Mode Debug`
- ~~`start_case_strainer_fixed.bat`~~ → Use `cslaunch.ps1`
- ~~`start_case_strainer_correct.bat`~~ → Use `cslaunch.ps1`

### Scripts Directory (Deprecated)
- ~~`scripts/start_casestrainer.bat`~~ → Use `cslaunch.ps1`
- ~~`scripts/start_casestrainer_updated.bat`~~ → Use `cslaunch.ps1`
- ~~`scripts/start_vue.ps1`~~ → Use `cslaunch.ps1` (includes Vue build)
- ~~`scripts/start_vue_local.bat`~~ → Use `cslaunch.ps1`
- ~~`scripts/start_for_nginx.bat`~~ → Use `cslaunch.ps1`
- ~~`scripts/start_with_d_python.bat`~~ → Use `cslaunch.ps1`
- ~~`scripts/start_log_monitor.bat`~~ → Use `cslaunch.ps1 -ShowLogs`

## ✅ Benefits of cslaunch.ps1

1. **Docker-based Deployment**: Modern containerized approach
2. **Menu-driven Interface**: User-friendly selection of options
3. **Health Checks**: Automatic validation of services
4. **Vue.js Build Management**: Automatic frontend building
5. **Error Handling**: Comprehensive logging and crash recovery
6. **Multiple Modes**: Production, Debug, Test, Diagnostics
7. **Auto-restart**: Automatic recovery from failures
8. **Cache Management**: Intelligent caching and cleanup

## 🔄 Migration Steps

1. **Stop using old scripts** - They now show deprecation notices
2. **Use `cslaunch.ps1`** for all deployments
3. **Update any automation** to call `cslaunch.ps1` instead
4. **Update documentation** to reference the new method

## 🆘 Troubleshooting

If you encounter issues with `cslaunch.ps1`:

1. **Check PowerShell execution policy**:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Run diagnostics**:
   ```powershell
   .\cslaunch.ps1 -Mode Diagnostics
   ```

3. **View logs**:
   ```powershell
   .\cslaunch.ps1 -ShowLogs
   ```

4. **Force clean rebuild**:
   ```powershell
   .\cslaunch.ps1 -MenuOption 3
   ```

## 📞 Support

If you need help migrating from old startup scripts to `cslaunch.ps1`, check the comprehensive help:

```powershell
.\cslaunch.ps1 -Help
```

---

**Last Updated**: July 28, 2025
**Deprecated Scripts Location**: `deprecated_scripts/`
