param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$IFogSimRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim',
    [string]$PythonExe = 'C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.15.0b1-windows-x86_64-none\python.exe',
    [string]$JdkHome = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot',
    [string]$WorkloadFile = '',
    [string]$ModelIn = '',
    [string]$RiskStateIn = '',
    [ValidateSet('none','analytical','calibrated')][string]$RiskMode = 'calibrated',
    [string]$OutputRoot = '',
    [double]$PartitionOverheadMs = 3.0,
    [double]$MergeOverheadMs = 2.0,
    [double]$WanLatencyMs = 45.0,
    [double]$WatchdogMs = 60000.0
)
$ErrorActionPreference = 'Stop'
$simulationSource = $PSScriptRoot
$action = Join-Path $simulationSource 'org\fog\test\perfeval\OffloadingActionV2.java'
$plan = Join-Path $simulationSource 'org\fog\test\perfeval\OffloadingActionV2ExecutionPlan.java'
$contract = Join-Path $simulationSource 'org\fog\test\perfeval\OffloadingActionV2ContractTest.java'
$experiment = Join-Path $simulationSource 'org\fog\test\perfeval\RlOffloadingV2PartialIntegrationExperiment.java'
$analyzer = Join-Path $simulationSource 'analyze_v2_policy_comparison.py'
$manifestBuilder = Join-Path $simulationSource 'create_v2_experiment_manifest.py'
$rlRoot = Join-Path $ProjectRoot 'deliverables\08_RL_Model'
$jarRoot = Join-Path $IFogSimRoot 'jars'
$sourceRoot = Join-Path $IFogSimRoot 'src'
$javac = Join-Path $JdkHome 'bin\javac.exe'
$java = Join-Path $JdkHome 'bin\java.exe'
foreach ($required in @($action,$plan,$contract,$experiment,$analyzer,$manifestBuilder,$PythonExe,$javac,$WorkloadFile,$ModelIn)) {
    if (-not (Test-Path $required)) { throw "Required file not found: $required" }
}
if ($RiskMode -ne 'none') {
    if (-not $RiskStateIn) { $RiskStateIn = "$ModelIn.risk.json" }
    if (-not (Test-Path $RiskStateIn)) { throw "Risk state not found for $RiskMode mode: $RiskStateIn" }
}
if (-not $OutputRoot) { $OutputRoot = Join-Path $ProjectRoot ('audit_output\v2_policy_comparison_' + (Get-Date -Format 'yyyyMMdd_HHmmss')) }
if (Test-Path $OutputRoot) { throw "Refusing to reuse existing output directory: $OutputRoot" }
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$classes = Join-Path $OutputRoot 'classes'
New-Item -ItemType Directory -Force -Path $classes | Out-Null
$classpath = "$jarRoot\*;$jarRoot\commons-math3-3.5\commons-math3-3.5.jar"
& $javac -encoding UTF-8 -cp $classpath -sourcepath "$sourceRoot;$simulationSource" -d $classes $action $plan $contract $experiment
if ($LASTEXITCODE -ne 0) { throw "javac failed: $LASTEXITCODE" }
$javaClasspath = "$classes;$classpath"
& $java -cp $javaClasspath org.fog.test.perfeval.OffloadingActionV2ContractTest
if ($LASTEXITCODE -ne 0) { throw "Java contract tests failed: $LASTEXITCODE" }

# Freeze provenance before any policy run. Every arm receives the exact same manifest.
$manifestPath = Join-Path $OutputRoot 'experiment_manifest.json'
$manifestArgs = @($manifestBuilder,'--project-root',$ProjectRoot,'--simulation-source',$simulationSource,'--rl-root',$rlRoot,'--ifogsim-root',$IFogSimRoot,'--jdk-home',$JdkHome,'--workload',$WorkloadFile,'--model',$ModelIn,'--risk-mode',$RiskMode,'--output',$manifestPath,'--partition-overhead-ms',$PartitionOverheadMs,'--merge-overhead-ms',$MergeOverheadMs,'--wan-latency-ms',$WanLatencyMs,'--watchdog-ms',$WatchdogMs)
if ($RiskMode -ne 'none') { $manifestArgs += @('--risk-state',$RiskStateIn) }
& $PythonExe @manifestArgs
if ($LASTEXITCODE -ne 0) { throw "Experiment manifest creation failed: $LASTEXITCODE" }
$manifestSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestPath).Hash.ToLowerInvariant()

# Fixed baselines must not receive the learned policy's risk filter or calibration state.
# Otherwise the comparison would confound placement policy with risk filtering.
$common = @('--python',$PythonExe,'--rl-root',$rlRoot,'--workload',$WorkloadFile,'--partition-overhead-ms',"$PartitionOverheadMs",'--merge-overhead-ms',"$MergeOverheadMs",'--wan-latency-ms',"$WanLatencyMs",'--watchdog-ms',"$WatchdogMs")
foreach ($policy in @('local','edge','cloud','random')) {
    $out = Join-Path $OutputRoot ('policy_' + $policy)
    New-Item -ItemType Directory -Force -Path $out | Out-Null
    Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $out 'experiment_manifest.json')
    $args = @('-cp',$javaClasspath,'org.fog.test.perfeval.RlOffloadingV2PartialIntegrationExperiment','--output',$out,'--run-id',('paired-' + $policy),'--mode','baseline','--policy',$policy,'--evaluation-mode') + $common
    & $java @args
    if ($LASTEXITCODE -ne 0) { throw "Baseline policy $policy failed: $LASTEXITCODE" }
}
$rlOut = Join-Path $OutputRoot 'policy_rl_eval'
New-Item -ItemType Directory -Force -Path $rlOut | Out-Null
Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $rlOut 'experiment_manifest.json')
$rlArgs = @('-cp',$javaClasspath,'org.fog.test.perfeval.RlOffloadingV2PartialIntegrationExperiment','--output',$rlOut,'--run-id',('paired-rl-eval-' + $RiskMode),'--mode','eval','--model-in',$ModelIn,'--evaluation-mode') + $common
if ($RiskMode -ne 'none') { $rlArgs += @('--risk-filter','--risk-state-in',$RiskStateIn) }
& $java @rlArgs
if ($LASTEXITCODE -ne 0) { throw "RL evaluation policy failed: $LASTEXITCODE" }
& $PythonExe $analyzer --root $OutputRoot --workload $WorkloadFile --manifest $manifestPath
if ($LASTEXITCODE -ne 0) { throw "Policy comparison analysis failed: $LASTEXITCODE" }
Write-Host "PASS: paired policy comparison completed (risk mode: $RiskMode). Artifacts: $OutputRoot"
