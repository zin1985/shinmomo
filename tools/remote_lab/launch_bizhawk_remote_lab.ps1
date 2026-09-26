param(
  [Parameter(Mandatory=$true)][string]$Rom,
  [string]$BizHawkRoot = "$env:USERPROFILE\Downloads\BizHawk-2.11-win-x64",
  [string]$LabDir = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($LabDir)) {
  $LabDir = Join-Path $env:LOCALAPPDATA "shinmomo-lab"
}

$exe = Join-Path $BizHawkRoot "EmuHawk.exe"
$lua = Join-Path $PSScriptRoot "shinmomo_remote_bridge.lua"

if (!(Test-Path -LiteralPath $exe)) { throw "EmuHawk.exe not found: $exe" }
if (!(Test-Path -LiteralPath $Rom)) { throw "ROM not found: $Rom" }
if (!(Test-Path -LiteralPath $lua)) { throw "Bridge Lua not found: $lua" }

New-Item -ItemType Directory -Force -Path $LabDir,(Join-Path $LabDir "screens"),(Join-Path $LabDir "responses"),(Join-Path $LabDir "captures") | Out-Null
Remove-Item -LiteralPath (Join-Path $LabDir "command.tsv") -Force -ErrorAction SilentlyContinue

$env:SHINMOMO_LAB_DIR = $LabDir

Write-Host "ShinMomo remote lab: $LabDir"
Write-Host "ROM remains out-of-tree: $Rom"

& $exe "--lua=$lua" "$Rom"
