param([ValidateRange(4,48)][int]$Presses=24)
$ErrorActionPreference='Stop'
$p='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $p 'tools\remote_lab\shinmomo_background_lab.ps1'
$source='village_dialogue_60_after_12_A_20261011'
$state='pack60_dialogue_continuation_after_'+$Presses+'_A_20261011'
$labStatus=& $lab -Action status|ConvertFrom-Json
if(!$labStatus.ok -or !$labStatus.running -or @($labStatus.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){throw 'Only hidden isolated lab'}
$backup='pack60_ext_backup_'+(Get-Date -Format 'yyMMddHHmmss')+'_'+([guid]::NewGuid().ToString('N').Substring(0,5))
$b=& $lab -Action save-state -StateName $backup|ConvertFrom-Json
if(!$b.ok){throw 'Cannot protect current user state'}
$history=@();$restored=$false
try{
 $load=& $lab -Action load-state -StateName $source|ConvertFrom-Json
 if(!$load.ok){throw 'After A12 pack0x60 source unavailable'}
 $first=& $lab -Action vm-frames -Frames 12|ConvertFrom-Json
 $d=Get-Content $first.path -Raw -Encoding UTF8|ConvertFrom-Json
 if($d.after.w0305 -ne 96 -or $d.after.w1573 -ne 37 -or $d.after.w157d -ne 56){throw 'Source scene mismatch'}
 $pic=& $lab -Action screenshot|ConvertFrom-Json
 $history+=,[pscustomobject]@{
   index=0;button='neutral12';pack=('0x{0:X2}' -f [int]$d.after.w0305)
   xy=@([int]$d.after.w1573,[int]$d.after.w157d);frame=$d.after.frame
   frame_sha256=(Get-FileHash $first.path -Algorithm SHA256).Hash
   screenshot_sha256=(Get-FileHash $pic.path -Algorithm SHA256).Hash
   screenshot_path=$pic.path
 }
 foreach($i in 1..$Presses){
  $a=& $lab -Action vm-frames-gamepad -Buttons A -Frames 8 -Player 1|ConvertFrom-Json
  $n=& $lab -Action vm-frames -Frames 20|ConvertFrom-Json
  if(!$a.ok -or !$n.ok){throw 'Dialogue controller input failed'}
  $doc=Get-Content $n.path -Raw -Encoding UTF8|ConvertFrom-Json
  $pic=& $lab -Action screenshot|ConvertFrom-Json
  $history+=,[pscustomobject]@{
    index=$i;button='A8_then_neutral20'
    pack=('0x{0:X2}' -f [int]$doc.after.w0305)
    xy=@([int]$doc.after.w1573,[int]$doc.after.w157d)
    frame=$doc.after.frame
    gamepad_sha256=(Get-FileHash $a.path -Algorithm SHA256).Hash
    neutral_sha256=(Get-FileHash $n.path -Algorithm SHA256).Hash
    screenshot_sha256=(Get-FileHash $pic.path -Algorithm SHA256).Hash
    screenshot_path=$pic.path
  }
  Write-Output ('A_AFTER_12_'+$i+' PACK='+$history[-1].pack+' XY='+($history[-1].xy -join ',')+' SCREEN='+$history[-1].screenshot_sha256)
 }
 $save=& $lab -Action save-state -StateName $state|ConvertFrom-Json
 if(!$save.ok){throw 'Unable to keep research stage'}
 foreach($button in @('Down','Up','Left','Right')){
   $r=& $lab -Action load-state -StateName $state|ConvertFrom-Json
   if(!$r.ok){throw 'Cannot reload scene stage'}
   $a=& $lab -Action vm-frames-gamepad -Buttons $button -Frames 96 -Player 1|ConvertFrom-Json
   $b=& $lab -Action vm-frames -Frames 120|ConvertFrom-Json
   $d=Get-Content $a.path -Raw -Encoding UTF8|ConvertFrom-Json
   $e=Get-Content $b.path -Raw -Encoding UTF8|ConvertFrom-Json
   $pic=& $lab -Action screenshot|ConvertFrom-Json
   $history+=,[pscustomobject]@{
     index=$Presses+1;button=$button
     pack=('0x{0:X2}' -f [int]$e.after.w0305)
     xy=@([int]$e.after.w1573,[int]$e.after.w157d)
     frame=$e.after.frame
     gamepad_sha256=(Get-FileHash $a.path -Algorithm SHA256).Hash
     neutral_sha256=(Get-FileHash $b.path -Algorithm SHA256).Hash
     screenshot_sha256=(Get-FileHash $pic.path -Algorithm SHA256).Hash
     screenshot_path=$pic.path
   }
   Write-Output ('WALK_AFTER_'+$Presses+'_ADDITIONAL_A '+$button+' -> '+$history[-1].pack+':'+($history[-1].xy -join ','))
 }
}finally{
 $r=& $lab -Action load-state -StateName $backup|ConvertFrom-Json
 if(!$r.ok){throw 'CRITICAL: hidden emulator restore failed'}
 $restored=$true
}
$dir=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab\research'
$file=Join-Path $dir ('pack60_A12_plus_'+$Presses+'_A_and_four_directions_20261011.json')
[ordered]@{
 schema_version=1;kind='pack60_dialogue_extended_then_four_real_controller_directions'
 source_after_original_A12=$source
 original_world_entrance_cheat_seeded=$true
 no_coordinate_wram_cheat_in_scene=$true
 dedicated_emulator_restored=$restored
 additional_real_A_presses=$Presses
 raw_captures_not_committed=$true
 history=$history
}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $file -Encoding UTF8
Write-Output ('PROOF_FILE='+$file+' RESTORED='+$restored)
