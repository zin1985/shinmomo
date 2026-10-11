param()
$ErrorActionPreference='Stop'
$repo='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $repo 'tools\remote_lab\shinmomo_background_lab.ps1'
$source='analysis_multi_world_catalog_transition_0756_p96_20261011'
$backupName='pack96_neutral_protected_'+(Get-Date -Format 'yyMMddHHmmss')+'_'+([guid]::NewGuid().ToString('N').Substring(0,6))
$s=& $lab -Action status|ConvertFrom-Json
if(!$s.ok -or !$s.running -or @($s.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){throw 'Only protected hidden BizHawk is permitted'}
$r=& $lab -Action save-state -StateName $backupName|ConvertFrom-Json
if(!$r.ok){throw 'Could not protect previous state'}
$captures=@()
$restored=$false
try{
  $l=& $lab -Action load-state -StateName $source|ConvertFrom-Json
  if(!$l.ok){throw 'Saved scene arrival unavailable'}
  foreach($frames in @(12,120,72)){
    $read=& $lab -Action vm-frames -Frames $frames|ConvertFrom-Json
    if(!$read.ok -or !(Test-Path -LiteralPath $read.path)){throw 'Failed neutral capture'}
    $doc=Get-Content $read.path -Raw -Encoding UTF8|ConvertFrom-Json
    $captures+=,[ordered]@{
      requested_frames=$frames
      first_frame=$doc.before.frame
      last_frame=$doc.after.frame
      source_pack=$doc.before.w0305
      source_xy=@($doc.before.w1573,$doc.before.w157d)
      result_pack=$doc.after.w0305
      result_xy=@($doc.after.w1573,$doc.after.w157d)
      raw_sha256=(Get-FileHash -LiteralPath $read.path -Algorithm SHA256).Hash
    }
  }
}finally{
 $reset=& $lab -Action load-state -StateName $backupName|ConvertFrom-Json
 if(!$reset.ok){throw 'CRITICAL: previous state restore failed'}
 $restored=$true
}
$dir=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab\research'
New-Item -ItemType Directory -Path $dir -Force|Out-Null
$file=Join-Path $dir 'pack96_no_buttons_204_frames_20261011.json'
[ordered]@{
 schema_version=1
 kind='protected_pack96_no_buttons_control_204frames'
 source_state=$source
 source_world_entrance_was_cheat_positioned=$true
 no_xy_wram_edits_during_control=$true
 no_gamepad_buttons_sent=$true
 all_previous_emulator_state_restored=$restored
 captures=$captures
}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $file -Encoding UTF8
Write-Output ('CONTROL='+$file+' RESTORED='+$restored)
$captures|ForEach-Object{Write-Output ('FRAMES='+$_.requested_frames+' '+$_.source_pack+':'+($_.source_xy -join ',')+' -> '+$_.result_pack+':'+($_.result_xy -join ','))}
