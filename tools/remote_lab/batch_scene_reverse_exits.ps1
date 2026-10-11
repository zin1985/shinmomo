param(
    [ValidateRange(0,35)][int]$Start=0,
    [ValidateRange(1,12)][int]$Count=3,
    [ValidateSet('Down','Up','Left','Right')][string]$Direction='Down',
    [ValidateRange(8,180)][int]$InputFrames=72
)
$ErrorActionPreference='Stop'
$repo='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $repo 'tools\remote_lab\shinmomo_background_lab.ps1'
$local=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab'
$proof=Get-Content (Join-Path $repo 'data\maps\transitions\world_37_gamepad_entrances_after_cheat_20261011.json') -Raw -Encoding UTF8|ConvertFrom-Json
$packList=@('0x96','0x98','0x9E','0xBD','0xB9','0xAD','0xAB','0xA9','0x65','0x83','0x8E','0x6B','0x8C','0x5A','0x82','0x5F','0x60','0x87','0xB1','0x7A')
$selected=@()
foreach($pack in $packList){
 $entry=@($proof.entries|Where-Object{$_.destination_pack -eq $pack}|Select-Object -First 1)
 if($entry.Count){$selected+=$entry[0]}
}
if($Start -ge $selected.Count){throw 'Start outside target list'}
$pick=@($selected|Select-Object -Skip $Start -First $Count)
$status=& $lab -Action status|ConvertFrom-Json
if(!$status.ok -or !$status.running -or @($status.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){throw 'Dedicated hidden BizHawk required'}
$restoreName='reverse_entry_bulk_backup_'+(Get-Date -Format 'yyMMddHHmmss')+'_'+([guid]::NewGuid().ToString('N').Substring(0,6))
$backup=& $lab -Action save-state -StateName $restoreName|ConvertFrom-Json
if(!$backup.ok){throw 'Unable to protect dedicated state'}
$records=@()
$restored=$false
try{
 foreach($item in $pick){
  $pack=$item.destination_pack
  $stateName=('analysis_multi_world_'+$item.transition_id+'_p'+$pack.Substring(2)+'_20261011')
  $result=[ordered]@{
   source_world_transition_id=$item.transition_id
   source_map_pack=$pack
   source_config_id=$item.destination_config_id
   original_world_entrance_cheat_positioned=$true
   source_real_arrival_xy=@([int]$item.settled_arrival_xy.x,[int]$item.settled_arrival_xy.y)
   actual_test_controller=$Direction
   input_frames=$InputFrames
   raw_trace_hashes=@()
   result_status='not_started'
   map_switch_frame=$null
   destination_pack=$null
   destination_xy=$null
   stable_arrival_frame=$null
   screenshot_sha256=$null
   screenshot_path=$null
  }
  try{
   $load=& $lab -Action load-state -StateName $stateName|ConvertFrom-Json
   if(!$load.ok){throw 'Missing original pack destination capture state'}
   $settle=& $lab -Action vm-frames -Frames 12|ConvertFrom-Json
   $prep=Get-Content $settle.path -Raw -Encoding UTF8|ConvertFrom-Json
   if([int]$prep.after.w0305 -ne [convert]::ToInt32($pack.Substring(2),16)){throw 'Unexpected loaded pack'}
   $test=& $lab -Action vm-frames-gamepad -Buttons $Direction -Frames $InputFrames -Player 1|ConvertFrom-Json
   $live=Get-Content $test.path -Raw -Encoding UTF8|ConvertFrom-Json
   $idle=& $lab -Action vm-frames -Frames 120|ConvertFrom-Json
   $neutral=Get-Content $idle.path -Raw -Encoding UTF8|ConvertFrom-Json
   $result.raw_trace_hashes=@(
    (Get-FileHash -Algorithm SHA256 -LiteralPath $settle.path).Hash,
    (Get-FileHash -Algorithm SHA256 -LiteralPath $test.path).Hash,
    (Get-FileHash -Algorithm SHA256 -LiteralPath $idle.path).Hash
   )
   $changed=@($live.samples+$neutral.samples|Where-Object{$_.w0305 -ne [convert]::ToInt32($pack.Substring(2),16)})
   if($changed.Count -and ($neutral.after.w0305 -ne [convert]::ToInt32($pack.Substring(2),16))){
     $result.map_switch_frame=$changed[0].frame
     $finish=& $lab -Action vm-frames -Frames 120|ConvertFrom-Json
     $end=Get-Content $finish.path -Raw -Encoding UTF8|ConvertFrom-Json
     $result.raw_trace_hashes+=@( (Get-FileHash -Algorithm SHA256 -LiteralPath $finish.path).Hash )
     $result.destination_pack=('0x{0:X2}' -f [int]$end.after.w0305)
     $result.destination_xy=@([int]$end.after.w1573,[int]$end.after.w157d)
     $steady=@($end.samples|Where-Object{
      $_.w0305 -eq $end.after.w0305 -and $_.w1573 -eq $end.after.w1573 -and $_.w157d -eq $end.after.w157d
     })
     if($steady.Count -ge 8){
       $result.stable_arrival_frame=$steady[0].frame
       $result.result_status='observed_map_switch_stable_local_window'
     }else{
       $result.result_status='observed_map_switch_arrival_not_stable'
     }
     $pic=& $lab -Action screenshot|ConvertFrom-Json
     if($pic.ok -and (Test-Path -LiteralPath $pic.path)){
      $result.screenshot_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $pic.path).Hash
      $result.screenshot_path=$pic.path
     }
   }else{
     $result.result_status='no_scene_pack_change_in_probe_window'
     $result.destination_pack=('0x{0:X2}' -f [int]$neutral.after.w0305)
     $result.destination_xy=@([int]$neutral.after.w1573,[int]$neutral.after.w157d)
   }
  }catch{
   $result.result_status='test_error'
   $result.error=$_.Exception.Message
  }
  $records+=[pscustomobject]$result
  Write-Output ('PROBE '+$pack+' '+$Direction+' '+$result.result_status+' TO='+$result.destination_pack+' XY='+($result.destination_xy -join ','))
 }
}finally{
 $r=& $lab -Action load-state -StateName $restoreName|ConvertFrom-Json
 if(!$r.ok){throw 'CRITICAL: failed to restore original dedicated emulator state'}
 $restored=$true
}
$dir=Join-Path $local 'research'
New-Item -ItemType Directory -Path $dir -Force|Out-Null
$out=Join-Path $dir ('reverse_scene_batch_'+$Start+'_'+$Count+'_'+$Direction+'_20261011.json')
[ordered]@{
 schema_version=1
 kind='protected_original_scene_arrival_controller_exit_trials'
 source_original_world_entry_cheat_positioned=$true
 actual_reverse_test_no_xy_wram_edits=$true
 local_story_state_only=$true
 untouched_original_emulator_restored=$restored
 test_count=@($records).Count
 results=$records
}|ConvertTo-Json -Depth 7|Set-Content -LiteralPath $out -Encoding UTF8
Write-Output ('PROOF_FILE='+$out+' RESTORED='+$restored)
