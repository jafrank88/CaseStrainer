@{
    RootModule        = 'DockerHealth.psm1'
    ModuleVersion     = '1.0.0'
    GUID              = '1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d'
    Author            = 'CaseStrainer Team'
    CompanyName       = 'UW Law'
    Copyright         = '(c) 2025. All rights reserved.'
    Description       = 'Comprehensive Docker health checks and diagnostics for CaseStrainer deployment'
    PowerShellVersion = '5.1'
    
    # Functions to export from this module
    FunctionsToExport = @(
        'Test-DockerProcesses',
        'Test-DockerCLI',
        'Test-DockerDaemon',
        'Test-DockerContainerRun',
        'Test-DockerCompose',
        'Test-DockerResources',
        'Test-DockerNetwork',
        'Invoke-DockerHealthCheck',
        'Test-DockerHealth'
    )
    
    # Cmdlets to export from this module
    CmdletsToExport = @()
    
    # Variables to export from this module
    VariablesToExport = @()
    
    # Aliases to export from this module
    AliasesToExport = @()
    
    # Private data to pass to the module
    PrivateData = @{
        PSData = @{
            Tags = @('Docker', 'HealthCheck', 'Diagnostics', 'CaseStrainer')
            LicenseUri = ''
            ProjectUri = ''
            IconUri = ''
            ReleaseNotes = 'Initial version with comprehensive Docker health checks'
        }
    }
}
