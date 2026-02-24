param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("all", "server", "client")]
    [string]$Target = "all",

    [Parameter(Mandatory = $false)]
    [string]$PfxPath = "",

    [Parameter(Mandatory = $false)]
    [string]$PfxPassword = "",

    [Parameter(Mandatory = $false)]
    [string]$CertThumbprint = "",

    [Parameter(Mandatory = $false)]
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command signtool -ErrorAction SilentlyContinue)) {
    throw "signtool is not installed or not in PATH."
}

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if ([string]::IsNullOrWhiteSpace($PfxPath) -and [string]::IsNullOrWhiteSpace($CertThumbprint)) {
    throw "Either -PfxPath or -CertThumbprint must be provided."
}

if (-not [string]::IsNullOrWhiteSpace($PfxPath) -and -not (Test-Path $PfxPath)) {
    throw "PFX file not found: $PfxPath"
}

function Invoke-SignFile([string]$FilePath) {
    if (-not (Test-Path $FilePath)) {
        Write-Host "Skip (missing): $FilePath"
        return
    }

    $args = @("sign", "/fd", "SHA256", "/tr", $TimestampUrl, "/td", "SHA256", "/a")

    if (-not [string]::IsNullOrWhiteSpace($PfxPath)) {
        $args += @("/f", $PfxPath)
        if (-not [string]::IsNullOrWhiteSpace($PfxPassword)) {
            $args += @("/p", $PfxPassword)
        }
    } else {
        $args += @("/sha1", $CertThumbprint)
    }

    $args += @($FilePath)
    Write-Host "Signing: $FilePath"
    & signtool @args
}

$files = @()
if ($Target -in @("all", "server")) {
    $files += @(
        (Join-Path $root "dist\MessengerServer.exe"),
        (Join-Path $root "dist\msi\MessengerServer.msi")
    )
}
if ($Target -in @("all", "client")) {
    $files += @(
        (Join-Path $root "dist\MessengerClient.exe"),
        (Join-Path $root "dist\msi\MessengerClient.msi")
    )
}

foreach ($file in $files) {
    Invoke-SignFile $file
}

Write-Host "Signing step completed."
