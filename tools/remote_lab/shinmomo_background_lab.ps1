param(
  [ValidateSet('start','status','hide','show','screenshot','step','gamepad','capture-memory','map-capture','save-state','load-state','stop')]
  [string]$Action='status',
  [string]$LabDir='', [string]$Rom='', [string]$BizHawkRoot='',
  [int]$Frames=1, [string]$Buttons='A', [int]$Player=1,
  [string]$Domain='WRAM',[string]$Start='0x0305',[int]$Length=32,
  [string]$SceneTag='background', [string]$StateName='background'
)
$ErrorActionPreference='Stop'
if (!$LabDir) { $LabDir=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab' }
if (!$Rom) { $Rom=Join-Path $env:USERPROFILE 'Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc' }
if (!$BizHawkRoot) { $BizHawkRoot=Join-Path $env:USERPROFILE 'Downloads\BizHawk-2.11-win-x64' }
$registrationPath=Join-Path $LabDir 'background_lab_process.json'
$client=Join-Path $PSScriptRoot 'shinmomo_lab.ps1'
$lua=Join-Path $PSScriptRoot 'shinmomo_remote_bridge.lua'
$expected='F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98'
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Text;
using System.Runtime.InteropServices;
public static class ShinMomoBgWin {
  public delegate bool Callback(IntPtr hwnd, IntPtr lparam);
  [DllImport("user32.dll")] public static extern bool EnumWindows(Callback cb, IntPtr data);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint processId);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hwnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hwnd, int cmd);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hwnd, StringBuilder title, int len);
  public static string[] Apply(int targetPid, int mode) {
    var result = new List<string>();
    EnumWindows((hwnd, unused) => {
      uint pid; GetWindowThreadProcessId(hwnd, out pid);
      if (pid != (uint)targetPid) return true;
      var title = new StringBuilder(256); GetWindowText(hwnd,title,title.Capacity);
      string name=title.ToString();
      if (name.IndexOf("BizHawk",StringComparison.OrdinalIgnoreCase)<0 && name!="Lua Console") return true;
      bool visible=IsWindowVisible(hwnd);
      if (mode==0 && visible) ShowWindow(hwnd,0);
      else if(mode==1 && !visible) ShowWindow(hwnd,9);
      result.Add(name + " | visible=" + IsWindowVisible(hwnd));
      return true;
    }, IntPtr.Zero);
    return result.ToArray();
  }
}
'@ -ErrorAction Stop
function Out-Json($obj) { $obj | ConvertTo-Json -Compress -Depth 7 }
function Get-Registered {
  if (!(Test-Path -LiteralPath $registrationPath)) { return $null }
  $registration=Get-Content -LiteralPath $registrationPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$($registration.pid)"
  if (!$proc) { return $null }
  if ($proc.Name -ne 'EmuHawk.exe' -or !([string]$proc.CommandLine).Contains([string]$registration.config) -or !([string]$proc.CommandLine).Contains([string]$registration.rom) -or !([string]$proc.CommandLine).Contains([string]$registration.lua)) {
    throw 'Registered PID does not match the dedicated BizHawk process. Refusing to operate.'
  }
  return $proc
}
function Call-Lab([string]$subcommand,[hashtable]$argsMap) {
  $result=& $client $subcommand -LabDir $LabDir -TimeoutMs 15000 @argsMap
  if (!$result) { throw 'No response from BizHawk bridge.' }
  return ($result | ConvertFrom-Json -ErrorAction Stop)
}
$proc=Get-Registered
if ($Action -notin @('start','status') -and !$proc) { throw 'Dedicated BizHawk not running. Run -Action start.' }
switch($Action) {
  'start' {
    if ($proc) {
      [void][ShinMomoBgWin]::Apply([int]$proc.ProcessId,0)
      Out-Json @{ok=$true;action='start';already_running=$true;pid=[int]$proc.ProcessId;hidden=$true;lab=$LabDir}
      break
    }
    $exe=Join-Path $BizHawkRoot 'EmuHawk.exe'
    $sourceConfig=Join-Path $BizHawkRoot 'config.ini'
    if (!(Test-Path $exe) -or !(Test-Path $sourceConfig) -or !(Test-Path $lua) -or !(Test-Path $client)) { throw 'BizHawk, config or bridge is missing.' }
    if (!(Test-Path $Rom) -or (Get-Item $Rom).Length -ne 2097152 -or (Get-FileHash $Rom -Algorithm SHA256).Hash -ne $expected) { throw 'Canonical ROM size/hash failed.' }
    foreach($dir in @($LabDir,(Join-Path $LabDir 'screens'),(Join-Path $LabDir 'responses'),(Join-Path $LabDir 'captures'),(Join-Path $LabDir 'states'))) {New-Item -ItemType Directory -Path $dir -Force | Out-Null}
    if (Test-Path (Join-Path $LabDir 'command.tsv')) { throw 'Stale mailbox exists; inspect before launch.' }
    $configPath=Join-Path $LabDir 'config.ini'
    $config=[IO.File]::ReadAllText($sourceConfig,[Text.Encoding]::UTF8)
    $config=[regex]::Replace($config,'"Unthrottled"\s*:\s*(true|false)','"Unthrottled": true')
    $config=[regex]::Replace($config,'"SoundOutputMethod"\s*:\s*\d+','"SoundOutputMethod": 3')
    $config=[regex]::Replace($config,'"SoundEnabled(?:Normal|RWFF)?"\s*:\s*(true|false)',{param($m) ($m.Value -replace '(true|false)$','false')})
    [IO.File]::WriteAllText($configPath,$config,[Text.UTF8Encoding]::new($false))
    $oldEnv=[Environment]::GetEnvironmentVariable('SHINMOMO_LAB_DIR','Process')
    try {
      $env:SHINMOMO_LAB_DIR=$LabDir
      $argsExe=@(('--config="'+$configPath+'"'),('--lua="'+$lua+'"'),('"'+$Rom+'"'))
      $created=Start-Process -FilePath $exe -ArgumentList $argsExe -WorkingDirectory $BizHawkRoot -WindowStyle Minimized -PassThru
    } finally { [Environment]::SetEnvironmentVariable('SHINMOMO_LAB_DIR',$oldEnv,'Process') }
    @{pid=$created.Id;rom=$Rom;config=$configPath;lua=$lua;created=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $registrationPath -Encoding UTF8
    $deadline=[Diagnostics.Stopwatch]::StartNew()
    $ready=$false
    while($deadline.ElapsedMilliseconds -lt 12000) {
      if (!(Get-Process -Id $created.Id -ErrorAction SilentlyContinue)) {throw 'BizHawk exited during startup.'}
      $windows=@([ShinMomoBgWin]::Apply([int]$created.Id,0))
      if (@($windows | Where-Object {$_ -like '*BizHawk*'}).Count -gt 0 -and @($windows | Where-Object {$_ -like '*Lua Console*'}).Count -gt 0) { $ready=$true;break }
      Start-Sleep -Milliseconds 150
    }
    if (!$ready) { throw 'BizHawk/Lua Console did not both initialize.' }
    Out-Json @{ok=$true;action='start';pid=$created.Id;hidden=$true;lab=$LabDir;rom_verified=$true}
  }
  'status' {Out-Json @{ok=$true;action='status';running=[bool]$proc;pid=$(if($proc){[int]$proc.ProcessId}else{$null});lab=$LabDir;windows=$(if($proc){@([ShinMomoBgWin]::Apply([int]$proc.ProcessId,-1))}else{@()})}}
  'hide' {Out-Json @{ok=$true;action='hide';windows=@([ShinMomoBgWin]::Apply([int]$proc.ProcessId,0))}}
  'show' {Out-Json @{ok=$true;action='show';windows=@([ShinMomoBgWin]::Apply([int]$proc.ProcessId,1))}}
  'screenshot' {
    $r=Call-Lab 'game-screen' @{}
    if (!(Test-Path -LiteralPath $r.path)) {throw 'Screenshot not found.'}
    $f=Get-Item -LiteralPath $r.path
    if($f.Length -lt 100){throw 'Screenshot file too small.'}
    Out-Json @{ok=$true;action='screenshot';path=$f.FullName;bytes=$f.Length;sha256=(Get-FileHash $f.FullName -Algorithm SHA256).Hash}
  }
  'step' {
    if($Frames -lt 1 -or $Frames -gt 600){throw 'Frames must be 1..600.'}
    Out-Json (Call-Lab 'step' @{ Frames = $Frames })
  }
  'gamepad' {
    if($Frames -lt 1 -or $Frames -gt 600 -or $Player -lt 1 -or $Player -gt 4){throw 'Frames 1..600 and player 1..4 required.'}
    if($Buttons -notmatch '^[A-Za-z0-9,+ -]+$'){throw 'Invalid buttons.'}
    Out-Json (Call-Lab 'gamepad' @{ Buttons = $Buttons; Frames = $Frames; Player = $Player })
  }
  'capture-memory' {
    if($Length -lt 1 -or $Length -gt 4096){throw 'Length must be 1..4096.'}
    Out-Json (Call-Lab 'capture-memory' @{ Domain = $Domain; Start = $Start; Length = $Length })
  }
  'map-capture' {Out-Json (Call-Lab 'map-capture' @{ SceneTag = $SceneTag })}
  'save-state' {
    if($StateName -notmatch '^[A-Za-z0-9_-]{1,64}$') {throw 'Invalid state name.'}
    Out-Json (Call-Lab 'save-state' @{ StateName = $StateName })
  }
  'load-state' {
    if($StateName -notmatch '^[A-Za-z0-9_-]{1,64}$') {throw 'Invalid state name.'}
    Out-Json (Call-Lab 'load-state' @{ StateName = $StateName })
  }
  'stop' {
    Stop-Process -Id ([int]$proc.ProcessId) -Force
    Remove-Item -LiteralPath $registrationPath -Force -ErrorAction SilentlyContinue
    Out-Json @{ok=$true;action='stop';stopped_pid=[int]$proc.ProcessId;note='ROM and runtime captures preserved'}
  }
}
