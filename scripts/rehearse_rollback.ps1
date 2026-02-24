param(
    [Parameter(Mandatory = $false)]
    [string]$MinVersion = "1.0.0",

    [Parameter(Mandatory = $false)]
    [string]$LatestVersion = "1.0.0"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $root "config.py"

if (-not (Test-Path $configPath)) {
    throw "config.py not found: $configPath"
}

$backup = Join-Path $env:TEMP ("config.py.rollback." + [guid]::NewGuid().ToString("N") + ".bak")
Copy-Item $configPath $backup -Force

try {
    Write-Host "[1/3] Switch to desktop-only mode"
    & (Join-Path $root "scripts\set_cutover_mode.ps1") `
        -Mode desktop-only `
        -MinVersion $MinVersion `
        -LatestVersion $LatestVersion `
        -DownloadUrl "https://example.invalid/desktop" `
        -ReleaseNotesUrl "https://example.invalid/release-notes"

    $contentDesktopOnly = Get-Content $configPath -Raw -Encoding UTF8
    if ($contentDesktopOnly -notmatch 'DESKTOP_ONLY_MODE\s*=\s*True') {
        throw "Desktop-only mode verification failed."
    }

    Write-Host "[2/3] Rollback to hybrid mode"
    & (Join-Path $root "scripts\set_cutover_mode.ps1") `
        -Mode hybrid `
        -MinVersion $MinVersion `
        -LatestVersion $LatestVersion

    $contentHybrid = Get-Content $configPath -Raw -Encoding UTF8
    if ($contentHybrid -notmatch 'DESKTOP_ONLY_MODE\s*=\s*False') {
        throw "Hybrid rollback verification failed."
    }

    Write-Host "[3/3] Rollback rehearsal passed"
}
finally {
    Copy-Item $backup $configPath -Force
    Remove-Item $backup -Force -ErrorAction SilentlyContinue
}
