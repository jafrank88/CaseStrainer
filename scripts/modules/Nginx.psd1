@{
    # Script module or binary module file associated with this manifest.
    RootModule = 'Nginx.psm1'

    # Version number of this module.
    ModuleVersion = '1.0.0'

    # Supported PSEditions
    CompatiblePSEditions = @('Core', 'Desktop')

    # ID used to uniquely identify this module
    GUID = 'a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d'

    # Author of this module
    Author = 'CaseStrainer Team'

    # Company or vendor of this module
    CompanyName = 'CaseStrainer'

    # Copyright statement for this module
    Copyright = '(c) 2025 CaseStrainer. All rights reserved.'

    # Description of the functionality provided by this module
    Description = 'Provides functions to manage Nginx web server for CaseStrainer deployment.'

    # Minimum version of the Windows PowerShell engine required by this module
    PowerShellVersion = '5.1'

    # Functions to export from this module, for best performance, do not use wildcards and do not delete the entry, use an empty array if there are no functions to export.
    FunctionsToExport = @(
        'Set-NginxConfig',
        'Test-NginxInstalled',
        'Test-NginxRunning',
        'Start-NginxServer',
        'Stop-NginxServer',
        'Update-NginxConfig',
        'Test-PortAvailable',
        'Get-NginxStatus'
    )

    # Cmdlets to export from this module, for best performance, do not use wildcards and do not delete the entry, use an empty array if there are no cmdlets to export.
    CmdletsToExport = @()

    # Variables to export from this module
    VariablesToExport = @()

    # Aliases to export from this module, for best performance, do not use wildcards and do not delete the entry, use an empty array if there are no aliases to export.
    AliasesToExport = @()

    # Private data to pass to the module specified in RootModule/ModuleToProcess. This may also contain a PSData hashtable with additional module metadata used by PowerShell.
    PrivateData = @{
        PSData = @{
            # Tags applied to this module. These help with module discovery in online galleries.
            Tags = @('Nginx', 'WebServer', 'CaseStrainer', 'Deployment')

            # A URL to the license for this module.
            # LicenseUri = ''

            # A URL to the main website for this project.
            # ProjectUri = ''

            # A URL to an icon representing this module.
            # IconUri = ''

            # ReleaseNotes of this module
            # ReleaseNotes = ''

            # Prerelease string of this module
            # Prerelease = ''

            # Flag to indicate whether the module requires explicit user acceptance for install/update/save
            # RequireLicenseAcceptance = $false

            # External dependent modules of this module
            # ExternalModuleDependencies = @()
        } # End of PSData hashtable
    } # End of PrivateData hashtable
}
