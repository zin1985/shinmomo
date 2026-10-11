param([ValidateRange(16,96)][int]$Frames=72)
$ErrorActionPreference='Stop'
$f=Join-Path $PSScriptRoot 'batch_scene_reverse_exits.ps1'
foreach($i in @(0,3,4,6,14,16)){
    Write-Output ("START "+$i+" direction Up")
    & $f -Start $i -Count 1 -Direction Up -InputFrames $Frames
    if(!$?){throw "Directional scene probe failed for index $i"}
}
Write-Output 'ALL SIX FORWARD-OPPOSITE PROBES COMPLETED WITH SOURCE RESTORES'
