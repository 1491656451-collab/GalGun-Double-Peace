[CmdletBinding()]
param(
    [string]$GameRoot
)

$ErrorActionPreference = 'Stop'
$PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $PatchRoot 'manifest_sha256.txt'

if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Manifest not found: $ManifestPath"
}
if ([string]::IsNullOrWhiteSpace($GameRoot)) {
    $GameRoot = Split-Path -Parent $PatchRoot
    $gameDataRoot = Join-Path $GameRoot 'GG2Game'
    if (-not (Test-Path -LiteralPath $gameDataRoot -PathType Container)) {
        throw "Automatic game root detection failed. Expected GG2Game beside the patch directory: $gameDataRoot"
    }
    Write-Host "Detected game root: $GameRoot"
}
$GameRoot = [IO.Path]::GetFullPath($GameRoot)
if ($GameRoot -match '(?i)GG2CNPatch_Distribution') {
    throw 'Do not use GG2CNPatch_Distribution as the game root.'
}
if (-not (Test-Path -LiteralPath $GameRoot -PathType Container)) {
    throw "Game root not found: $GameRoot"
}

$entries = @()
foreach ($line in Get-Content -LiteralPath $ManifestPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -notmatch '^([0-9A-Fa-f]{64})\s{2}(.+)$') {
        throw "Invalid manifest line: $line"
    }
    $entries += [PSCustomObject]@{ Hash = $Matches[1].ToUpperInvariant(); Relative = $Matches[2] }
}
if ($entries.Count -eq 0) { throw 'Manifest contains no files.' }

$targets = @()
foreach ($entry in $entries) {
    if ($entry.Relative -match '(^|[\\/])\.\.([\\/]|$)') { throw "Unsafe manifest path: $($entry.Relative)" }
    $source = Join-Path $PatchRoot $entry.Relative
    $target = Join-Path $GameRoot $entry.Relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Patch file missing: $source" }
    if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw "Target file missing: $target" }
    $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($sourceHash -ne $entry.Hash) { throw "Patch hash mismatch: $($entry.Relative)" }
    $targets += [PSCustomObject]@{ Relative = $entry.Relative; Source = $source; Target = $target; Hash = $entry.Hash }
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupRoot = Join-Path $PatchRoot (Join-Path 'backup' $stamp)
foreach ($item in $targets) {
    $backupPath = Join-Path $backupRoot $item.Relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backupPath) | Out-Null
    Copy-Item -LiteralPath $item.Target -Destination $backupPath -Force
}

foreach ($item in $targets) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $item.Target) | Out-Null
    Copy-Item -LiteralPath $item.Source -Destination $item.Target -Force
    $targetHash = (Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($targetHash -ne $item.Hash) { throw "Installed hash mismatch: $($item.Relative)" }
}

Write-Host "Installed $($targets.Count) files."
Write-Host "Backup created at: $backupRoot"
Write-Host 'Installation completed.'
