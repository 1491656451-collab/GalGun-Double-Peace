[CmdletBinding()]
param(
    [string]$GameRoot,
    [string]$BackupPath
)

$ErrorActionPreference = 'Stop'
$PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $PatchRoot 'manifest_sha256.txt'

if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw "Manifest not found: $ManifestPath" }
if ([string]::IsNullOrWhiteSpace($GameRoot)) {
    $GameRoot = Split-Path -Parent $PatchRoot
    $gameDataRoot = Join-Path $GameRoot 'GG2Game'
    if (-not (Test-Path -LiteralPath $gameDataRoot -PathType Container)) {
        throw "Automatic game root detection failed. Expected GG2Game beside the patch directory: $gameDataRoot"
    }
    Write-Host "Detected game root: $GameRoot"
}
$GameRoot = [IO.Path]::GetFullPath($GameRoot)
if ($GameRoot -match '(?i)GG2CNPatch_Distribution') { throw 'Do not use GG2CNPatch_Distribution as the game root.' }
if (-not (Test-Path -LiteralPath $GameRoot -PathType Container)) { throw "Game root not found: $GameRoot" }

if ([string]::IsNullOrWhiteSpace($BackupPath)) {
    $backupBase = Join-Path $PatchRoot 'backup'
    if (-not (Test-Path -LiteralPath $backupBase -PathType Container)) { throw "No backup directory found: $backupBase" }
    $latest = Get-ChildItem -LiteralPath $backupBase -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if ($null -eq $latest) { throw "No timestamped backup found in: $backupBase" }
    $BackupPath = $latest.FullName
} else {
    $BackupPath = [IO.Path]::GetFullPath($BackupPath)
}
if (-not (Test-Path -LiteralPath $BackupPath -PathType Container)) { throw "Backup path not found: $BackupPath" }

$entries = @()
foreach ($line in Get-Content -LiteralPath $ManifestPath) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -notmatch '^([0-9A-Fa-f]{64})\s{2}(.+)$') { throw "Invalid manifest line: $line" }
    $entries += [PSCustomObject]@{ Relative = $Matches[2] }
}

foreach ($entry in $entries) {
    if ($entry.Relative -match '(^|[\\/])\.\.([\\/]|$)') { throw "Unsafe manifest path: $($entry.Relative)" }
    $source = Join-Path $BackupPath $entry.Relative
    $target = Join-Path $GameRoot $entry.Relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Backup file missing: $source" }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
    $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToUpperInvariant()
    $targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($sourceHash -ne $targetHash) { throw "Restore hash mismatch: $($entry.Relative)" }
}

Write-Host "Restored $($entries.Count) files."
Write-Host "Restored from: $BackupPath"
Write-Host 'Restore completed.'
