param(
 [ValidateRange(0,2)][int]$Start=0,
 [ValidateRange(1,3)][int]$Count=1,
 [ValidateRange(24,96)][int]$StepFrames=72
)
$ErrorActionPreference='Stop'
$repo='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $repo 'tools\remote_lab\shinmomo_background_lab.ps1'
$pk=@('BD','B9','AB')
if($Start+$Count -gt $pk.Count){throw 'Requested region outside known dungeon packs'}
$sequences=@(
 @('Up','Left','Up'),
 @('Up','Right','Up'),
 @('Down','Left','Down'),
 @('Down','Right','Down'),
 @('Left','Down','Left'),
 @('Right','Down','Right'),
 @('Left','Up','Left'),
 @('Right','Up','Right')
)
$status=& $lab -Action status|ConvertFrom-Json
if(!$status.ok -or !$status.running -or @($status.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){throw 'Only the hidden dedicated BizHawk is permitted'}
$backup='dungeon_branch_backup_'+(Get-Date -Format 'yyMMddHHmmss')+'_'+([guid]::NewGuid().ToString('N').Substring(0,6))
$b=& $lab -Action save-state -StateName $backup|ConvertFrom-Json
if(!$b.ok){throw 'Could not protect original emulator'}
$all=@();$restored=$false
try{
 foreach($pack in @($pk|Select-Object -Skip $Start -First $Count)){
  $source='scene_modal5_'+$pack+'_post_A_20261011'
  $expect=[Convert]::ToInt32($pack,16)
  foreach($i in 0..($sequences.Count-1)){
   $load=& $lab -Action load-state -StateName $source|ConvertFrom-Json
   if(!$load.ok){throw ('Missing exact verified post-A source '+$source)}
   $obs=@()
   $phase='same_scene'
   foreach($button in $sequences[$i]){
     $move=& $lab -Action vm-frames-gamepad -Buttons $button -Frames $StepFrames -Player 1|ConvertFrom-Json
     if(!$move.ok){throw 'Gamepad route step failed'}
     $m=Get-Content -LiteralPath $move.path -Raw -Encoding UTF8|ConvertFrom-Json
     $obs+=,[pscustomobject]@{
      button=$button;frames=$StepFrames;first_frame=$m.before.frame;last_frame=$m.after.frame
      source_pack=('0x{0:X2}' -f [int]$m.before.w0305)
      source_xy=@([int]$m.before.w1573,[int]$m.before.w157d)
      destination_pack=('0x{0:X2}' -f [int]$m.after.w0305)
      destination_xy=@([int]$m.after.w1573,[int]$m.after.w157d)
      raw_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $move.path).Hash
     }
     if($m.after.w0305 -ne $expect){
       $phase='pack_changed'
       break
     }
   }
   $neutral=& $lab -Action vm-frames -Frames 120|ConvertFrom-Json
   $n=Get-Content -LiteralPath $neutral.path -Raw -Encoding UTF8|ConvertFrom-Json
   $pic=& $lab -Action screenshot|ConvertFrom-Json
   $row=[pscustomobject]@{
     original_scene_pack=('0x'+$pack)
     original_source_state=$source
     route_index=$i
     route_buttons=@($sequences[$i])
     raw_steps=$obs
     first_frame=$obs[0].first_frame
     neutral120_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $neutral.path).Hash
     neutral120_frame_begin=$n.before.frame;neutral120_frame_end=$n.after.frame
     neutral120_after_pack=('0x{0:X2}' -f [int]$n.after.w0305)
     neutral120_after_xy=@([int]$n.after.w1573,[int]$n.after.w157d)
     status=$phase
     screenshot_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $pic.path).Hash
     screenshot_path=$pic.path
   }
   $all+=,$row
   Write-Output ('PACK=0x'+$pack+' ROUTE='+$i+' '+($sequences[$i] -join '>')+' FINAL='+$row.neutral120_after_pack+':'+($row.neutral120_after_xy -join ',')+' STATUS='+$phase)
  }
 }
}finally{
 $reset=& $lab -Action load-state -StateName $backup|ConvertFrom-Json
 if(!$reset.ok){throw 'CRITICAL: original emulator state restoration failed'}
 $restored=$true
}
$dir=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab\research'
$file=Join-Path $dir ('dungeon_branch_8x_'+$Start+'_'+$Count+'_20261011.json')
[ordered]@{
 schema_version=1;kind='three_dungeons_genuine_controller_branch_path_probes'
 world_entrance_initially_cheat_positioned=$true
 scene_probe_wram_XY_cheat_used=$false
 original_hidden_emulator_restored=$restored
 directions_each_segment=$StepFrames
 exact_post_A_scene_source_state_used=$true
 start_index=$Start;count=$Count;results=$all
}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $file -Encoding UTF8
Write-Output ('PROOF_FILE='+$file+' RESTORED='+$restored)
