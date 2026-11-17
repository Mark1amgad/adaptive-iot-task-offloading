[CmdletBinding()]
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$IFogSimRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim',
    [string]$PythonExe = 'C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.15.0b1-windows-x86_64-none\python.exe',
    [string]$InferencePythonExe = 'C:\Users\DELL\Python313\python.exe',
    [string]$JdkHome = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot',
    [string]$ModelIn = 'C:\Users\DELL\OneDrive\Desktop\Research\adaptive-iot-task-offloading\audit_output\aba_pilot_seed_101_20261117\training\python_model.json',
    [string]$RiskStateIn = '',
    [ValidateSet('none','analytical','calibrated')][string]$RiskMode = 'calibrated',
    [string]$SeedRegistry = '',
    [string]$ExperimentFamily = 'iiot_final_aba',
    [ValidateSet('development','validation','test')][string]$EvaluationSplit = 'test',
    [string]$OutputRoot = '',
    [int[]]$Seeds = @(),
    [int]$TasksPerPhase = 30,
    [ValidateSet('combined','network_only','workload_only')][string]$ShiftMode = 'network_only',
    [double]$FixedDeadlineMs = 0.0,
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
$regimeInference = Join-Path $simulationSource 'analyze_v2_aba_regime_inference.py'
if (-not $RiskStateIn) { $RiskStateIn = "$ModelIn.risk.json" }
foreach ($required in @($generator,$runner,$inference,$regimeInference,$PythonExe,$InferencePythonExe,$ModelIn,$RiskStateIn,(Join-Path $JdkHome 'bin\javac.exe'),(Join-Path $IFogSimRoot 'jars'))) {
    if (-not (Test-Path $required)) { throw "Required file not found: $required" }
}
if ($Seeds.Count -lt 2) { throw 'No default seed allocation is provided. Supply at least two explicitly approved seeds after checking the versioned seed registry and local run archives.' }
$historicalSeeds = @(7,42,43,44,45,81) + (101..121) + (201..205) + (301..305) + (401..405) + (901..906) + (951..956)
$reused = @($Seeds | Where-Object { $historicalSeeds -contains $_ })
if ($reused.Count -gt 0) { throw "Refusing known reused seed IDs for a new batch: $($reused -join ', '). Historical IDs require a separately labelled exploratory run." }
if (($Seeds | Select-Object -Unique).Count -ne $Seeds.Count) { throw 'Seed list contains duplicates.' }
if ($TasksPerPhase -lt 10) { throw 'TasksPerPhase must be at least 10.' }
if ($FixedDeadlineMs -lt 0) { throw 'FixedDeadlineMs must be zero (legacy profile) or positive.' }
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
    Write-Host ("[{0}/{1}] Generating {2} A-B-A workload for seed {3} (fixed deadline: {4} ms)" -f $runIndex,$Seeds.Count,$ShiftMode,$seed,$FixedDeadlineMs)
    $generatorArgs = @('--seed',$seed,'--tasks-per-phase',$TasksPerPhase,'--output',$workload,'--shift-mode',$ShiftMode)
    if ($FixedDeadlineMs -gt 0) { $generatorArgs += @('--fixed-deadline-ms',$FixedDeadlineMs) }
    & $PythonExe $generator @generatorArgs
    if ($LASTEXITCODE -ne 0) { throw "Workload generation failed for seed $seed" }
    Write-Host ("[{0}/{1}] Running five paired policy arms for seed {2}" -f $runIndex,$Seeds.Count,$seed)
    & $runner -ProjectRoot $ProjectRoot -IFogSimRoot $IFogSimRoot -PythonExe $PythonExe -JdkHome $JdkHome -WorkloadFile $workload -ModelIn $ModelIn -RiskStateIn $RiskStateIn -RiskMode $RiskMode -SeedRegistry $SeedRegistry -ExperimentFamily $ExperimentFamily -EvaluationSplit $EvaluationSplit -OutputRoot $evaluationRoot -PartitionOverheadMs $PartitionOverheadMs -MergeOverheadMs $MergeOverheadMs -WanLatencyMs $WanLatencyMs -WatchdogMs $WatchdogMs
    if ($LASTEXITCODE -ne 0) { throw "Policy comparison failed for seed $seed" }
    $summary = Join-Path $evaluationRoot 'policy_comparison_summary.json'
    if (-not (Test-Path $summary)) { throw "Missing summary for seed $seed" }
    $summaryPaths += $summary
}
$inferenceOutput = Join-Path $OutputRoot 'paired_seed_inference.json'
$regimeOutput = Join-Path $OutputRoot 'aba_regime_inference.json'
Write-Host "All per-seed policy comparisons completed. Running paired-seed and regime inference."
& $InferencePythonExe $inference @summaryPaths --output $inferenceOutput
if ($LASTEXITCODE -ne 0) { throw 'Paired-seed inference failed.' }
& $InferencePythonExe $regimeInference @summaryPaths --output $regimeOutput
if ($LASTEXITCODE -ne 0) { throw 'A-B-A regime inference failed.' }
Write-Host "PASS: paired-seed A-B-A batch completed (risk mode: $RiskMode; split: $EvaluationSplit). Artifacts: $OutputRoot"
