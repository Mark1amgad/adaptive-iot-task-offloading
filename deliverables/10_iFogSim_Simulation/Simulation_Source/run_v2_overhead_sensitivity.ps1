param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$IFogSimRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim',
    [string]$PythonExe = 'C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.15.0b1-windows-x86_64-none\python.exe',
    [string]$JdkHome = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot',
    [string]$OutputRoot = ''
)
$ErrorActionPreference = 'Stop'
$runner = Join-Path $PSScriptRoot 'run_v2_partial_acceptance.ps1'
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $ProjectRoot ('audit_output\v2_overhead_sensitivity_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
if (Test-Path $OutputRoot) { throw "Refusing to reuse existing output directory: $OutputRoot" }
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

$scenarios = @(
    @{ Name = 'zero_overhead'; Partition = 0.0; Merge = 0.0 },
    @{ Name = 'high_overhead'; Partition = 10.0; Merge = 10.0 }
)
foreach ($scenario in $scenarios) {
    $runRoot = Join-Path $OutputRoot $scenario.Name
    & $runner -ProjectRoot $ProjectRoot -IFogSimRoot $IFogSimRoot -PythonExe $PythonExe -JdkHome $JdkHome -RunRoot $runRoot -DeadlineMs 1000.0 -PartitionOverheadMs $scenario.Partition -MergeOverheadMs $scenario.Merge -WanLatencyMs 45.0 -WatchdogMs 1000.0
    if ($LASTEXITCODE -ne 0) { throw "Scenario $($scenario.Name) failed: $LASTEXITCODE" }
}
Write-Host "PASS: zero- and high-overhead sensitivity runs completed. Artifacts: $OutputRoot"
