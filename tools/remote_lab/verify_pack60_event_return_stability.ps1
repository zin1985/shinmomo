param()
$ErrorActionPreference='Stop'
$p='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $p 'tools\remote_lab\shinmomo_background_lab.ps1'
$saved='pack60_dialogue_continuation_after_24_A_20261011'
$st=& $lab -Action status|ConvertFrom-Json
if(!$st.ok -or !$st.running -or @($st.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){throw 'Only hidden dedicated emulator'}
$original='pack60_world_stability_backup_'+(Get-Date -Format 'yyMMddHHmmss')+'_'+[guid]::NewGuid().ToString('N').Substring(0,5)
$before=& $lab -Action save-state -StateName $original|ConvertFrom-Json
if(!$before.ok){throw 'Unable to preserve emulator'}
$outData=@()
try{
 $load=& $lab -Action load-state -StateName $saved|ConvertFrom-Json
 if(!$load.ok){throw 'Pack60 post-event fixture missing'}
 $pressed=& $lab -Action vm-frames-gamepad -Buttons Down -Frames 96 -Player 1|ConvertFrom-Json
 $ops=@($pressed)
 foreach($i in 1..3){
   $capture=& $lab -Action vm-frames -Frames 120|ConvertFrom-Json
   $ops+=,$capture
 }
 foreach($x in $ops){
   $doc=Get-Content $x.path -Raw -Encoding UTF8|ConvertFrom-Json
   $screen=& $lab -Action screenshot|ConvertFrom-Json
   $row=[pscustomobject]@{
     button=$doc.buttons;input_sent=$doc.input_sent
     requested_frames=$doc.requested_frames
     start_frame=$doc.before.frame;end_frame=$doc.after.frame
     start_pack=$doc.before.w0305;end_pack=$doc.after.w0305
     start_xy=@([int]$doc.before.w1573,[int]$doc.before.w157d)
     end_xy=@([int]$doc.after.w1573,[int]$doc.after.w157d)
     trace_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $x.path).Hash
     screenshot_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $screen.path).Hash
     screenshot_path=$screen.path
   }
   $outData+=,$row
   Write-Output ('FRAMES='+$row.requested_frames+' '+$row.start_pack+':'+($row.start_xy -join ',')+' -> '+$row.end_pack+':'+($row.end_xy -join ','))
 }
}finally{
 $reset=& $lab -Action load-state -StateName $original|ConvertFrom-Json
 if(!$reset.ok){throw 'CRITICAL original state restore failed'}
 Write-Output 'ORIGINAL_RESTORED=True'
}
$dir=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab\research'
$file=Join-Path $dir 'pack60_A36_down_saved_world_extended_stability_20261011.json'
[ordered]@{
 schema_version=1;kind='pack60_36_real_A_presses_then_Down_world_return_stability'
 original_world_entry_cheat_positioned=$true
 no_XY_Wram_edit_during_scene=$true
 original_hidden_emulator_restored=$true
 original_dialogue_A_presses=12
 additional_dialogue_A_presses=24
 records=$outData
}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $file -Encoding UTF8
Write-Output ('PROOF_FILE='+$file)
