param(
 [ValidateSet('0x82','0x60')][string]$Pack='0x82',
 [ValidateRange(1,16)][int]$Presses=10
)
$ErrorActionPreference='Stop'
$repo='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $repo 'tools\remote_lab\shinmomo_background_lab.ps1'
$ledger=Get-Content (Join-Path $repo 'data\maps\transitions\world_37_gamepad_entrances_after_cheat_20261011.json') -Raw -Encoding UTF8|ConvertFrom-Json
$entry=@($ledger.entries|Where-Object{$_.destination_pack -eq $Pack}|Select-Object -First 1)
if($entry.Count -ne 1){throw 'Expected exact one source scene'}
$name='analysis_multi_world_'+$entry[0].transition_id+'_p'+$Pack.Substring(2)+'_20261011'
$s=& $lab -Action status|ConvertFrom-Json
if(!$s.ok -or !$s.running -or @($s.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){throw 'Protected hidden emulator required'}
$backup='village_dialogue_p'+$Pack.Substring(2)+'_'+(Get-Date -Format 'yyMMddHHmmss')+'_'+[guid]::NewGuid().ToString('N').Substring(0,5)
$b=& $lab -Action save-state -StateName $backup|ConvertFrom-Json
if(!$b.ok){throw 'Original scene backup failed'}
$history=@();$restored=$false
try{
 $load=& $lab -Action load-state -StateName $name|ConvertFrom-Json
 if(!$load.ok){throw 'Expected pack entry savestate missing'}
 $settle=& $lab -Action vm-frames -Frames 12|ConvertFrom-Json
 $doc=Get-Content $settle.path -Raw -Encoding UTF8|ConvertFrom-Json
 if(('0x{0:X2}' -f [int]$doc.after.w0305) -ne $Pack){throw 'Incorrect source savestate pack'}
 $pic=& $lab -Action screenshot|ConvertFrom-Json
 $history+=,[pscustomobject]@{
  index=0;input='None';frame=$doc.after.frame
  pack=('0x{0:X2}' -f [int]$doc.after.w0305);xy=@([int]$doc.after.w1573,[int]$doc.after.w157d)
  screenshot=$pic.path;screen_sha256=(Get-FileHash $pic.path -Algorithm SHA256).Hash
  neutral_sha256=(Get-FileHash $settle.path -Algorithm SHA256).Hash
 }
 for($i=1;$i -le $Presses;$i++){
  $action=& $lab -Action vm-frames-gamepad -Buttons A -Frames 8 -Player 1|ConvertFrom-Json
  $idle=& $lab -Action vm-frames -Frames 20|ConvertFrom-Json
  if(!$action.ok -or !$idle.ok){throw 'Gamepad dialogue trial failed'}
  $after=Get-Content $idle.path -Raw -Encoding UTF8|ConvertFrom-Json
  $pic=& $lab -Action screenshot|ConvertFrom-Json
  $history+=,[pscustomobject]@{
   index=$i;input='A8 neutral20';frame=$after.after.frame
   pack=('0x{0:X2}' -f [int]$after.after.w0305);xy=@([int]$after.after.w1573,[int]$after.after.w157d)
   screenshot=$pic.path;screen_sha256=(Get-FileHash $pic.path -Algorithm SHA256).Hash
   gamepad_sha256=(Get-FileHash $action.path -Algorithm SHA256).Hash
   neutral_sha256=(Get-FileHash $idle.path -Algorithm SHA256).Hash
  }
  Write-Output ('PACK='+$Pack+' PRESS='+$i+' PACK_AFTER='+$history[-1].pack+' XY='+($history[-1].xy -join ',')+' SCREEN='+$history[-1].screen_sha256)
 }
 $saved='village_dialogue_'+$Pack.Substring(2)+'_after_'+$Presses+'_A_20261011'
 $v=& $lab -Action save-state -StateName $saved|ConvertFrom-Json
 if(!$v.ok){throw 'Cannot preserve reached village research state'}
 $walk=& $lab -Action vm-frames-gamepad -Buttons Down -Frames 96 -Player 1|ConvertFrom-Json
 $neutral=& $lab -Action vm-frames -Frames 120|ConvertFrom-Json
 $finish=Get-Content $neutral.path -Raw -Encoding UTF8|ConvertFrom-Json
 $history+=,[pscustomobject]@{
  index=$Presses+1;input='Down96 neutral120';frame=$finish.after.frame
  pack=('0x{0:X2}' -f [int]$finish.after.w0305);xy=@([int]$finish.after.w1573,[int]$finish.after.w157d)
  input_sha256=(Get-FileHash $walk.path -Algorithm SHA256).Hash
  neutral_sha256=(Get-FileHash $neutral.path -Algorithm SHA256).Hash
 }
 Write-Output ('PACK='+$Pack+' AFTER_A_AND_DOWN='+$history[-1].pack+':'+($history[-1].xy -join ','))
}finally{
 $reset=& $lab -Action load-state -StateName $backup|ConvertFrom-Json
 if(!$reset.ok){throw 'CRITICAL: Could not restore original dedicated emulator'}
 $restored=$true
}
$dir=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab\research'
$file=Join-Path $dir ('village_dialogue_'+$Pack.Substring(2)+'_A_'+$Presses+'_20261011.json')
[ordered]@{
 schema_version=1;kind='village_scene_repeated_dialogue_and_down_probe'
 pack=$Pack;source_world_transition_id=$entry[0].transition_id
 original_world_entry_was_cheat_seeded=$true
 probe_uses_no_xy_cheat=$true
 original_hidden_emulator_restored=$restored
 A_presses=$Presses;history=$history
}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $file -Encoding UTF8
Write-Output ('PROOF_FILE='+$file)
