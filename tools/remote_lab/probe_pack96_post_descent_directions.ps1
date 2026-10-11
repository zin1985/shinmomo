param()
$ErrorActionPreference='Stop'
$repo='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $repo 'tools\remote_lab\shinmomo_background_lab.ps1'
$origin='analysis_multi_world_catalog_transition_0756_p96_20261011'
$target='analysis_pack96_after_natural_down_39_24_20261011'
$s=& $lab -Action status|ConvertFrom-Json
if(!$s.running -or @($s.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){throw 'Hidden emulator only'}
$backup='pack96_autodown_test_backup_'+(Get-Date -Format 'yyMMddHHmmss')
$b=& $lab -Action save-state -StateName $backup|ConvertFrom-Json
if(!$b.ok){throw 'Cannot protect original'}
$log=@()
try{
 $l=& $lab -Action load-state -StateName $origin|ConvertFrom-Json
 if(!$l.ok){throw 'Source pack96 missing'}
 $n1=& $lab -Action vm-frames -Frames 120|ConvertFrom-Json
 $n2=& $lab -Action vm-frames -Frames 120|ConvertFrom-Json
 $d=Get-Content $n2.path -Raw -Encoding UTF8|ConvertFrom-Json
 if($d.after.w0305 -ne 150 -or $d.after.w1573 -ne 39 -or $d.after.w157d -ne 24){throw 'Exact 0x96 descent completion did not settle'}
 $save=& $lab -Action save-state -StateName $target|ConvertFrom-Json
 if(!$save.ok){throw 'Cannot save post-descent research fixture'}
 $pic=& $lab -Action screenshot|ConvertFrom-Json
 $log+=('FIXTURE='+$target+' SCREEN='+$pic.path)
 foreach($direction in @('Left','Right','Up','Down')){
  $fresh=& $lab -Action load-state -StateName $target|ConvertFrom-Json
  if(!$fresh.ok){throw 'Post-descent fixture could not be reloaded'}
  $g=& $lab -Action vm-frames-gamepad -Buttons $direction -Frames 96 -Player 1|ConvertFrom-Json
  $n=& $lab -Action vm-frames -Frames 120|ConvertFrom-Json
  if(!$g.ok -or !$n.ok){throw 'Gamepad or neutral capture failed'}
  $one=Get-Content $g.path -Raw -Encoding UTF8|ConvertFrom-Json
  $two=Get-Content $n.path -Raw -Encoding UTF8|ConvertFrom-Json
  $entry=[ordered]@{
   direction=$direction
   start_frame=$one.before.frame
   start_pack=$one.before.w0305
   start_xy=@($one.before.w1573,$one.before.w157d)
   post_pad_pack=$one.after.w0305
   post_pad_xy=@($one.after.w1573,$one.after.w157d)
   after_neutral_pack=$two.after.w0305
   after_neutral_xy=@($two.after.w1573,$two.after.w157d)
   input_capture_sha256=(Get-FileHash -LiteralPath $g.path -Algorithm SHA256).Hash
   neutral_capture_sha256=(Get-FileHash -LiteralPath $n.path -Algorithm SHA256).Hash
  }
  $log+=($entry|ConvertTo-Json -Compress)
 }
}finally{
 $x=& $lab -Action load-state -StateName $backup|ConvertFrom-Json
 if(!$x.ok){throw 'CRITICAL ORIGINAL RESTORE FAILED'}
 $log+='RESTORED=True'
}
$log|ForEach-Object{Write-Output $_}
