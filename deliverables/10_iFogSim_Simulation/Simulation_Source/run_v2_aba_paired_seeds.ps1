[CmdletBinding()]
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$IFogSimRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim',
    [string]$PythonExe = 'C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.15.0b1-windows-x86_64-none\python.exe',
    [string]$InferencePythonExe = 'C:\Users\DELL\Python313\python.exe',
    [string]$JdkHome = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot',
    [string]$ModelIn = 'C:\Users\DELL\OneDrive\Desktop\Research\adaptive-iot-task-offloading\audit_output\aba_pilot_seed_101_20261117\training\python_model.json',
    [string]$RiskStateIn = '',
    [string]$OutputRoot = '',
    [int[]]$Seeds = @(102..121),
    [int]$TasksPerPhase = 30,
    [double]$PartitionOverheadMs = 3.0,
    [double]$MergeOverheadMs = 2.0,
    [double]$WanLatencyMs = 45.0,
    [double]$WatchdogMs = 60000.0
)
$ErrorActionPreference = 'Stop'
$simulationSource = $PSScriptRoot
$generator = Join-Path $simulationSource 'generate_v2_aba_workload.py'
$runner = Join-Path $simulationSource 'run_v2_policy_comparison.ps1'
$inference = Join-Path $simulationSource 'analyze_v2_paired_seed_inference.py'
if (-not $RiskStateIn) { $RiskStateIn = "$ModelIn.risk.json" }
foreach ($required in @($generator,$runner,$inference,$PythonExe,$InferencePythonExe,$ModelIn,$RiskStateIn,(Join-Path $JdkHome 'bin\javac.exe'),(Join-Path $IFogSimRoot 'jars'))) {
    if (-not (Test-Path $required)) { throw "Required file not found: $required" }
}
if ($Seeds.Count -lt 2) { throw 'At least two distinct test seeds are required.' }
if (($Seeds | Select-Object -Unique).Count -ne $Seeds.Count) { throw 'Seed list contains duplicates.' }
if ($TasksPerPhase -lt 10) { throw 'TasksPerPhase must be at least 10.' }
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $ProjectRoot ('audit_output\aba_paired_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
if (Test-Path $OutputRoot) { throw "Refusing to reuse existing output directory: $OutputRoot" }
$workloads = Join-Path $OutputRoot 'workloads'
$evaluations = Join-Path $OutputRoot 'evaluations'
New-Item -ItemType Directory -Force -Path $workloads,$evaluations | Out-Null
$summaryPaths = @()
$runIndex = 0
foreach ($seed in $Seeds) {
    $runIndex++
    $workload = Join-Path $workloads ("aba_seed_{0}.jsonl" -f $seed)
    $evaluationRoot = Join-Path $evaluations ("seed_{0}" -f $seed)
    Write-Host ("[{0}/{1}] Generating A-B-A workload for seed {2}" -f $runIndex,$Seeds.Count,$seed)
    & $PythonExe $generator --seed $seed --tasks-per-phase $TasksPerPhase --output $workload
    if ($LASTEXITCODE -ne 0) { throw "Workload generation failed for seed $seed" }
    Write-Host ("[{0}/{1}] Running five paired policy arms for seed {2}" -f $runIndex,$Seeds.Count,$seed)
    & $runner -ProjectRoot $ProjectRoot -IFogSimRoot $IFogSimRoot -PythonExe $PythonExe -JdkHome $JdkHome -WorkloadFile $workload -ModelIn $ModelIn -RiskStateIn $RiskStateIn -OutputRoot $evaluationRoot -PartitionOverheadMs $PartitionOverheadMs -MergeOverheadMs $MergeOverheadMs -WanLatencyMs $WanLatencyMs -WatchdogMs $WatchdogMs
    if ($LASTEXITCODE -ne 0) { throw "Policy comparison failed for seed $seed" }
    $summary = Join-Path $evaluationRoot 'policy_comparison_summary.json'
    if (-not (Test-Path $summary)) { throw "Missing summary for seed $seed" }
    $summaryPaths += $summary
}
$inferenceOutput = Join-Path $OutputRoot 'paired_seed_inference.json'
Write-Host "All per-seed policy comparisons completed. Running paired-seed inference."
& $InferencePythonExe $inference @summaryPaths --output $inferenceOutput
if ($LASTEXITCODE -ne 0) { throw 'Paired-seed inference failed.' }
Write-Host "PASS: paired-seed A-B-A batch completed. Artifacts: $OutputRoot"
