param(
  [string]$LabDir='',
  [string]$OutFile=''
)
$ErrorActionPreference='Stop'
$labScript=Join-Path $PSScriptRoot 'shinmomo_background_lab.ps1'
if(!(Test-Path -LiteralPath $labScript)){throw 'Dedicated background lab entry not found'}
if(!$LabDir){$LabDir=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab'}
$probes=@(
  @{key='map_state';start='0x0300';length=96},
  @{key='vm_mode_and_entry';start='0x1390';length=64},
  @{key='player_coordinates';start='0x1570';length=32},
  @{key='saved_map_pack';start='0x15C0';length=32}
)
$data=@{}
foreach($probe in $probes){
  # capture-memory only. No stepping, state restoration or keyboard input.
  $raw=& $labScript -Action capture-memory -LabDir $LabDir -Domain 'WRAM' -Start $probe.start -Length $probe.length
  $response=($raw |Select-Object -Last 1 |ConvertFrom-Json)
  if(!$response.ok -or !(Test-Path -LiteralPath $response.path)){throw 'Invalid bridge capture result'}
  $capture=Get-Content -LiteralPath $response.path -Raw -Encoding UTF8 |ConvertFrom-Json
  if([int]$capture.start -ne [Convert]::ToInt32($probe.start,16) -or $capture.bytes.Count -ne $probe.length){
    throw ('Capture range mismatch at '+$probe.start)
  }
  $data[$probe.key]=@{frame=[long]$capture.frame;path=$response.path;bytes=@($capture.bytes)}
}
$frames=@($data.Values|ForEach-Object{$_.frame}|Select-Object -Unique)
$coherent=$frames.Count -eq 1
function HexByte($value){return ('0x'+([int]$value).ToString('X2'))}
$values=@{
  'WRAM_0305_current_pack'=HexByte $data['map_state'].bytes[5]
  'WRAM_035F_vm_mode'=HexByte $data['map_state'].bytes[95]
  'WRAM_1398_special_dispatch'=HexByte $data['vm_mode_and_entry'].bytes[8]
  'WRAM_13B8_destination_entry'=HexByte $data['vm_mode_and_entry'].bytes[40]
  'WRAM_1573_x_raw'=HexByte $data['player_coordinates'].bytes[3]
  'WRAM_157D_y_raw'=HexByte $data['player_coordinates'].bytes[13]
  'WRAM_15CF_previous_pack'=HexByte $data['saved_map_pack'].bytes[15]
  'WRAM_15D0_new_pack'=HexByte $data['saved_map_pack'].bytes[16]
}
$report=[ordered]@{
  schema_version=1
  kind='shinmomo_background_vm_context_readonly'
  frame_consistent=$coherent
  observed_frame=$(if($coherent){$frames[0]}else{$null})
  sampled_frames=@($frames)
  values=$values
  exact_capture_paths=@($data.Values|ForEach-Object{$_.path}|Sort-Object)
  interpretation='Observational snapshot only. A normal-mode byte or active map pack does not prove a particular event/transition executed. If frame_consistent=false, fields must not be combined as a same-frame state.'
  emulator_control_actions='none'
  input_sent=$false
}
if(!$OutFile){
  $folder=Join-Path $LabDir 'captures'
  $stamp=(Get-Date).ToString('yyyyMMdd_HHmmss_fff')
  $OutFile=Join-Path $folder ('vm_context_'+$stamp+'.json')
}
$dir=Split-Path -Parent $OutFile
New-Item -ItemType Directory -Force -Path $dir |Out-Null
[IO.File]::WriteAllText($OutFile,($report|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
@{ok=$true;path=$OutFile;frame_consistent=$coherent;sampled_frames=@($frames);values=$values;input_sent=$false} |ConvertTo-Json -Depth 5 -Compress
