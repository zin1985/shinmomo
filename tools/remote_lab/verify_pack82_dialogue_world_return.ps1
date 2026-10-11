param()
$ErrorActionPreference='Stop'
$repo='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $repo 'tools\remote_lab\shinmomo_background_lab.ps1'
$fixture='village_dialogue_82_after_12_A_20261011'
$backup='pack82_return_protect_'+(Get-Date -Format 'yyMMddHHmmss')
$s=& $lab -Action status|ConvertFrom-Json
if(!$s.ok -or !$s.running -or @($s.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){throw 'Hidden source emulator required'}
$b=& $lab -Action save-state -StateName $backup|ConvertFrom-Json
if(!$b.ok){throw 'Unable to save emulator'}
$data=@();$restored=$false
try{
 $l=& $lab -Action load-state -StateName $fixture|ConvertFrom-Json
 if(!$l.ok){throw 'Protected original dialogue scene unavailable'}
 $s=& $lab -Action vm-frames-gamepad -Buttons Down -Frames 96 -Player 1|ConvertFrom-Json
 $refs=@($s)
 foreach($n in @(120,120,120)){
  $a=& $lab -Action vm-frames -Frames $n|ConvertFrom-Json
  $refs+=,$a
 }
 foreach($item in $refs){
  $doc=Get-Content $item.path -Raw -Encoding UTF8|ConvertFrom-Json
  $image=& $lab -Action screenshot|ConvertFrom-Json
  $data+=,[pscustomobject]@{
    input=$doc.buttons;input_sent=$doc.input_sent
    requested_frames=$doc.requested_frames
    first_frame=$doc.before.frame;last_frame=$doc.after.frame
    first_pack=$doc.before.w0305;last_pack=$doc.after.w0305
    first_xy=@($doc.before.w1573,$doc.before.w157d)
    final_xy=@($doc.after.w1573,$doc.after.w157d)
    trace_sha256=(Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash
    screenshot_sha256=(Get-FileHash -LiteralPath $image.path -Algorithm SHA256).Hash
    screenshot_path=$image.path
  }
  Write-Output ('FRAMES='+$doc.requested_frames+' PACK='+$doc.before.w0305+'->'+$doc.after.w0305+' XY='+($doc.before.w1573,$doc.before.w157d -join ',')+' TO='+($doc.after.w1573,$doc.after.w157d -join ','))
 }
}finally{
 $r=& $lab -Action load-state -StateName $backup|ConvertFrom-Json
 if(!$r.ok){throw 'CRITICAL: Emulator restore failed'}
 $restored=$true
}
$dir=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab\research'
$file=Join-Path $dir 'pack82_A12_down_saved_world_return_stability_20261011.json'
[ordered]@{
 schema_version=1;kind='pack82_twelve_real_A_dialogues_then_real_Down_world_return'
 A_12_fixture='village_dialogue_82_A_12_20261011.json'
 original_world_entered_via_cheat_adjacent_gamepad=$true
 no_xy_Wram_writes_during_scene_return=$true
 original_emulator_restored=$restored
 records=$data
}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $file -Encoding UTF8
Write-Output ('PROOF_FILE='+$file+' RESTORED='+$restored)
