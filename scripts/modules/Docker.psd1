@{
    # Script module or binary module file associated with this manifest.
    RootModule = 'Docker.psm1'

    # Version number of this module.
    ModuleVersion = '1.1.0'

    # ID used to uniquely identify this module
    GUID = '5a9f0b8c-3a8f-4b1a-8f3a-9c8b7c6d5e4f'

    # Author of this module
    Author = 'CaseStrainer Team'

    # Company or vendor of this module
    CompanyName = 'UW Law'

    # Copyright statement for this module
    Copyright = '(c) 2025. All rights reserved.'

    # Description of the functionality provided by this module
    Description = 'Docker management module for CaseStrainer deployment with comprehensive health checks'

    # Minimum version of the Windows PowerShell engine required by this module
    PowerShellVersion = '5.1'

    # Modules that must be imported into the global environment prior to importing this module
    # RequiredModules = @()

    # Functions to export from this module
    FunctionsToExport = @(
        'Start-DockerDesktop',
        'Stop-DockerDesktop',
        'Test-DockerAvailability',
        'Get-DockerResourceUsage',
        'Invoke-DockerCleanup',
        'Start-DockerHealthMonitor',
        'Stop-DockerHealthMonitor',
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
            Tags = @('Docker', 'Container', 'DevOps', 'CaseStrainer', 'HealthCheck')
            LicenseUri = 'https://github.com/yourorg/CaseStrainer/blob/main/LICENSE'
            ProjectUri = 'https://github.com/yourorg/CaseStrainer'
            ReleaseNotes = @'
## 1.1.0 - 2025-07-31
### Added
- Comprehensive Docker health checks and diagnostics
- Automatic Docker Desktop startup and recovery
- Resource usage monitoring and cleanup
- Network and container execution tests
- Detailed error reporting and troubleshooting

## 1.0.0 - 2025-01-01
### Added
- Initial release with basic Docker management functions
'@
        } # End of PSData hashtable
    } # End of PrivateData hashtable
}
