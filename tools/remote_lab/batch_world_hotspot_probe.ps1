param(
    [ValidateRange(0,100)][int]$Start=0,
    [ValidateRange(1,12)][int]$Count=5,
    [ValidateSet('south','north')][string]$Approach='south'
)
$ErrorActionPreference='Stop'
$repo='C:\Users\zin\Documents\GitHub\shinmomo'
$lab=Join-Path $repo 'tools\remote_lab\shinmomo_background_lab.ps1'
$client=Join-Path $repo 'tools\remote_lab\shinmomo_lab.ps1'
$labDir=Join-Path $env:LOCALAPPDATA 'shinmomo-bg-lab'
$baseState='analysis_world_lv60_hien_20261011'
$plan=Get-Content (Join-Path $repo 'data\maps\transitions\world_hotspot_30scene_probe_plan_20261011.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$selected=@($plan.targets | Select-Object -Skip $Start -First $Count)
$running=& $lab -Action status | ConvertFrom-Json
if(!$running.ok -or !$running.running -or
   !@($running.windows).Count -or
   @($running.windows | Where-Object { $_ -notmatch 'visible=False'}).Count){
    throw 'Only the isolated and hidden BizHawk instance can be used'
}
if(!@($selected).Count){throw 'No probe targets in requested window'}
function Read-B([string]$address,[int]$len=1){
    $r=& $lab -Action capture-memory -Domain WRAM -Start $address -Length $len | ConvertFrom-Json
    if(!$r.ok -or !(Test-Path -LiteralPath $r.path)){throw "Cannot read $address"}
    return ,@((Get-Content -LiteralPath $r.path -Raw -Encoding UTF8 | ConvertFrom-Json).bytes)
}
function Write-B([string]$address,[int]$value){
    if($value -lt 0 -or $value -gt 255){throw 'Expected 8-bit WRAM value'}
    $r=& $client write-memory -LabDir $labDir -Domain WRAM -Start $address -Data ('0x{0:X2}' -f $value) | ConvertFrom-Json
    if(!$r.ok){throw "Cannot write $address"}
}
$backupName='world_hotspot_bulk_protect_'+(Get-Date -Format 'yyMMddHHmmss')+'_'+([guid]::NewGuid().ToString('N').Substring(0,6))
$backup=& $lab -Action save-state -StateName $backupName | ConvertFrom-Json
if(!$backup.ok -or !(Test-Path -LiteralPath $backup.path)){throw 'Unable to protect user lab emulator state'}
$results=@()
$completed=0
$restored=$false
try {
    foreach($target in $selected) {
        $id=[string]$target.transition_id
        $sourceX=[int]$target.source_x
        $sourceY=[int]$target.source_y
        $offset=if($Approach -eq 'south'){1}else{-1}
        $startingY=$sourceY+$offset
        $buttons=if($Approach -eq 'south'){'Up'}else{'Down'}
        $record=[ordered]@{
            source_id=$id
            source_cell_xy=@($sourceX,$sourceY)
            approach_xy=@($sourceX,$startingY)
            approach_direction=$buttons
            static_destination_pack=$target.static_destination_pack
            static_destination_config=$target.static_destination_config
            static_destination_x=$target.static_destination_x
            static_destination_y=$target.static_destination_y
            entry_replay_status='not_started'
            source_position_cheat=$true
            gamepad_trigger=$true
            runtime_target_pack=$null
            runtime_arrival_xy=$null
            map_switch_frame=$null
            screenshot_sha256=$null
            screenshot_local_path=$null
            state_name=$null
            raw_input_capture_sha256=$null
            raw_neutral_capture_sha256=$null
        }
        try {
            $l=& $lab -Action load-state -StateName $baseState | ConvertFrom-Json
            if(!$l.ok){throw 'Base world Hien state failed to load'}
            if((Read-B '0x0305')[0] -ne 76){throw 'Wrong world pack 0x4C in source fixture'}
            Write-B '0x1573' $sourceX
            Write-B '0x157D' $startingY
            if((Read-B '0x1573')[0] -ne $sourceX -or
                (Read-B '0x157D')[0] -ne $startingY){throw 'Cheat coordinate mismatch'}
            $idle=& $lab -Action vm-frames -Frames 16|ConvertFrom-Json
            if(!$idle.ok){throw 'Neutral stabilizer failed'}
            $j=Get-Content -LiteralPath $idle.path -Raw -Encoding UTF8|ConvertFrom-Json
            if($j.after.w0305 -ne 76 -or $j.after.w1573 -ne $sourceX -or
                $j.after.w157d -ne $startingY){throw 'Cheat world scene not stable'}
            $probe=& $lab -Action vm-frames-gamepad -Buttons $buttons -Player 1 -Frames 26|ConvertFrom-Json
            if(!$probe.ok){throw 'Controller movement capture failed'}
            $d=Get-Content -LiteralPath $probe.path -Raw -Encoding UTF8|ConvertFrom-Json
            $no=& $lab -Action vm-frames -Frames 120|ConvertFrom-Json
            if(!$no.ok){throw 'First neutral frame capture failed'}
            $nd=Get-Content -LiteralPath $no.path -Raw -Encoding UTF8|ConvertFrom-Json
            $record.raw_input_capture_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $probe.path).Hash
            $record.raw_neutral_capture_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $no.path).Hash
            $contact=@($d.samples | Where-Object {
                $_.w0305 -eq 76 -and
                $_.w1573 -ge $sourceX -and
                $_.w1573 -lt ($sourceX+[int]$target.source_width) -and
                $_.w157d -eq $sourceY
            })
            $record.source_hotspot_touched=$contact.Count -gt 0
            $record.source_contact_frame=if($contact.Count){$contact[0].frame}else{$null}
            $switch=@($d.samples | Where-Object {$_.w0305 -ne 76})
            if($switch.Count){$record.map_switch_frame=$switch[0].frame}
            if($nd.after.w0305 -eq 76){
                $record.entry_replay_status='no_pack_switch_observed'
                $record.final_world_xy=@($nd.after.w1573,$nd.after.w157d)
            }else {
                $next=& $lab -Action vm-frames -Frames 120|ConvertFrom-Json
                if(!$next.ok){throw 'Second neutral capture failed'}
                $end=Get-Content -LiteralPath $next.path -Raw -Encoding UTF8|ConvertFrom-Json
                $record.raw_extra_neutral_capture_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $next.path).Hash
                $record.runtime_target_pack=('0x{0:X2}' -f [int]$end.after.w0305)
                $record.runtime_arrival_xy=@([int]$end.after.w1573,[int]$end.after.w157d)
                $record.map_switch_frame=if($switch.Count){$switch[0].frame}else{(@($nd.samples | Where-Object {$_.w0305 -ne 76}) | Select-Object -First 1).frame}
                $record.entry_replay_status=if($record.runtime_target_pack -eq $target.static_destination_pack) {
                    'gamepad_event_arrived_at_rom_candidate_pack'
                }else{'gamepad_event_different_pack'}
                $shot=& $lab -Action screenshot|ConvertFrom-Json
                if($shot.ok -and (Test-Path -LiteralPath $shot.path)){
                    $record.screenshot_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $shot.path).Hash
                    $record.screenshot_local_path=$shot.path
                }
                $stateName=('analysis_multi_world_'+$id+'_p'+($record.runtime_target_pack -replace '0x','')+'_20261011')
                if(!(Test-Path -LiteralPath (Join-Path "$labDir\states" ($stateName+'.State')))){
                    $save=& $lab -Action save-state -StateName $stateName|ConvertFrom-Json
                    if($save.ok){$record.state_name=$stateName}
                }
            }
        }catch{
            $record.entry_replay_status='probe_error'
            $record.error=$_.Exception.Message
        }
        $results+=[pscustomobject]$record
        $completed++
        Write-Output ('ITEM '+$completed+'/'+@($selected).Count+' '+$id+' '+$target.static_destination_pack+' -> '+$record.entry_replay_status+' PACK='+$record.runtime_target_pack+' XY='+($record.runtime_arrival_xy -join ',')+' CONTACT='+$record.source_hotspot_touched)
    }
}finally{
    $r=& $lab -Action load-state -StateName $backupName |ConvertFrom-Json
    if(!$r.ok){throw 'CRITICAL: the emulator source state could not be restored'}
    $restored=$true
}
$outDir=Join-Path $labDir 'research'
New-Item -ItemType Directory -Path $outDir -Force|Out-Null
$fname=('world_batch_'+$Start+'_'+$Count+'_'+$Approach+'_20261011.json')
$outpath=Join-Path $outDir $fname
[ordered]@{
    schema_version=1
    kind='cheat_adjacent_world_to_actual_gamepad_scene_batch'
    source_analysis_state=$baseState
    source_map_pack='0x4C'
    source_xy_set_by_cheat_before_controller=$true
    all_current_story_gates_proven=$false
    real_controller_trigger_event=$true
    original_emulator_state_restored=$restored
    total_requested=@($selected).Count
    results=$results
}|ConvertTo-Json -Depth 10 |Set-Content -LiteralPath $outpath -Encoding UTF8
Write-Output ('RESULTS_FILE='+$outpath+' COUNT='+$completed+' RESTORED='+$restored)
