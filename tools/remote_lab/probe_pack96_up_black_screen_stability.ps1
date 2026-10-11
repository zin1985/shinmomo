param()
$ErrorActionPreference='Stop'
$repo='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $repo 'tools\remote_lab\shinmomo_background_lab.ps1'
$source='analysis_pack96_title_dismissed_39_24_20261011'
$back='pack96_up_transition_check_'+(Get-Date -Format 'yyMMddHHmmss')
$x=& $lab -Action save-state -StateName $back|ConvertFrom-Json
if(!$x.ok){throw 'Failed to protect emulator'}
try{
 $l=& $lab -Action load-state -StateName $source|ConvertFrom-Json
 if(!$l.ok){throw 'Cannot load valid post-modal scene fixture'}
 $a=& $lab -Action vm-frames-gamepad -Buttons Up -Frames 96 -Player 1|ConvertFrom-Json
 $parts=@()
 foreach($n in @(120,120,120,120)){
   $sample=& $lab -Action vm-frames -Frames $n|ConvertFrom-Json
   $doc=Get-Content $sample.path -Raw -Encoding UTF8|ConvertFrom-Json
   $pic=& $lab -Action screenshot|ConvertFrom-Json
   $parts+=,[pscustomobject]@{
     frame=$doc.after.frame;pack=$doc.after.w0305;x=$doc.after.w1573;y=$doc.after.w157d
     selector=$doc.after.w126e;secondary=$doc.after.w12b4
     screenshot=$pic.path
     screenshot_sha256=(Get-FileHash -LiteralPath $pic.path -Algorithm SHA256).Hash
     trace_sha256=(Get-FileHash -LiteralPath $sample.path -Algorithm SHA256).Hash
   }
 }
 $parts|ForEach-Object{Write-Output ($_|ConvertTo-Json -Compress)}
}finally{
 $r=& $lab -Action load-state -StateName $back|ConvertFrom-Json
 if(!$r.ok){throw 'CRITICAL: Original lab restore failed'}
 Write-Output 'RESTORED=True'
}
