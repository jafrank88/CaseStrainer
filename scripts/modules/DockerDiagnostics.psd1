@{
    RootModule = 'DockerDiagnostics.ps1'
    ModuleVersion = '1.0.0'
    GUID = 'b2c3d4e5-f6a7-4b5c-8d7e-9f0a1b2c3d4e'
    Author = 'CaseStrainer Team'
    CompanyName = 'CaseStrainer'
    Copyright = '(c) 2025 CaseStrainer. All rights reserved.'
    Description = 'Diagnostic functions for Docker issues in CaseStrainer'
    PowerShellVersion = '5.1'
    FunctionsToExport = @(
        'Get-DockerStatus',
        'Reset-Docker'
    )
    PrivateData = @{
        PSData = @{
            Tags = @('Docker', 'Diagnostics', 'Troubleshooting', 'CaseStrainer')
            LicenseUri = 'https://github.com/yourorg/casestrainer/LICENSE'
            ProjectUri = 'https://github.com/yourorg/casestrainer'
            ReleaseNotes = 'Initial version with Docker diagnostic functions'
        }
    }
}
