param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("all", "server", "client")]
    [string]$Target = "all",

    [Parameter(Mandatory = $false)]
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    throw "PyInstaller is not installed or not in PATH. Install with: pip install pyinstaller"
}

$specFile = Join-Path $root "messenger.spec"
if (-not (Test-Path $specFile)) {
    throw "Spec file not found: $specFile"
}

$serverSpec = Join-Path $root "messenger.spec"
$clientSpec = Join-Path $root "messenger_client.spec"
if (-not (Test-Path $serverSpec)) {
    throw "Server spec not found: $serverSpec"
}
if (-not (Test-Path $clientSpec)) {
    throw "Client spec not found: $clientSpec"
}

if ($Clean) {
    Write-Host "Cleaning previous build outputs..."
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $root "build")
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $root "dist")
}

function Invoke-SpecBuild([string]$specPath) {
    $args = @($specPath, "--noconfirm")
    if ($Clean) { $args += "--clean" }
    pyinstaller @args
}

if ($Target -in @("all", "server")) {
    Write-Host "Building server EXE via messenger.spec..."
    Invoke-SpecBuild $serverSpec
}

if ($Target -in @("all", "client")) {
    Write-Host "Building client EXE via messenger_client.spec..."
    Invoke-SpecBuild $clientSpec
}

$distRoot = Join-Path $root "dist"
$serverExe = Join-Path $distRoot "MessengerServer.exe"
$clientExe = Join-Path $distRoot "MessengerClient.exe"

if ($Target -in @("all", "server") -and -not (Test-Path $serverExe)) {
    throw "Server executable not found: $serverExe"
}
if ($Target -in @("all", "client") -and -not (Test-Path $clientExe)) {
    throw "Client executable not found: $clientExe"
}

$releaseRoot = Join-Path $distRoot "exe"
$serverOut = Join-Path $releaseRoot "server"
$clientOut = Join-Path $releaseRoot "client"

New-Item -ItemType Directory -Force -Path $serverOut | Out-Null
New-Item -ItemType Directory -Force -Path $clientOut | Out-Null

if ($Target -in @("all", "server")) {
    Copy-Item $serverExe -Destination (Join-Path $serverOut "MessengerServer.exe") -Force
    Write-Host "Prepared server build dir: $serverOut"
}

if ($Target -in @("all", "client")) {
    Copy-Item $clientExe -Destination (Join-Path $clientOut "MessengerClient.exe") -Force
    Write-Host "Prepared client build dir: $clientOut"
}

Write-Host ""
Write-Host "Build complete."
Write-Host "Raw EXEs:"
if ($Target -in @("all", "server")) { Write-Host "  $serverExe" }
if ($Target -in @("all", "client")) { Write-Host "  $clientExe" }
Write-Host "MSI-ready dirs:"
if ($Target -in @("all", "server")) { Write-Host "  $serverOut" }
if ($Target -in @("all", "client")) { Write-Host "  $clientOut" }
