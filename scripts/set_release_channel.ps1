param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("stable", "canary")]
    [string]$DefaultChannel = "stable",

    [Parameter(Mandatory = $false)]
    [string]$StableMinVersion = "1.0.0",

    [Parameter(Mandatory = $false)]
    [string]$StableLatestVersion = "1.0.0",

    [Parameter(Mandatory = $false)]
    [string]$StableDownloadUrl = "",

    [Parameter(Mandatory = $false)]
    [string]$StableReleaseNotesUrl = "",

    [Parameter(Mandatory = $false)]
    [string]$CanaryMinVersion = "1.0.0",

    [Parameter(Mandatory = $false)]
    [string]$CanaryLatestVersion = "1.0.0",

    [Parameter(Mandatory = $false)]
    [string]$CanaryDownloadUrl = "",

    [Parameter(Mandatory = $false)]
    [string]$CanaryReleaseNotesUrl = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $root "config.py"

if (-not (Test-Path $configPath)) {
    throw "config.py not found: $configPath"
}

$content = Get-Content $configPath -Raw -Encoding UTF8

$replacements = @(
    @{ Pattern = 'DESKTOP_CLIENT_CHANNEL_DEFAULT\s*=\s*".*?"'; Value = "DESKTOP_CLIENT_CHANNEL_DEFAULT = `"$DefaultChannel`"" },
    @{ Pattern = 'DESKTOP_CLIENT_MIN_VERSION\s*=\s*".*?"'; Value = "DESKTOP_CLIENT_MIN_VERSION = `"$StableMinVersion`"" },
    @{ Pattern = 'DESKTOP_CLIENT_LATEST_VERSION\s*=\s*".*?"'; Value = "DESKTOP_CLIENT_LATEST_VERSION = `"$StableLatestVersion`"" },
    @{ Pattern = 'DESKTOP_CLIENT_DOWNLOAD_URL\s*=\s*".*?"'; Value = "DESKTOP_CLIENT_DOWNLOAD_URL = `"$StableDownloadUrl`"" },
    @{ Pattern = 'DESKTOP_CLIENT_RELEASE_NOTES_URL\s*=\s*".*?"'; Value = "DESKTOP_CLIENT_RELEASE_NOTES_URL = `"$StableReleaseNotesUrl`"" },
    @{ Pattern = 'DESKTOP_CLIENT_CANARY_MIN_VERSION\s*=\s*".*?"'; Value = "DESKTOP_CLIENT_CANARY_MIN_VERSION = `"$CanaryMinVersion`"" },
    @{ Pattern = 'DESKTOP_CLIENT_CANARY_LATEST_VERSION\s*=\s*".*?"'; Value = "DESKTOP_CLIENT_CANARY_LATEST_VERSION = `"$CanaryLatestVersion`"" },
    @{ Pattern = 'DESKTOP_CLIENT_CANARY_DOWNLOAD_URL\s*=\s*".*?"'; Value = "DESKTOP_CLIENT_CANARY_DOWNLOAD_URL = `"$CanaryDownloadUrl`"" },
    @{ Pattern = 'DESKTOP_CLIENT_CANARY_RELEASE_NOTES_URL\s*=\s*".*?"'; Value = "DESKTOP_CLIENT_CANARY_RELEASE_NOTES_URL = `"$CanaryReleaseNotesUrl`"" }
)

foreach ($replace in $replacements) {
    $content = [regex]::Replace($content, $replace.Pattern, $replace.Value)
}

Set-Content -Path $configPath -Value $content -Encoding UTF8

Write-Host "Release channel configuration updated."
Write-Host "  Default channel: $DefaultChannel"
Write-Host "  Stable latest: $StableLatestVersion"
Write-Host "  Canary latest: $CanaryLatestVersion"
