param(
  [ValidatePattern('^[A-Za-z0-9_-]{1,64}$')][string]$BaseState='vmtrace_world_pack4c_x55_y236_preentry_20261011',
  [ValidatePattern('^[A-Za-z0-9_-]{1,64}$')][string]$OutputState='analysis_world_hien_dungeon91_ready_20261011',
  [ValidateRange(1,254)][int]$X=47,
  [ValidateRange(1,254)][int]$Y=200,
  [ValidateRange(1,99)][int]$Level=60,
  [ValidateRange(0,120)][int]$NeutralFrames=16
)
$ErrorActionPreference='Stop'
$bg=Join-Path $PSScriptRoot 'shinmomo_background_lab.ps1'
$client=Join-Path $PSScriptRoot 'shinmomo_lab.ps1'
$labdir=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab'
$status=& $bg -Action status|ConvertFrom-Json
if(!$status.ok -or !$status.running -or
   !@($status.windows).Count -or
   @($status.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){
  throw 'Dedicated hidden BizHawk not positively verified'
}
$base=Join-Path (Join-Path $labdir 'states') ($BaseState+'.State')
if(!(Test-Path -LiteralPath $base)){throw "Missing existing base savestate"}
$output=Join-Path (Join-Path $labdir 'states') ($OutputState+'.State')
if(Test-Path -LiteralPath $output){throw 'Refusing to overwrite existing analysis savestate'}
function ReadWRAM([string]$addr,[int]$len){
 $raw=& $bg -Action capture-memory -Domain WRAM -Start $addr -Length $len|ConvertFrom-Json
 if(!$raw.ok -or !(Test-Path -LiteralPath $raw.path)){throw "WRAM read failed at $addr"}
 return ,@((Get-Content -LiteralPath $raw.path -Raw -Encoding UTF8|ConvertFrom-Json).bytes)
}
function WriteWRAM([string]$addr,[string]$data){
 $r=& $client write-memory -LabDir $labdir -Domain WRAM -Start $addr -Data $data|ConvertFrom-Json
 if(!$r.ok){throw "WRAM write failed at $addr"}
}
$rollback='analysis_hienwarp_restore_'+(Get-Date -Format 'yyMMddHHmmss')+'_'+([guid]::NewGuid().ToString('N').Substring(0,6))
$save=& $bg -Action save-state -StateName $rollback|ConvertFrom-Json
if(!$save.ok -or !(Test-Path -LiteralPath $save.path)){throw 'Cannot protect original hidden emulator state'}
$errorText=$null
$verified=$null
$restored=$false
try{
 $loaded=& $bg -Action load-state -StateName $BaseState|ConvertFrom-Json
 if(!$loaded.ok){throw 'Unable to load analysis base save'}
 if((ReadWRAM '0x0305' 1)[0] -ne 76){throw 'Hien world/coordinate warp requires pack0x4C source'}
 $before=[ordered]@{
   level=(ReadWRAM '0x1623' 1)[0]
   destinations=ReadWRAM '0x1931' 4
   spells=ReadWRAM '0x44DA' 12
   world_x=(ReadWRAM '0x1573' 1)[0]
   world_y=(ReadWRAM '0x157D' 1)[0]
 }
 $spells=ReadWRAM '0x44DA' 12
 if($spells -notcontains 51){
   $empty=[array]::IndexOf($spells,0)
   if($empty -lt 0){throw 'Cannot enable Hien without empty Momotaro spell slot'}
   WriteWRAM ('0x{0:X4}' -f (0x44DA+$empty)) '0x33'
 }
 WriteWRAM '0x1623' ('0x{0:X2}' -f $Level)
 WriteWRAM '0x1931' '0xFF,0xFF,0xFF,0xFF'
 # Coordinate patch is a research cheat, NOT proof of traversable route.
 WriteWRAM '0x1573' ('0x{0:X2}' -f $X)
 WriteWRAM '0x157D' ('0x{0:X2}' -f $Y)
 $after=[ordered]@{
   level=(ReadWRAM '0x1623' 1)[0]
   destinations=ReadWRAM '0x1931' 4
   spells=ReadWRAM '0x44DA' 12
   world_x=(ReadWRAM '0x1573' 1)[0]
   world_y=(ReadWRAM '0x157D' 1)[0]
   current_pack=(ReadWRAM '0x0305' 1)[0]
 }
 if($after.level -ne $Level -or
    @($after.destinations|Where-Object{$_ -ne 255}).Count -ne 0 -or
    $after.spells -notcontains 51 -or $after.current_pack -ne 76 -or
    $after.world_x -ne $X -or $after.world_y -ne $Y){
   throw 'Hien/coordinate cheat readback not verified'
 }
 if($NeutralFrames -gt 0){
   $frame=& $bg -Action vm-frames -Frames $NeutralFrames|ConvertFrom-Json
   $doc=Get-Content -LiteralPath $frame.path -Raw -Encoding UTF8|ConvertFrom-Json
   if(!$frame.ok -or $doc.after.w0305 -ne 76 -or
      $doc.after.w1573 -ne $X -or $doc.after.w157d -ne $Y){
     throw 'Cheat-positioned world state not stable after neutral frames'
   }
 }
 $new=& $bg -Action save-state -StateName $OutputState|ConvertFrom-Json
 if(!$new.ok -or !(Test-Path -LiteralPath $new.path)){throw 'Cheat save not created'}
 $verified=[ordered]@{
   ok=$true
   kind='analysis_only_hien_unlocked_world_coordinate_warp'
   base_state=$BaseState
   analysis_state=$OutputState
   analysis_state_local_path=$new.path
   source_pack='0x4C'
   coordinate_patch_only=@('WRAM:1573','WRAM:157D')
   target_coordinate=@($X,$Y)
   hien_spell_id='0x33'
   all_hien_destinations_enabled=$true
   character_level=$Level
   neutral_stability_frames=$NeutralFrames
   normal_world_route_to_target_proven=$false
   actual_hien_menu_destinations_read=$false
   cheat_or_hien_used_for_next_travel='coordinate_warp'
   original_emulator_state_restored=$false
 }
}catch{
 $errorText=$_.Exception.Message
}finally{
 $back=& $bg -Action load-state -StateName $rollback|ConvertFrom-Json
 if(!$back.ok){throw 'CRITICAL: original BizHawk state restore failed'}
 $restored=$true
}
if($errorText){
 [ordered]@{
   ok=$false;error=$errorText;original_emulator_state_restored=$restored;
   source_unchanged=$true;new_graph_edges=0
 }|ConvertTo-Json -Compress -Depth 7
 return
}
$verified.original_emulator_state_restored=$restored
$verified|ConvertTo-Json -Compress -Depth 7
