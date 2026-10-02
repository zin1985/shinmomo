param(
  [string]$BaseState = "mole_remote",
  [string]$OutputState = "analysis_lv60_hien",
  [ValidateRange(1,99)][int]$Level = 60,
  [string]$LabDir = ""
)

$ErrorActionPreference = "Stop"
$Lab = Join-Path $PSScriptRoot "shinmomo_lab.ps1"
if ([string]::IsNullOrWhiteSpace($LabDir)) {
  $LabDir = if ($env:SHINMOMO_LAB_DIR) { $env:SHINMOMO_LAB_DIR } else { Join-Path $env:LOCALAPPDATA "shinmomo-lab" }
}

function Capture-Bytes([string]$Start,[int]$Length) {
  $r = (& $Lab capture-memory -Domain WRAM -Start $Start -Length $Length -LabDir $LabDir | ConvertFrom-Json)
  return (Get-Content $r.path -Raw -Encoding UTF8 | ConvertFrom-Json).bytes
}

function Write-Bytes([string]$Start,[string]$Data) {
  (& $Lab write-memory -Domain WRAM -Start $Start -Data $Data -LabDir $LabDir | ConvertFrom-Json) | Out-Null
}

(& $Lab load-state -StateName $BaseState -LabDir $LabDir | ConvertFrom-Json) | Out-Null

$before = [ordered]@{
  level = (Capture-Bytes "0x1623" 1)[0]
  hien_destinations = @(Capture-Bytes "0x1931" 4)
  spells = @(Capture-Bytes "0x44DA" 12)
}

Write-Bytes "0x1623" ('0x{0:X2}' -f $Level)
Write-Bytes "0x1931" "0xFF,0xFF,0xFF,0xFF"

$spells = @(Capture-Bytes "0x44DA" 12)
if ($spells -notcontains 0x33) {
  $slot = -1
  for ($i=0; $i -lt $spells.Count; $i++) {
    if ($spells[$i] -eq 0) { $slot=$i; break }
  }
  if ($slot -lt 0) { throw "No empty Momotaro spell slot available for Hien (0x33)." }
  Write-Bytes ("0x{0:X4}" -f (0x44DA+$slot)) "0x33"
}

$after = [ordered]@{
  level = (Capture-Bytes "0x1623" 1)[0]
  hien_destinations = @(Capture-Bytes "0x1931" 4)
  spells = @(Capture-Bytes "0x44DA" 12)
}

if ($after.level -ne $Level) { throw "Level verification failed." }
if (@($after.hien_destinations | Where-Object { $_ -ne 255 }).Count -ne 0) { throw "Hien destination verification failed." }
if ($after.spells -notcontains 0x33) { throw "Hien spell verification failed." }

$save = (& $Lab save-state -StateName $OutputState -LabDir $LabDir | ConvertFrom-Json)

[ordered]@{
  ok = $true
  base_state = $BaseState
  output_state = $OutputState
  path = $save.path
  before = $before
  after = $after
  notes = @(
    "Level uses WRAM 0x1623.",
    "Hien destinations use WRAM 0x1931..0x1934 and are set to FF.",
    "Momotaro spell slots use WRAM 0x44DA..0x44E5; Hien spell id is 0x33."
  )
} | ConvertTo-Json -Depth 8
