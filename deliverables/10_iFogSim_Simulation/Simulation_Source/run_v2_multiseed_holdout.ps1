param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$IFogSimRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim',
    [string]$PythonExe = 'C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.15.0b1-windows-x86_64-none\python.exe',
    [string]$JdkHome = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot',
    [string]$ModelIn = '',
    [int]$TrainingSeed = 42,
    [int[]]$EvaluationSeeds = @(43,44,45),
    [int]$TasksPerSeed = 60,
    [string]$OutputRoot = ''
)
$ErrorActionPreference = 'Stop'
$generator = Join-Path $PSScriptRoot 'generate_workload_v2.py'
$comparisonRunner = Join-Path $PSScriptRoot 'run_v2_policy_comparison.ps1'
$analyzer = Join-Path $PSScriptRoot 'analyze_v2_multiseed.py'
foreach ($required in @($generator,$comparisonRunner,$analyzer,$PythonExe,$ModelIn)) {
    if (-not (Test-Path $required)) { throw "Required file not found: $required" }
}
if ($EvaluationSeeds.Count -lt 2) { throw 'At least two held-out seeds are required for multi-seed analysis.' }
if (-not $OutputRoot) { $OutputRoot = Join-Path $ProjectRoot ('audit_output\v2_multiseed_holdout_' + (Get-Date -Format 'yyyyMMdd_HHmmss')) }
if (Test-Path $OutputRoot) { throw "Refusing to reuse existing output directory: $OutputRoot" }
$workloadDir = Join-Path $OutputRoot 'workloads'
New-Item -ItemType Directory -Force -Path $workloadDir | Out-Null
$analysisArgs = @('--training-seed',"$TrainingSeed",'--training-model',$ModelIn)
foreach ($seed in $EvaluationSeeds) {
    $workloadFile = Join-Path $workloadDir ("workload_seed$seed.jsonl")
    & $PythonExe $generator --seed $seed --tasks $TasksPerSeed --profile mixed --output $workloadFile
    if ($LASTEXITCODE -ne 0) { throw "Workload generation failed for seed $seed" }
    $comparisonRoot = Join-Path $OutputRoot ("comparison_seed$seed")
    & $comparisonRunner -ProjectRoot $ProjectRoot -IFogSimRoot $IFogSimRoot -PythonExe $PythonExe -JdkHome $JdkHome -WorkloadFile $workloadFile -ModelIn $ModelIn -OutputRoot $comparisonRoot
    if ($LASTEXITCODE -ne 0) { throw "Policy comparison failed for seed $seed" }
    $analysisArgs += @('--comparison-root',$comparisonRoot,'--workload',$workloadFile)
}
$summary = Join-Path $OutputRoot 'multi_seed_summary.json'
$analysisArgs += @('--output',$summary)
& $PythonExe $analyzer @analysisArgs
if ($LASTEXITCODE -ne 0) { throw 'Multi-seed analysis failed' }
Write-Host "PASS: held-out seeds $($EvaluationSeeds -join ', ') completed. Summary: $summary"
