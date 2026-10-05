<#
  claude-footprint.ps1
  --------------------------------------------------------------------------
  Purpose : Find what Claude-related tooling and local git repositories are
            consuming on this machine.
  Policy  : READ ONLY. This script never deletes, moves or modifies anything.

  Run     : powershell -ExecutionPolicy Bypass -File .\claude-footprint.ps1

  Sections
    1. Known Claude / AI tooling locations (probed, with depth-1 breakdown)
    2. AppData top-level breakdown (to catch anything section 1 missed)
    3. Local git repositories (.git size, last activity)
    4. Things a file scan cannot see

  Note    : Pure ASCII on purpose. Windows PowerShell 5.1 reads BOM-less
            files with the legacy code page, which corrupts non-ASCII text
            and breaks the parser. Do not add Japanese to this file.

  Warning : Section 2 and 3 walk large directory trees and can take several
            minutes. Use -SkipAppData or -SkipGit to shorten a run.
  --------------------------------------------------------------------------
#>

[CmdletBinding()]
param(
    # Where to look for git repositories
    [string[]]$SearchRoots = @(
        "$env:USERPROFILE\Desktop",
        "$env:USERPROFILE\Documents",
        "$env:USERPROFILE\source",
        "C:\dev"
    ),

    [int]$TopN = 20,

    [switch]$SkipAppData,
    [switch]$SkipGit,

    [string]$JsonOut
)

$ErrorActionPreference = 'Continue'

# --- helpers ----------------------------------------------------------------
function Format-Size([long]$Bytes) {
    if     ($Bytes -ge 1TB) { return "{0,8:N2} TB" -f ($Bytes / 1TB) }
    elseif ($Bytes -ge 1GB) { return "{0,8:N2} GB" -f ($Bytes / 1GB) }
    elseif ($Bytes -ge 1MB) { return "{0,8:N2} MB" -f ($Bytes / 1MB) }
    elseif ($Bytes -ge 1KB) { return "{0,8:N2} KB" -f ($Bytes / 1KB) }
    else                    { return "{0,8} B"  -f  $Bytes }
}

# Total size of a folder. Reparse points are skipped so linked content is not
# counted twice. Access-denied entries are silently ignored.
function Get-FolderSize([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }

    $sum = 0L
    $cnt = 0
    Get-ChildItem -LiteralPath $Path -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) } |
        ForEach-Object { $sum += $_.Length; $cnt++ }

    return [pscustomobject]@{ Bytes = $sum; Count = $cnt }
}

function Write-Rule { Write-Host ("=" * 78) }

$result = [ordered]@{
    ScannedAt = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
}

# ===========================================================================
# 1. Known Claude / AI tooling locations
# ===========================================================================
Write-Host ""
Write-Rule
Write-Host "1. Known Claude / AI tooling locations"
Write-Rule

# Label -> path. Layout changes between versions, so treat a miss as "not
# present on this machine or moved", not as an error.
$known = [ordered]@{
    'Claude Desktop (roaming: config, logs, cache)' = "$env:APPDATA\Claude"
    'Claude Desktop (local: app versions)'          = "$env:LOCALAPPDATA\AnthropicClaude"
    'Claude Code (sessions, projects, history)'     = "$env:USERPROFILE\.claude"
    'Ollama (models)'                               = "$env:USERPROFILE\.ollama"
    'npm global packages'                           = "$env:APPDATA\npm"
    'npm cache'                                     = "$env:LOCALAPPDATA\npm-cache"
    'pip cache'                                     = "$env:LOCALAPPDATA\pip\Cache"
    'VS Code (user data, workspace storage)'        = "$env:APPDATA\Code"
    'VS Code extensions'                            = "$env:USERPROFILE\.vscode\extensions"
    'User temp'                                     = "$env:LOCALAPPDATA\Temp"
}

$knownReport = @()

foreach ($label in $known.Keys) {
    $path = $known[$label]
    $size = Get-FolderSize $path

    if ($null -eq $size) {
        Write-Host ("  {0,-11}  {1}" -f "[absent]", $label) -ForegroundColor DarkGray
        continue
    }

    Write-Host ("  {0}  {1}" -f (Format-Size $size.Bytes), $label) -ForegroundColor White
    Write-Host ("               {0}  ({1:N0} files)" -f $path, $size.Count) -ForegroundColor DarkGray

    # Depth-1 breakdown, so accumulating version folders (app-1.2.3, etc.)
    # and oversized subfolders become visible.
    $children = Get-ChildItem -LiteralPath $path -Directory -Force -ErrorAction SilentlyContinue |
        ForEach-Object {
            $cs = Get-FolderSize $_.FullName
            [pscustomobject]@{ Name = $_.Name; Bytes = $cs.Bytes }
        } | Sort-Object Bytes -Descending | Select-Object -First 5

    foreach ($c in $children) {
        if ($c.Bytes -gt 1MB) {
            Write-Host ("      -> {0}  {1}" -f (Format-Size $c.Bytes), $c.Name) -ForegroundColor DarkCyan
        }
    }

    $knownReport += [ordered]@{
        Label = $label
        Path  = $path
        Bytes = $size.Bytes
        Files = $size.Count
    }
}

$knownTotal = ($knownReport | Measure-Object -Property Bytes -Sum).Sum
Write-Host ""
Write-Host ("  SUBTOTAL {0}" -f (Format-Size $knownTotal)) -ForegroundColor Yellow

$result.KnownLocations = $knownReport

# ===========================================================================
# 2. AppData top-level breakdown
# ===========================================================================
if (-not $SkipAppData) {
    Write-Host ""
    Write-Rule
    Write-Host "2. AppData top-level breakdown (this takes a while)"
    Write-Rule

    $appDataReport = @()

    foreach ($base in @("$env:APPDATA", "$env:LOCALAPPDATA")) {

        if (-not (Test-Path -LiteralPath $base)) { continue }

        Write-Host ""
        Write-Host "  $base" -ForegroundColor Cyan

        $dirs = Get-ChildItem -LiteralPath $base -Directory -Force -ErrorAction SilentlyContinue |
            ForEach-Object {
                Write-Progress -Activity "Measuring $base" -Status $_.Name
                $s = Get-FolderSize $_.FullName
                [pscustomobject]@{ Name = $_.Name; Path = $_.FullName; Bytes = $s.Bytes; Count = $s.Count }
            } | Sort-Object Bytes -Descending

        Write-Progress -Activity "Measuring $base" -Completed

        $baseTotal = ($dirs | Measure-Object -Property Bytes -Sum).Sum
        Write-Host ("  total {0}" -f (Format-Size $baseTotal))
        Write-Host ""

        $dirs | Select-Object -First $TopN | ForEach-Object {
            $pct = if ($baseTotal -gt 0) { 100 * $_.Bytes / $baseTotal } else { 0 }
            Write-Host ("    {0}  {1,5:N1}%  {2}" -f (Format-Size $_.Bytes), $pct, $_.Name)
        }

        $appDataReport += [ordered]@{
            Base       = $base
            TotalBytes = $baseTotal
            Folders    = @($dirs | Select-Object -First $TopN | ForEach-Object {
                [ordered]@{ Name = $_.Name; Bytes = $_.Bytes; Count = $_.Count }
            })
        }
    }

    $result.AppData = $appDataReport
}

# ===========================================================================
# 3. Local git repositories
# ===========================================================================
if (-not $SkipGit) {
    Write-Host ""
    Write-Rule
    Write-Host "3. Local git repositories"
    Write-Rule

    $repos = @()

    foreach ($sr in $SearchRoots) {

        if (-not (Test-Path -LiteralPath $sr)) {
            Write-Host ("  [absent] {0}" -f $sr) -ForegroundColor DarkGray
            continue
        }

        Write-Host ("  searching {0} ..." -f $sr) -ForegroundColor Cyan

        # .git is hidden, so -Force is required to see it at all.
        Get-ChildItem -LiteralPath $sr -Recurse -Directory -Force -Filter '.git' -ErrorAction SilentlyContinue |
            ForEach-Object {
                Write-Progress -Activity "Measuring repositories" -Status $_.FullName
                $gitSize  = Get-FolderSize $_.FullName
                $repoRoot = Split-Path $_.FullName -Parent
                $workSize = Get-FolderSize $repoRoot

                $repos += [pscustomobject]@{
                    Repo      = $repoRoot
                    GitBytes  = $gitSize.Bytes
                    TotalBytes= $workSize.Bytes
                    LastWrite = $_.LastWriteTime
                }
            }
    }

    Write-Progress -Activity "Measuring repositories" -Completed

    if ($repos.Count -eq 0) {
        Write-Host "  no repositories found under the given search roots" -ForegroundColor DarkGray
        Write-Host "  hint: pass -SearchRoots to point at where your code lives"
    }
    else {
        $gitTotal = ($repos | Measure-Object -Property GitBytes -Sum).Sum
        Write-Host ""
        Write-Host ("  {0} repositories, .git total {1}" -f $repos.Count, (Format-Size $gitTotal)) -ForegroundColor Yellow
        Write-Host ""
        Write-Host ("    {0}  {1}  {2}  {3}" -f ".git".PadLeft(11), "working tree".PadLeft(13), "last write", "path")

        $repos | Sort-Object GitBytes -Descending | ForEach-Object {
            Write-Host ("    {0}  {1}  {2}  {3}" -f `
                (Format-Size $_.GitBytes), `
                (Format-Size $_.TotalBytes), `
                $_.LastWrite.ToString('yyyy-MM-dd'), `
                $_.Repo)
        }

        Write-Host ""
        Write-Host "  Note: a large .git relative to the working tree usually means"
        Write-Host "  committed binaries or generated files. 'git count-objects -vH'"
        Write-Host "  inside a repository shows the breakdown."

        $result.GitRepos = @($repos | Sort-Object GitBytes -Descending | ForEach-Object {
            [ordered]@{ Repo = $_.Repo; GitBytes = $_.GitBytes; TotalBytes = $_.TotalBytes; LastWrite = $_.LastWrite.ToString('yyyy-MM-dd') }
        })
    }
}

# ===========================================================================
# 4. Things a file scan cannot see
# ===========================================================================
Write-Host ""
Write-Rule
Write-Host "4. Space a file scan cannot see - check these separately"
Write-Rule
Write-Host "  Docker Desktop : lives inside a WSL2 virtual disk"
Write-Host "                   check -> docker system df"
Write-Host "                   path  -> %LOCALAPPDATA%\Docker\wsl  (ext4.vhdx)"
Write-Host "  Ollama models  : check -> ollama list"
Write-Host "  WSL distros    : check -> wsl --list -v"
Write-Host "  Recycle Bin    : check -> Storage settings, or empty it manually"
Write-Host "  Windows Update : check -> Disk Cleanup (cleanmgr)"

# --- optional JSON ----------------------------------------------------------
if ($JsonOut) {
    $result | ConvertTo-Json -Depth 6 | Out-File -LiteralPath $JsonOut -Encoding UTF8
    Write-Host ""
    Write-Host ("JSON written to: {0}" -f $JsonOut) -ForegroundColor Green
}

Write-Host ""
Write-Host "Done. Nothing was deleted." -ForegroundColor Green
Write-Host ""