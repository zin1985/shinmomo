param(
  [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_-]{1,64}$')][string]$BaseState,
  [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_-]{1,64}$')][string]$OutputState,
  [Parameter(Mandatory=$true)][ValidateRange(1,255)][int]$ExpectedPack,
  [Parameter(Mandatory=$true)][ValidateRange(1,254)][int]$X,
  [Parameter(Mandatory=$true)][ValidateRange(1,254)][int]$Y,
  [ValidateRange(0,60)][int]$NeutralFrames=16
)
$ErrorActionPreference='Stop'
$bg=Join-Path $PSScriptRoot 'shinmomo_background_lab.ps1'
$bridge=Join-Path $PSScriptRoot 'shinmomo_lab.ps1'
$dir=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab'
$before=& $bg -Action status |ConvertFrom-Json
if(!$before.ok -or !$before.running -or
   !@($before.windows).Count -or
   @($before.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){
  throw 'The dedicated emulator must be running with all windows hidden'
}
$base=Join-Path (Join-Path $dir 'states') ($BaseState+'.State')
$out=Join-Path (Join-Path $dir 'states') ($OutputState+'.State')
if(!(Test-Path -LiteralPath $base)){throw 'Known analysis source state missing'}
if(Test-Path -LiteralPath $out){throw 'Refusing to overwrite any existing state'}
function ReadByte([string]$addr){
  $r=& $bg -Action capture-memory -Domain WRAM -Start $addr -Length 1|ConvertFrom-Json
  if(!$r.ok -or !(Test-Path -LiteralPath $r.path)){throw 'Memory read failed'}
  return [int]((Get-Content -LiteralPath $r.path -Raw -Encoding UTF8|ConvertFrom-Json).bytes[0])
}
function WriteByte([string]$addr,[int]$value){
  $r=& $bridge write-memory -LabDir $dir -Domain WRAM -Start $addr -Data ('0x{0:X2}' -f $value)|ConvertFrom-Json
  if(!$r.ok){throw 'Protected analysis coordinate write failed'}
}
$rollback='isolated_scene_warp_rollback_'+(Get-Date -Format 'yyMMddHHmmss')+'_'+([guid]::NewGuid().ToString('N').Substring(0,6))
$save=& $bg -Action save-state -StateName $rollback|ConvertFrom-Json
if(!$save.ok -or !(Test-Path -LiteralPath $save.path)){throw 'Original isolated state backup failed'}
$errorInfo=$null
$answer=$null
$restored=$false
try {
 $loaded=& $bg -Action load-state -StateName $BaseState|ConvertFrom-Json
 if(!$loaded.ok){throw 'Scene source state cannot be loaded'}
 $sourcePack=ReadByte '0x0305'
 if($sourcePack -ne $ExpectedPack){throw 'Expected scene-pack assertion failed; no coordinate changes'}
 $fromX=ReadByte '0x1573'
 $fromY=ReadByte '0x157D'
 WriteByte '0x1573' $X
 WriteByte '0x157D' $Y
 if((ReadByte '0x0305') -ne $ExpectedPack -or
    (ReadByte '0x1573') -ne $X -or
    (ReadByte '0x157D') -ne $Y){throw 'Unstable/unverified analysis coordinates'}
 if($NeutralFrames -gt 0){
  $frames=& $bg -Action vm-frames -Frames $NeutralFrames|ConvertFrom-Json
  if(!$frames.ok){throw 'Cannot observe coordinate stability'}
  $j=Get-Content -LiteralPath $frames.path -Raw -Encoding UTF8|ConvertFrom-Json
  if($j.after.w0305 -ne $ExpectedPack -or
     $j.after.w1573 -ne $X -or $j.after.w157d -ne $Y){
    throw 'Requested scene position is not stable after neutral frames'
  }
 }
 $new=& $bg -Action save-state -StateName $OutputState|ConvertFrom-Json
 if(!$new.ok -or !(Test-Path -LiteralPath $new.path)){throw 'Could not save separate scene analysis state'}
 $answer=[ordered]@{
    ok=$true
    kind='analysis_cheat_scene_coordinate_warp_only'
    base_state=$BaseState
    new_state=$OutputState
    local_state_path=$new.path
    expected_scene_pack=$ExpectedPack
    original_position=@($fromX,$fromY)
    positioned_at=@($X,$Y)
    neutral_frames=$NeutralFrames
    only_wram_changed=@('0x1573','0x157D')
    normal_route_to_warp_position_proven=$false
    event_or_stair_trigger_proven=$false
    original_emulator_state_restored=$false
 }
}catch{
 $errorInfo=$_.Exception.Message
}finally{
 $r=& $bg -Action load-state -StateName $rollback|ConvertFrom-Json
 if(!$r.ok){throw 'CRITICAL: The previous emulator state could not be restored'}
 $restored=$true
}
if($errorInfo){
 [ordered]@{
    ok=$false;reason=$errorInfo;original_emulator_state_restored=$restored
    new_graph_edges=0
 }|ConvertTo-Json -Compress -Depth 7
 return
}
$answer.original_emulator_state_restored=$restored
$answer|ConvertTo-Json -Compress -Depth 7
