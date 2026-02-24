param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("client", "server")]
    [string]$Target,

    [Parameter(Mandatory = $true)]
    [string]$BuildDir,

    [Parameter(Mandatory = $false)]
    [string]$Configuration = "Release"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command wix -ErrorAction SilentlyContinue)) {
    throw "WiX v4 CLI (wix) is not installed or not in PATH."
}

$root = Split-Path -Parent $PSScriptRoot
$wixFile = if ($Target -eq "client") {
    Join-Path $root "packaging\wix\MessengerClient.wxs"
} else {
    Join-Path $root "packaging\wix\MessengerServer.wxs"
}

if (-not (Test-Path $wixFile)) {
    throw "Missing WiX definition: $wixFile"
}

$outDir = Join-Path $root "dist\msi"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$msiName = if ($Target -eq "client") { "MessengerClient.msi" } else { "MessengerServer.msi" }
$outPath = Join-Path $outDir $msiName

$define = if ($Target -eq "client") { "-dClientBuildDir=$BuildDir" } else { "-dServerBuildDir=$BuildDir" }

Write-Host "Building MSI for $Target..."
wix build $wixFile $define -o $outPath

Write-Host "MSI created: $outPath"

