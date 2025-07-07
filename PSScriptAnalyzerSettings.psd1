@{
    Severity = @('Error', 'Warning')
    ExcludeRules = @(
        'PSAvoidUsingWriteHost'  # Acceptable for interactive scripts
    )
    IncludeDefaultRules = $true
    Rules = @{
        PSUseSingularNouns = @{
            Enable = $false  # Disable for function names like "Start-Services"
        }
        PSAvoidUsingComputerNameHardcoded = @{
            Whitelist = @('localhost', '127.0.0.1')
        }
    }
} 