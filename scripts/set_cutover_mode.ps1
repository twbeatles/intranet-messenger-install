param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("desktop-only", "hybrid")]
    [string]$Mode,

    [Parameter(Mandatory = $false)]
    [string]$MinVersion = "1.0.0",

    [Parameter(Mandatory = $false)]
    [string]$LatestVersion = "1.0.0",

    [Parameter(Mandatory = $false)]
    [string]$DownloadUrl = "",

    [Parameter(Mandatory = $false)]
    [string]$ReleaseNotesUrl = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $root "config.py"

if (-not (Test-Path $configPath)) {
    throw "config.py not found: $configPath"
}

$content = Get-Content $configPath -Raw -Encoding UTF8
$desktopOnly = if ($Mode -eq "desktop-only") { "True" } else { "False" }

$replacements = @{
    "DESKTOP_ONLY_MODE\s*=\s*(True|False)" = "DESKTOP_ONLY_MODE = $desktopOnly"
    "DESKTOP_CLIENT_MIN_VERSION\s*=\s*`".*?`"" = "DESKTOP_CLIENT_MIN_VERSION = `"$MinVersion`""
    "DESKTOP_CLIENT_LATEST_VERSION\s*=\s*`".*?`"" = "DESKTOP_CLIENT_LATEST_VERSION = `"$LatestVersion`""
    "DESKTOP_CLIENT_DOWNLOAD_URL\s*=\s*`".*?`"" = "DESKTOP_CLIENT_DOWNLOAD_URL = `"$DownloadUrl`""
    "DESKTOP_CLIENT_RELEASE_NOTES_URL\s*=\s*`".*?`"" = "DESKTOP_CLIENT_RELEASE_NOTES_URL = `"$ReleaseNotesUrl`""
}

foreach ($pattern in $replacements.Keys) {
    $content = [regex]::Replace($content, $pattern, $replacements[$pattern])
}

Set-Content -Path $configPath -Value $content -Encoding UTF8
Write-Host "Cutover mode updated:"
Write-Host "  DESKTOP_ONLY_MODE = $desktopOnly"
Write-Host "  MIN_VERSION = $MinVersion"
Write-Host "  LATEST_VERSION = $LatestVersion"

