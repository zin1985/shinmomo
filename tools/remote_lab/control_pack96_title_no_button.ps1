param()
$ErrorActionPreference='Stop'
$p='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $p 'tools\remote_lab\shinmomo_background_lab.ps1'
$fixture='analysis_pack96_after_natural_down_39_24_20261011'
$name='pack96_modal_control_backup_'+(Get-Date -Format 'yyMMddHHmmss')
$b=& $lab -Action save-state -StateName $name|ConvertFrom-Json
if(!$b.ok){throw 'Source lab backup failed'}
try{
 $l=& $lab -Action load-state -StateName $fixture|ConvertFrom-Json
 if(!$l.ok){throw 'Fixture missing'}
 $idle=& $lab -Action vm-frames -Frames 72|ConvertFrom-Json
 $trial=& $lab -Action vm-frames-gamepad -Buttons Right -Frames 72 -Player 1|ConvertFrom-Json
 $a=Get-Content $trial.path -Raw -Encoding UTF8|ConvertFrom-Json
 $pic=& $lab -Action screenshot|ConvertFrom-Json
 Write-Output ('CONTROL_NO_BUTTON_RIGHT='+$a.before.w0305+':'+$a.before.w1573+','+$a.before.w157d+' -> '+$a.after.w0305+':'+$a.after.w1573+','+$a.after.w157d+' PIC='+$pic.path)
 Write-Output ('NEUTRAL_HASH='+(Get-FileHash $idle.path -Algorithm SHA256).Hash)
 Write-Output ('RIGHT_HASH='+(Get-FileHash $trial.path -Algorithm SHA256).Hash)
}finally{$r=& $lab -Action load-state -StateName $name|ConvertFrom-Json;if(!$r.ok){throw 'CRITICAL: Original state restoration failed'};Write-Output 'RESTORED=True'}
