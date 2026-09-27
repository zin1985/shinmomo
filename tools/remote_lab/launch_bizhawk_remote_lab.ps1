param(
  [Parameter(Mandatory=$true)][string]$Rom,
  [string]$BizHawkRoot = "$env:USERPROFILE\Downloads\BizHawk-2.11-win-x64",
  [string]$LabDir = "",
  [switch]$NormalSpeed
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($LabDir)) {
  $LabDir = Join-Path $env:LOCALAPPDATA "shinmomo-lab"
}

$exe = Join-Path $BizHawkRoot "EmuHawk.exe"
$lua = Join-Path $PSScriptRoot "shinmomo_remote_bridge.lua"
$configPath = Join-Path $BizHawkRoot "config.ini"

if (!(Test-Path -LiteralPath $exe)) { throw "EmuHawk.exe not found: $exe" }
if (!(Test-Path -LiteralPath $Rom)) { throw "ROM not found: $Rom" }
if (!(Test-Path -LiteralPath $lua)) { throw "Bridge Lua not found: $lua" }

New-Item -ItemType Directory -Force -Path $LabDir,(Join-Path $LabDir "screens"),(Join-Path $LabDir "responses"),(Join-Path $LabDir "captures") | Out-Null
Remove-Item -LiteralPath (Join-Path $LabDir "command.tsv") -Force -ErrorAction SilentlyContinue

$env:SHINMOMO_LAB_DIR = $LabDir

Write-Host "ShinMomo remote lab: $LabDir"
Write-Host "ROM remains out-of-tree: $Rom"

$originalConfig = $null
$configChanged = $false

try {
  if (!$NormalSpeed -and (Test-Path -LiteralPath $configPath)) {
    $originalConfig = [IO.File]::ReadAllText($configPath, [Text.Encoding]::UTF8)
    $fastConfig = $originalConfig.Replace('"Unthrottled": false', '"Unthrottled": true')
    if ($fastConfig -ne $originalConfig) {
      [IO.File]::WriteAllText($configPath, $fastConfig, [Text.UTF8Encoding]::new($false))
      $configChanged = $true
    }
    Write-Host "Remote lab speed: MAX / unthrottled while explicit frame commands run."
  } else {
    Write-Host "Remote lab speed: normal throttled mode."
  }

  & $exe "--lua=$lua" "$Rom"
}
finally {
  if ($configChanged -and $null -ne $originalConfig) {
    [IO.File]::WriteAllText($configPath, $originalConfig, [Text.UTF8Encoding]::new($false))
    Write-Host "BizHawk throttle setting restored after remote lab exit."
  }
}
