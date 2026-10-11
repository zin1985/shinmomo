param()
$ErrorActionPreference='Stop'
$repo='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $repo 'tools\remote_lab\shinmomo_background_lab.ps1'
$source='analysis_pack96_after_natural_down_39_24_20261011'
$research='analysis_pack96_title_dismissed_39_24_20261011'
$backup='pack96_postmodal_back_'+(Get-Date -Format 'yyMMddHHmmss')
$sys=& $lab -Action status|ConvertFrom-Json
if(!$sys.running -or @($sys.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){throw 'Not a protected hidden BizHawk'}
$save=& $lab -Action save-state -StateName $backup|ConvertFrom-Json
if(!$save.ok){throw 'Unable to protect original state'}
$records=@()
try{
 $l=& $lab -Action load-state -StateName $source|ConvertFrom-Json
 if(!$l.ok){throw 'Post-descend stage missing'}
 $dismiss=& $lab -Action vm-frames-gamepad -Buttons A -Frames 8 -Player 1|ConvertFrom-Json
 $settle=& $lab -Action vm-frames -Frames 64|ConvertFrom-Json
 $d=Get-Content $settle.path -Raw -Encoding UTF8|ConvertFrom-Json
 if($d.after.w0305 -ne 150 -or $d.after.w1573 -ne 39 -or $d.after.w157d -ne 24){throw 'Title-dismissed position wrong'}
 $sav=& $lab -Action save-state -StateName $research|ConvertFrom-Json
 if(!$sav.ok){throw 'Cannot save post-title research stage'}
 foreach($button in @('Left','Right','Up','Down')){
  $l=& $lab -Action load-state -StateName $research|ConvertFrom-Json
  if(!$l.ok){throw 'Trial scene load failed'}
  $a=& $lab -Action vm-frames-gamepad -Buttons $button -Frames 96 -Player 1|ConvertFrom-Json
  $z=& $lab -Action vm-frames -Frames 120|ConvertFrom-Json
  $doc=Get-Content $a.path -Raw -Encoding UTF8|ConvertFrom-Json
  $end=Get-Content $z.path -Raw -Encoding UTF8|ConvertFrom-Json
  $pic=& $lab -Action screenshot|ConvertFrom-Json
  $record=[ordered]@{
   button=$button;source_pack=$doc.before.w0305
   source_xy=@($doc.before.w1573,$doc.before.w157d)
   pad_end_pack=$doc.after.w0305
   pad_end_xy=@($doc.after.w1573,$doc.after.w157d)
   settled_pack=$end.after.w0305
   settled_xy=@($end.after.w1573,$end.after.w157d)
   gamepad_sha256=(Get-FileHash -LiteralPath $a.path -Algorithm SHA256).Hash
   neutral_sha256=(Get-FileHash -LiteralPath $z.path -Algorithm SHA256).Hash
   screenshot_path=$pic.path
   screenshot_sha256=(Get-FileHash -LiteralPath $pic.path -Algorithm SHA256).Hash
  }
  $records+=,[pscustomobject]$record
  Write-Output ($record|ConvertTo-Json -Compress -Depth 4)
 }
}finally{
 $reset=& $lab -Action load-state -StateName $backup|ConvertFrom-Json
 if(!$reset.ok){throw 'CRITICAL: restore original lab failed'}
 Write-Output 'RESTORED=True'
}
$dir=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab\research'
$out=Join-Path $dir 'pack96_post_title_dismissed_four_directions_20261011.json'
[ordered]@{schema_version=1;kind='isolated_pack96_four_directions_after_title_dismissed';
 original_world_entrance_coordinate_cheat_used=$true
 no_xy_coordinate_cheat_during_probe=$true
 title_dismissed_with_real_A_button=$true
 original_emulator_state_restored=$true
 result_count=@($records).Count
 results=$records
}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $out -Encoding UTF8
Write-Output ('PROOF_FILE='+$out)
