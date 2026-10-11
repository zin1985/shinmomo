param(
 [ValidateRange(0,4)][int]$Start=0,
 [ValidateRange(1,5)][int]$Count=2,
 [ValidateRange(24,180)][int]$DirectionalFrames=96
)
$ErrorActionPreference='Stop'
$repo='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $repo 'tools\remote_lab\shinmomo_background_lab.ps1'
$local=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab'
$ledger=Get-Content (Join-Path $repo 'data\maps\transitions\world_37_gamepad_entrances_after_cheat_20261011.json') -Raw -Encoding UTF8|ConvertFrom-Json
$targets=@('0xBD','0xB9','0xAB','0x82','0x60')
if($Start+$Count -gt $targets.Count){throw 'Requested batch overflows exact target list'}
$status=& $lab -Action status|ConvertFrom-Json
if(!$status.ok -or !$status.running -or @($status.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){throw 'Only dedicated hidden BizHawk instance is allowed'}
$backup='scene_modal5_original_'+(Get-Date -Format 'yyMMddHHmmss')+'_'+[guid]::NewGuid().ToString('N').Substring(0,5)
$b=& $lab -Action save-state -StateName $backup|ConvertFrom-Json
if(!$b.ok){throw 'Unable to protect dedicated emulator state'}
$records=@();$restored=$false
try{
 foreach($pack in @($targets|Select-Object -Skip $Start -First $Count)){
  $e=@($ledger.entries|Where-Object{$_.destination_pack -eq $pack}|Select-Object -First 1)
  if($e.Count -ne 1){throw "Unexpected source entry count for $pack"}
  $entry=$e[0]
  $source='analysis_multi_world_'+$entry.transition_id+'_p'+$pack.Substring(2)+'_20261011'
  $data=[ordered]@{
   pack=$pack;source_transition_id=$entry.transition_id
   source_config_id=$entry.destination_config_id
   original_world_entry_was_cheat_seeded=$true
   no_xy_Wram_writes_inside_these_trials=$true
   saved_source_arrival_xy=@([int]$entry.settled_arrival_xy.x,[int]$entry.settled_arrival_xy.y)
   initial_screenshot_path=$null;initial_screenshot_sha256=$null
   before_A_pack=$null;before_A_xy=$null
   after_A_pack=$null;after_A_xy=$null
   A_trace_sha256=$null;post_A_neutral_sha256=$null
   A_dismissed_screenshot_path=$null;A_dismissed_screenshot_sha256=$null
   directions=@();result_status='started'
  }
  try{
   $l=& $lab -Action load-state -StateName $source|ConvertFrom-Json
   if(!$l.ok){throw 'Exact original destination state cannot be loaded'}
   $settle=& $lab -Action vm-frames -Frames 12|ConvertFrom-Json
   $before=Get-Content $settle.path -Raw -Encoding UTF8|ConvertFrom-Json
   $data.before_A_pack=('0x{0:X2}' -f [int]$before.after.w0305)
   $data.before_A_xy=@([int]$before.after.w1573,[int]$before.after.w157d)
   if($data.before_A_pack -ne $pack){throw 'Source savestate not on expected scene pack'}
   $shot=& $lab -Action screenshot|ConvertFrom-Json
   if(!$shot.ok){throw 'Original scene image capture missing'}
   $data.initial_screenshot_path=$shot.path
   $data.initial_screenshot_sha256=(Get-FileHash -LiteralPath $shot.path -Algorithm SHA256).Hash
   $press=& $lab -Action vm-frames-gamepad -Buttons A -Frames 8 -Player 1|ConvertFrom-Json
   $neutral=& $lab -Action vm-frames -Frames 64|ConvertFrom-Json
   $end=Get-Content $neutral.path -Raw -Encoding UTF8|ConvertFrom-Json
   $data.A_trace_sha256=(Get-FileHash -LiteralPath $press.path -Algorithm SHA256).Hash
   $data.post_A_neutral_sha256=(Get-FileHash -LiteralPath $neutral.path -Algorithm SHA256).Hash
   $data.after_A_pack=('0x{0:X2}' -f [int]$end.after.w0305)
   $data.after_A_xy=@([int]$end.after.w1573,[int]$end.after.w157d)
   $shot=& $lab -Action screenshot|ConvertFrom-Json
   if(!$shot.ok){throw 'Post A image not obtained'}
   $data.A_dismissed_screenshot_path=$shot.path
   $data.A_dismissed_screenshot_sha256=(Get-FileHash -LiteralPath $shot.path -Algorithm SHA256).Hash
   $sceneName='scene_modal5_'+$pack.Substring(2)+'_post_A_20261011'
   $sav=& $lab -Action save-state -StateName $sceneName|ConvertFrom-Json
   if(!$sav.ok){throw 'Failed to protect exact post-A scene'}
   foreach($dir in @('Down','Up','Left','Right')){
    $l=& $lab -Action load-state -StateName $sceneName|ConvertFrom-Json
    if(!$l.ok){throw 'Cannot load post-A savestate'}
    $pad=& $lab -Action vm-frames-gamepad -Buttons $dir -Frames $DirectionalFrames -Player 1|ConvertFrom-Json
    $wait=& $lab -Action vm-frames -Frames 120|ConvertFrom-Json
    if(!$pad.ok -or !$wait.ok){throw 'Gamepad/neutral frame probe failed'}
    $first=Get-Content $pad.path -Raw -Encoding UTF8|ConvertFrom-Json
    $last=Get-Content $wait.path -Raw -Encoding UTF8|ConvertFrom-Json
    $extra=$null
    if($last.after.w0305 -ne [convert]::ToInt32($data.after_A_pack.Substring(2),16)){
      $long=& $lab -Action vm-frames -Frames 240|ConvertFrom-Json
      $extra=Get-Content $long.path -Raw -Encoding UTF8|ConvertFrom-Json
    }
    $shot=& $lab -Action screenshot|ConvertFrom-Json
    $data.directions+=,[pscustomobject]@{
      direction=$dir;input_frames=$DirectionalFrames;neutral_frames=120
      after_transition_neutral_extra_frames=$(if($extra){240}else{0})
      initial_pack=('0x{0:X2}' -f [int]$first.before.w0305)
      initial_xy=@([int]$first.before.w1573,[int]$first.before.w157d)
      after_gamepad_pack=('0x{0:X2}' -f [int]$first.after.w0305)
      after_gamepad_xy=@([int]$first.after.w1573,[int]$first.after.w157d)
      after_neutral_pack=('0x{0:X2}' -f [int]$last.after.w0305)
      after_neutral_xy=@([int]$last.after.w1573,[int]$last.after.w157d)
      final_pack=('0x{0:X2}' -f [int]$(if($extra){$extra.after.w0305}else{$last.after.w0305}))
      final_xy=@([int]$(if($extra){$extra.after.w1573}else{$last.after.w1573}),[int]$(if($extra){$extra.after.w157d}else{$last.after.w157d}))
      gamepad_capture_sha256=(Get-FileHash -LiteralPath $pad.path -Algorithm SHA256).Hash
      neutral_capture_sha256=(Get-FileHash -LiteralPath $wait.path -Algorithm SHA256).Hash
      extra_capture_sha256=$(if($extra){(Get-FileHash -LiteralPath $long.path -Algorithm SHA256).Hash}else{$null})
      screenshot_path=$shot.path
      screenshot_sha256=(Get-FileHash -LiteralPath $shot.path -Algorithm SHA256).Hash
    }
    $lastDirection=$data.directions[-1]
    Write-Output ('PACK='+$pack+' DIR='+$dir+' AFTER_A='+$data.after_A_pack+':'+($data.after_A_xy -join ',')+' FINAL='+$lastDirection.final_pack+':'+($lastDirection.final_xy -join ','))
   }
   $data.result_status='completed'
  }catch{
   $data.result_status='probe_error';$data.error=$_.Exception.Message
   Write-Output ('ERROR pack='+$pack+' '+$data.error)
  }
  $records+=,[pscustomobject]$data
 }
}finally{
 $reset=& $lab -Action load-state -StateName $backup|ConvertFrom-Json
 if(!$reset.ok){throw 'CRITICAL: Failed to restore protected original emulator state'}
 $restored=$true
}
$dir=Join-Path $local 'research'
New-Item -ItemType Directory -Path $dir -Force|Out-Null
$file=Join-Path $dir ('scene_modal5_A8_directional_'+$Start+'_'+$Count+'_20261011.json')
[ordered]@{
 schema_version=1;kind='five_scenes_title_modal_A8_controller_probes'
 original_world_entry_coordinate_cheat_seeded=$true
 controller_probe_XY_coordinate_cheat_used=$false
 original_hidden_emulator_state_restored=$restored
 isolated_dedicated_hidden_bizhawk_used=$true
 requested_count=$Count;start_index=$Start;results=$records
}|ConvertTo-Json -Depth 9|Set-Content -LiteralPath $file -Encoding UTF8
Write-Output ('PROOF_FILE='+$file+' RESTORED='+$restored)
