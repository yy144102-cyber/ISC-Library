# Print the versions of the development tools, for the table in
# workspace.md section 3 ("measured values"). Read only: changes nothing.
#
# Run from the workspace root:
#     pwsh -File Library/tools/pc-setup/check-env.ps1
#
# ASCII only (workspace.md R7).

$ErrorActionPreference = 'Continue'

function Show-Version($label, $exe, $argList) {
    if (Get-Command $exe -ErrorAction SilentlyContinue) {
        $v = (& $exe @argList 2>&1 | Select-Object -First 1)
    } else {
        $v = 'not found'
    }
    '{0,-12} {1}' -f $label, $v
}

'{0,-12} {1}' -f 'date', (Get-Date -Format 'yyyy-MM-dd')
'{0,-12} {1}' -f 'computer', $env:COMPUTERNAME
$os = Get-CimInstance Win32_OperatingSystem
'{0,-12} {1} {2}' -f 'OS', $os.Caption, $os.Version
'{0,-12} {1}' -f 'PowerShell', $PSVersionTable.PSVersion.ToString()
Show-Version 'git'     'git'    @('--version')
Show-Version 'Python'  'python' @('--version')
Show-Version 'VS Code' 'code'   @('--version')
Show-Version 'winget'  'winget' @('--version')
if (Get-Command dotnet -ErrorAction SilentlyContinue) {
    $sdks = (dotnet --list-sdks | ForEach-Object { ($_ -split ' ')[0] }) -join ' / '
    '{0,-12} {1}' -f '.NET SDK', $sdks
} else {
    '{0,-12} {1}' -f '.NET SDK', 'not found'
}
if (Get-Command code -ErrorAction SilentlyContinue) {
    $n = (code --list-extensions 2>$null | Measure-Object).Count
    '{0,-12} {1}' -f 'VS Code ext', "$n extensions"
}
