param()
$ErrorActionPreference='Stop'
$repo='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $repo 'tools\remote_lab\shinmomo_background_lab.ps1'
$origin='analysis_pack96_after_natural_down_39_24_20261011'
$backupName='pack96_button_probe_backup_'+(Get-Date -Format 'yyMMddHHmmss')
$sys=& $lab -Action status|ConvertFrom-Json
if(!$sys.ok -or !$sys.running -or @($sys.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){throw 'Hidden BizHawk only'}
$b=& $lab -Action save-state -StateName $backupName|ConvertFrom-Json
if(!$b.ok){throw 'Could not protect source lab state'}
try{
 foreach($btn in @('A','B','Start')){
  $l=& $lab -Action load-state -StateName $origin|ConvertFrom-Json
  if(!$l.ok){throw 'Arrival fixture not found'}
  $press=& $lab -Action vm-frames-gamepad -Buttons $btn -Frames 8 -Player 1|ConvertFrom-Json
  if(!$press.ok){throw 'Controller button refused'}
  $idle=& $lab -Action vm-frames -Frames 64|ConvertFrom-Json
  if(!$idle.ok){throw 'Neutral following button failed'}
  $walk=& $lab -Action vm-frames-gamepad -Buttons Right -Frames 72 -Player 1|ConvertFrom-Json
  if(!$walk.ok){throw 'Walking probe failed'}
  $doc=Get-Content $walk.path -Raw -Encoding UTF8|ConvertFrom-Json
  $image=& $lab -Action screenshot|ConvertFrom-Json
  $f=Get-Content $idle.path -Raw -Encoding UTF8|ConvertFrom-Json
  $out=[ordered]@{
    button=$btn
    after_button_neutral_pack=$f.after.w0305
    after_button_neutral_xy=@($f.after.w1573,$f.after.w157d)
    after_right_pack=$doc.after.w0305
    after_right_xy=@($doc.after.w1573,$doc.after.w157d)
    original_frame=$doc.before.frame
    ending_frame=$doc.after.frame
    press_sha256=(Get-FileHash -LiteralPath $press.path -Algorithm SHA256).Hash
    neutral_sha256=(Get-FileHash -LiteralPath $idle.path -Algorithm SHA256).Hash
    right_sha256=(Get-FileHash -LiteralPath $walk.path -Algorithm SHA256).Hash
    screenshot_path=$image.path
    screenshot_sha256=(Get-FileHash -LiteralPath $image.path -Algorithm SHA256).Hash
  }
  Write-Output ($out|ConvertTo-Json -Compress -Depth 4)
 }
}finally{
 $r=& $lab -Action load-state -StateName $backupName|ConvertFrom-Json
 if(!$r.ok){throw 'Original lab state restore failed'}
 Write-Output 'RESTORED=True'
}
