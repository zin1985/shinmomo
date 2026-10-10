param(
  [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_-]{1,64}$')][string]$StateName,
  [Parameter(Mandatory=$true)][ValidatePattern('^(?:A|B|X|Y|L|R|Up|Down|Left|Right|Start|Select)(?:[, ]+(?:A|B|X|Y|L|R|Up|Down|Left|Right|Start|Select))*$')][string]$Buttons,
  [ValidateRange(1,120)][int]$InputFrames=18,
  [ValidateRange(1,120)][int]$SettleFrames=120,
  [ValidateRange(2,120)][int]$StableFrames=8
)
$ErrorActionPreference='Stop'
$lab=Join-Path $PSScriptRoot 'shinmomo_background_lab.ps1'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$auditor=Join-Path $root 'tools\python\audit_transition_phases.py'
$labDir=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab'
$fixture=Join-Path (Join-Path $labDir 'states') ($StateName+'.State')
if(!(Test-Path -LiteralPath $fixture)){throw "Local source savestate not found: $fixture"}
$watch=& $lab -Action status|ConvertFrom-Json
if(!$watch.ok -or !$watch.running){throw 'Dedicated BizHawk not running'}
if(!@($watch.windows).Count -or @($watch.windows|Where-Object{$_ -notmatch 'visible=False'}).Count){
  throw 'Background lab has a visible window. Refusing automated probe.'
}
$rollback='probe_restore_'+(Get-Date -Format 'yyMMddHHmmss')+'_'+([guid]::NewGuid().ToString('N').Substring(0,6))
$save=& $lab -Action save-state -StateName $rollback|ConvertFrom-Json
if(!$save.ok -or !(Test-Path -LiteralPath $save.path)){
  throw 'Could not protect original isolated emulator state'
}
$inputPath=$null
$settlePath=$null
$auditPath=$null
$failure=$null
$restoreSuccess=$false
try{
  $load=& $lab -Action load-state -StateName $StateName|ConvertFrom-Json
  if(!$load.ok){throw 'Could not load requested test fixture'}
  $inputCapture=& $lab -Action vm-frames-gamepad -Buttons $Buttons -Player 1 -Frames $InputFrames|ConvertFrom-Json
  if(!$inputCapture.ok){throw 'No valid input frame series'}
  $inputPath=$inputCapture.path
  $settleCapture=& $lab -Action vm-frames -Frames $SettleFrames|ConvertFrom-Json
  if(!$settleCapture.ok){throw 'No valid neutral settlement frame series'}
  $settlePath=$settleCapture.path
  $auditPath=Join-Path (Join-Path $labDir 'captures') ('probe_phases_'+([guid]::NewGuid().ToString('N').Substring(0,12))+'.json')
  # Preserve expected Python audit failure as local evidence, not a
  # remote stderr/transport failure that may tear down Mole Remote.
  $auditOut=Join-Path (Join-Path $labDir 'captures') ('probe_audit_'+([guid]::NewGuid().ToString('N').Substring(0,10))+'.out')
  $auditErr=($auditOut+'.err')
  $run=Start-Process -FilePath 'py.exe' -ArgumentList @(
    '-3', $auditor,
    '--input-trace', $inputPath,
    '--settle-trace', $settlePath,
    '--stable-frames', $StableFrames,
    '--output', $auditPath
  ) -Wait -PassThru -NoNewWindow -RedirectStandardOutput $auditOut -RedirectStandardError $auditErr
  if($run.ExitCode -ne 0 -or !(Test-Path -LiteralPath $auditPath)){
    throw 'Phase audit rejected the experiment (no proven pack switch and settled arrival). Local stderr: '+$auditErr
  }
  $result=Get-Content -LiteralPath $auditPath -Raw -Encoding UTF8|ConvertFrom-Json
  if($result.kind -ne 'runtime_pack_switch_and_settled_arrival_phases' -or
      $result.exact_cpu_handler_execution_proven -ne $false){
    throw 'Unexpected or unsafe phase-audit result'
  }
  $record=[ordered]@{
    ok=$true
    command='probe-map-transition'
    source_fixture=$StateName
    isolated_joypad=$Buttons
    input_frames=$InputFrames
    neutral_settle_frames=$SettleFrames
    frame_switch=$result.pack_switch_frame
    source_pack=$result.source_pack
    destination_pack=$result.destination_pack
    first_settled_frame=$result.first_settled_arrival_frame
    first_settled_coordinate=$result.settled_arrival
    input_capture_local=$inputPath
    settle_capture_local=$settlePath
    evidence_local=$auditPath
    CPU_opcode_proven=$false
    original_state_backup_local=$save.path
    rollback_state_loaded=$false
  }
}catch{
  # An ordinary "no transition" experiment is not a transport failure.
  # Always restore first and emit a fail-closed result. Rollback failure
  # remains a hard error and must NEVER be reported as safe success.
  $failure=$_.Exception.Message
}finally{
  $restored=& $lab -Action load-state -StateName $rollback|ConvertFrom-Json
  if(!$restored.ok){throw 'CRITICAL: isolated emulator rollback did not complete'}
  $restoreSuccess=$true
}
if($failure){
  [ordered]@{
    ok=$false
    command='probe-map-transition'
    outcome='no_verified_transition_or_validation_failed'
    reason=$failure
    source_fixture=$StateName
    input_capture_local=$inputPath
    settle_capture_local=$settlePath
    rollback_state_loaded=$restoreSuccess
    original_state_backup_local=$save.path
    new_graph_edges_promoted=0
  }|ConvertTo-Json -Compress -Depth 6
  return
}
$record.rollback_state_loaded=$restoreSuccess
$record|ConvertTo-Json -Compress -Depth 6
