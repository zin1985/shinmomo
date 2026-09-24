param(
  [Parameter(Mandatory=$true)][string]$Rom,
  [string]$BizHawkRoot = "$env:USERPROFILE\Downloads\BizHawk-2.11-win-x64",
  [string]$Out = "$PSScriptRoot\goal13_trace.jsonl"
)
$ErrorActionPreference = 'Stop'
$exe = Join-Path $BizHawkRoot 'EmuHawk.exe'
if (!(Test-Path -LiteralPath $exe)) { throw "EmuHawk.exe not found: $exe" }
if (!(Test-Path -LiteralPath $Rom)) { throw "ROM not found: $Rom" }
$lua = Join-Path $PSScriptRoot 'bizhawk_goal13_probe.lua'
$env:SHINMOMO_TRACE_OUT = $Out
& $exe --lua $lua $Rom
