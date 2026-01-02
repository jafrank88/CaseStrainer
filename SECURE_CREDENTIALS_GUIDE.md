# Secure SMTP Credentials Setup Guide

## Security Issue Fixed

The original code used `ConvertTo-SecureString` with `-AsPlainText -Force`, which exposed passwords in plaintext and posed a security risk. This has been updated to use encrypted secure strings.

## Recommended Setup Options

### Option 1: Encrypted Environment Variables (Recommended)

1. **Create an encrypted password file:**
```powershell
# Read password securely (prompts without echoing to screen)
$password = Read-Host "Enter SMTP password" -AsSecureString

# Convert to encrypted string and save to file
$encryptedPassword = $password | ConvertFrom-SecureString
$encryptedPassword | Out-File -FilePath "D:\dev\casestrainer\config\smtp_password.enc" -Encoding UTF8
```

2. **Set up environment variables:**
```powershell
# Set username (plaintext is acceptable for username)
$env:SMTP_USERNAME = "your-smtp-username@example.com"

# Set encrypted password file path
$env:SMTP_PASSWORD_ENCRYPTED = Get-Content "D:\dev\casestrainer\config\smtp_password.enc" -Raw

# Remove plaintext password environment variable if it exists
Remove-Item Env:SMTP_PASSWORD -ErrorAction SilentlyContinue
```

### Option 2: Windows Credential Manager (Most Secure)

1. **Store credentials in Windows Credential Manager:**
```powershell
# Store SMTP credentials securely
cmdkey /generic:CaseStrainer_SMTP /user:"your-smtp-username@example.com" /pass:"your-password"
```

2. **Modify the code to use Windows Credential Manager:**
```powershell
# Retrieve credentials from Windows Credential Manager
try {
    $credential = Get-StoredCredential -Target "CaseStrainer_SMTP"
    if ($credential) {
        $emailParams['Credential'] = $credential
    }
} catch {
    Write-DockerDaemonLog "Failed to retrieve stored credentials: $($_.Exception.Message)" "ERROR"
}
```

### Option 3: PowerShell Secret Management (Enterprise)

1. **Install PowerShell Secret Management module:**
```powershell
Install-Module -Name Microsoft.PowerShell.SecretManagement -Scope CurrentUser
Install-Module -Name Microsoft.PowerShell.SecretStore -Scope CurrentUser
```

2. **Set up secret vault:**
```powershell
# Register a local secret vault
Register-SecretVault -Name "CaseStrainerVault" -ModuleName Microsoft.PowerShell.SecretStore -DefaultVault
```

3. **Store SMTP credentials:**
```powershell
# Store credentials securely
Set-Secret -Name "SMTP_Username" -Secret "your-smtp-username@example.com" -Vault "CaseStrainerVault"
Set-Secret -Name "SMTP_Password" -Secret "your-password" -Vault "CaseStrainerVault"
```

## Environment Variable Configuration

### For Development (Temporary)
```powershell
$env:SMTP_USERNAME = "your-username@example.com"
$env:SMTP_PASSWORD = "your-password"  # Will show security warning
```

### For Production (Secure)
```powershell
$env:SMTP_USERNAME = "your-username@example.com"
$env:SMTP_PASSWORD_ENCRYPTED = Get-Content "D:\dev\casestrainer\config\smtp_password.enc" -Raw
```

## Testing the Setup

1. **Test email functionality:**
```powershell
# Test with current configuration
.\scripts\test_email_notification.ps1
```

2. **Verify secure credentials:**
```powershell
# Check if encrypted credentials are working
$env:SMTP_USERNAME
$env:SMTP_PASSWORD_ENCRYPTED
```

## Security Best Practices

1. **Never commit password files to version control**
2. **Use different credentials for development and production**
3. **Rotate passwords regularly**
4. **Monitor email notification logs for unauthorized access**
5. **Use application-specific passwords when possible**
6. **Enable two-factor authentication on email accounts**

## Troubleshooting

### Common Issues

1. **"Failed to create SMTP credentials"**
   - Check that encrypted password file exists and is readable
   - Verify the encrypted password was created on the same machine/user account

2. **"Email notification failed"**
   - Verify SMTP server settings
   - Check firewall rules for SMTP ports (587, 465, 25)
   - Ensure email account allows less secure apps or use app passwords

3. **"WARNING: Using plaintext SMTP password"**
   - Follow Option 1 or 2 to set up encrypted credentials
   - This warning indicates security vulnerability

### Debug Mode

Enable debug logging to troubleshoot email issues:
```powershell
$env:EMAIL_DEBUG = "true"
.\cslaunch.ps1 -Monitor
```

## Migration from Plaintext

If you were previously using plaintext passwords:

1. **Create encrypted version:**
```powershell
# Convert existing plaintext password to encrypted
$existingPassword = $env:SMTP_PASSWORD
$securePassword = ConvertTo-SecureString $existingPassword -AsPlainText -Force
$encryptedPassword = $securePassword | ConvertFrom-SecureString
$encryptedPassword | Out-File -FilePath "D:\dev\casestrainer\config\smtp_password.enc" -Encoding UTF8

# Update environment variables
$env:SMTP_PASSWORD_ENCRYPTED = Get-Content "D:\dev\casestrainer\config\smtp_password.enc" -Raw
Remove-Item Env:SMTP_PASSWORD
```

2. **Test the new configuration:**
```powershell
.\test_enhanced_simple.ps1
```

3. **Remove plaintext traces:**
```powershell
# Clear command history
Clear-History
# Remove any temporary files with plaintext passwords
```

## File Permissions

Ensure secure file permissions for credential files:
```powershell
# Restrict access to credential files
icacls "D:\dev\casestrainer\config\smtp_password.enc" /grant:r "NT AUTHORITY\SYSTEM:(R)"
icacls "D:\dev\casestrainer\config\smtp_password.enc" /grant:r "NT AUTHORITY\LOCAL SERVICE:(R)"
icacls "D:\dev\casestrainer\config\smtp_password.enc" /deny "Everyone:(W)"
```
