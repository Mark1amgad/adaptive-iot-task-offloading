param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$IFogSimRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim',
    [string]$PythonExe = 'C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.15.0b1-windows-x86_64-none\python.exe',
    [string]$JdkHome = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot',
    [string]$OutputRoot = '',
    [int]$Seed = 42,
    [int]$Tasks = 60,
    [ValidateSet('mixed','divisible','indivisible')][string]$Profile = 'mixed',
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
$generator = Join-Path $simulationSource 'generate_workload_v2.py'
$validator = Join-Path $simulationSource 'validate_v2_workload.py'
$rlRoot = Join-Path $ProjectRoot 'deliverables\08_RL_Model'
$jarRoot = Join-Path $IFogSimRoot 'jars'
$sourceRoot = Join-Path $IFogSimRoot 'src'
$javac = Join-Path $JdkHome 'bin\javac.exe'
$java = Join-Path $JdkHome 'bin\java.exe'
foreach ($required in @($action,$plan,$contract,$experiment,$generator,$validator,$PythonExe,$javac)) {
    if (-not (Test-Path $required)) { throw "Required file not found: $required" }
}
if (-not $OutputRoot) { $OutputRoot = Join-Path $ProjectRoot ('audit_output\v2_workload_seed' + $Seed + '_' + (Get-Date -Format 'yyyyMMdd_HHmmss')) }
if (Test-Path $OutputRoot) { throw "Refusing to reuse existing output directory: $OutputRoot" }
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$workloadFile = Join-Path $OutputRoot ('workload_seed' + $Seed + '.jsonl')
& $PythonExe $generator --seed $Seed --tasks $Tasks --profile $Profile --output $workloadFile
if ($LASTEXITCODE -ne 0) { throw "Workload generation failed: $LASTEXITCODE" }
$classes = Join-Path $OutputRoot 'classes'
New-Item -ItemType Directory -Force -Path $classes | Out-Null
$classpath = "$jarRoot\*;$jarRoot\commons-math3-3.5\commons-math3-3.5.jar"
& $javac -encoding UTF-8 -cp $classpath -sourcepath "$sourceRoot;$simulationSource" -d $classes $action $plan $contract $experiment
if ($LASTEXITCODE -ne 0) { throw "javac failed: $LASTEXITCODE" }
$javaClasspath = "$classes;$classpath"
& $java -cp $javaClasspath org.fog.test.perfeval.OffloadingActionV2ContractTest
if ($LASTEXITCODE -ne 0) { throw "Java contract tests failed: $LASTEXITCODE" }
$runOutput = Join-Path $OutputRoot 'train_policy'
New-Item -ItemType Directory -Force -Path $runOutput | Out-Null
& $java -cp $javaClasspath org.fog.test.perfeval.RlOffloadingV2PartialIntegrationExperiment --output $runOutput --python $PythonExe --rl-root $rlRoot --run-id ("v2-workload-seed-" + $Seed) --mode train --workload $workloadFile --partition-overhead-ms $PartitionOverheadMs --merge-overhead-ms $MergeOverheadMs --wan-latency-ms $WanLatencyMs --watchdog-ms $WatchdogMs
if ($LASTEXITCODE -ne 0) { throw "Variable-workload iFogSim run failed: $LASTEXITCODE" }
& $PythonExe $validator --root $OutputRoot
if ($LASTEXITCODE -ne 0) { throw "Variable-workload validation failed: $LASTEXITCODE" }
Write-Host "PASS: variable workload run completed. Artifacts: $OutputRoot"
