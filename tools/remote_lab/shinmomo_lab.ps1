param(
  [Parameter(Mandatory=$true, Position=0)]
  [ValidateSet("screen","click","key","gamepad","capture-memory")]
  [string]$Command,

  [int]$X = 0,
  [int]$Y = 0,
  [ValidateSet("left","right","middle")]
  [string]$Button = "left",
  [string]$Keys = "",
  [string]$WindowTitle = "",

  [string]$Buttons = "",
  [int]$Frames = 1,
  [int]$Player = 1,

  [string]$Domain = "WRAM",
  [string]$Start = "0x0000",
  [int]$Length = 256,

  [string]$Out = "",
  [string]$LabDir = "",
  [int]$TimeoutMs = 8000
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($LabDir)) {
  if ($env:SHINMOMO_LAB_DIR) {
    $LabDir = $env:SHINMOMO_LAB_DIR
  } else {
    $LabDir = Join-Path $env:LOCALAPPDATA "shinmomo-lab"
  }
}

$ScreensDir = Join-Path $LabDir "screens"
$ResponsesDir = Join-Path $LabDir "responses"
$CapturesDir = Join-Path $LabDir "captures"
$CommandPath = Join-Path $LabDir "command.tsv"

New-Item -ItemType Directory -Force -Path $LabDir,$ScreensDir,$ResponsesDir,$CapturesDir | Out-Null

function Emit-Result([hashtable]$Data) {
  $Data | ConvertTo-Json -Compress -Depth 6
}

function New-CommandId {
  $ms = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  $tail = [Guid]::NewGuid().ToString("N").Substring(0,8)
  return "$ms-$tail"
}

function Invoke-Bridge([string[]]$Fields) {
  $id = New-CommandId
  $responsePath = Join-Path $ResponsesDir "$id.tsv"
  $tmpPath = "$CommandPath.tmp.$id"

  foreach ($f in $Fields) {
    if ($null -eq $f) { continue }
    if ($f.Contains([char]9) -or $f.Contains([char]13) -or $f.Contains([char]10)) {
      throw "Bridge arguments cannot contain tabs or newlines."
    }
  }

  $line = (@($id) + $Fields) -join [char]9
  [IO.File]::WriteAllText($tmpPath, $line, [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmpPath -Destination $CommandPath -Force

  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.ElapsedMilliseconds -lt $TimeoutMs) {
    if (Test-Path -LiteralPath $responsePath) {
      $text = [IO.File]::ReadAllText($responsePath, [Text.Encoding]::UTF8).Trim()
      Remove-Item -LiteralPath $responsePath -Force -ErrorAction SilentlyContinue
      $parts = $text -split [char]9, 3
      if ($parts.Count -lt 2 -or $parts[0] -ne $id) {
        throw "Invalid bridge response: $text"
      }
      if ($parts[1] -ne "OK") {
        $detail = if ($parts.Count -ge 3) { $parts[2] } else { "unknown bridge error" }
        throw "BizHawk bridge error: $detail"
      }
      return $(if ($parts.Count -ge 3) { $parts[2] } else { "" })
    }
    Start-Sleep -Milliseconds 40
  }

  throw "Timed out waiting for BizHawk bridge. Is shinmomo_remote_bridge.lua loaded? LabDir=$LabDir"
}

switch ($Command) {
  "screen" {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    if ([string]::IsNullOrWhiteSpace($Out)) {
      $stamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
      $Out = Join-Path $ScreensDir "desktop_$stamp.png"
    }

    $bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $gfx = [System.Drawing.Graphics]::FromImage($bmp)
    try {
      $gfx.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0, $bmp.Size)
      $bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
    } finally {
      $gfx.Dispose()
      $bmp.Dispose()
    }

    Emit-Result @{ ok=$true; command="screen"; path=$Out; width=$bounds.Width; height=$bounds.Height }
  }

  "click" {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class ShinMomoMouse {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extraInfo);
}
"@
    $flags = @{
      left   = @(0x0002,0x0004)
      right  = @(0x0008,0x0010)
      middle = @(0x0020,0x0040)
    }[$Button]

    [ShinMomoMouse]::SetCursorPos($X,$Y) | Out-Null
    Start-Sleep -Milliseconds 40
    [ShinMomoMouse]::mouse_event([uint32]$flags[0],0,0,0,[UIntPtr]::Zero)
    Start-Sleep -Milliseconds 35
    [ShinMomoMouse]::mouse_event([uint32]$flags[1],0,0,0,[UIntPtr]::Zero)

    Emit-Result @{ ok=$true; command="click"; x=$X; y=$Y; button=$Button }
  }

  "key" {
    if ([string]::IsNullOrWhiteSpace($Keys)) { throw "-Keys is required for key." }
    if (-not [string]::IsNullOrWhiteSpace($WindowTitle)) {
      $shell = New-Object -ComObject WScript.Shell
      if (-not $shell.AppActivate($WindowTitle)) {
        throw "Window not found for AppActivate: $WindowTitle"
      }
      Start-Sleep -Milliseconds 120
    }
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.SendKeys]::SendWait($Keys)
    Emit-Result @{ ok=$true; command="key"; keys=$Keys; window=$WindowTitle }
  }

  "gamepad" {
    if ([string]::IsNullOrWhiteSpace($Buttons)) { throw "-Buttons is required for gamepad." }
    if ($Frames -lt 1 -or $Frames -gt 600) { throw "-Frames must be 1..600." }
    if ($Player -lt 1 -or $Player -gt 4) { throw "-Player must be 1..4." }

    $payload = Invoke-Bridge @("GAMEPAD", "$Player", $Buttons, "$Frames")
    Emit-Result @{ ok=$true; command="gamepad"; player=$Player; buttons=$Buttons; frames=$Frames; bridge=$payload }
  }

  "capture-memory" {
    if ($Length -lt 1 -or $Length -gt 4096) { throw "-Length must be 1..4096." }
    $payload = Invoke-Bridge @("CAPTURE_MEMORY", $Domain, $Start, "$Length")
    Emit-Result @{ ok=$true; command="capture-memory"; domain=$Domain; start=$Start; length=$Length; path=$payload }
  }
}
