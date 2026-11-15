param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$IFogSimRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim',
    [string]$PythonExe = 'C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.15.0b1-windows-x86_64-none\python.exe',
    [string]$JdkHome = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot',
    [string]$RunRoot = '',
    [double]$DeadlineMs = 1000.0,
    [double]$PartitionOverheadMs = 3.0,
    [double]$MergeOverheadMs = 2.0,
    [double]$WanLatencyMs = 45.0,
    [double]$WatchdogMs = 1000.0
)
$ErrorActionPreference = 'Stop'
$simulationSource = $PSScriptRoot
$action = Join-Path $simulationSource 'org\fog\test\perfeval\OffloadingActionV2.java'
$plan = Join-Path $simulationSource 'org\fog\test\perfeval\OffloadingActionV2ExecutionPlan.java'
$contract = Join-Path $simulationSource 'org\fog\test\perfeval\OffloadingActionV2ContractTest.java'
$experiment = Join-Path $simulationSource 'org\fog\test\perfeval\RlOffloadingV2PartialIntegrationExperiment.java'
$validator = Join-Path $simulationSource 'validate_v2_partial_integration.py'
$rlRoot = Join-Path $ProjectRoot 'deliverables\08_RL_Model'
$jarRoot = Join-Path $IFogSimRoot 'jars'
$sourceRoot = Join-Path $IFogSimRoot 'src'
$javac = Join-Path $JdkHome 'bin\javac.exe'
$java = Join-Path $JdkHome 'bin\java.exe'
foreach ($required in @($action,$plan,$contract,$experiment,$validator,$PythonExe,$javac)) {
    if (-not (Test-Path $required)) { throw "Required file not found: $required" }
}
if (-not $RunRoot) {
    $RunRoot = Join-Path $ProjectRoot ('audit_output\v2_partial_acceptance_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
if (Test-Path $RunRoot) { throw "Refusing to reuse existing output directory: $RunRoot" }
New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
$classes = Join-Path $RunRoot 'classes'
New-Item -ItemType Directory -Force -Path $classes | Out-Null
$classpath = "$jarRoot\*;$jarRoot\commons-math3-3.5\commons-math3-3.5.jar"
& $javac -encoding UTF-8 -cp $classpath -sourcepath "$sourceRoot;$simulationSource" -d $classes $action $plan $contract $experiment
if ($LASTEXITCODE -ne 0) { throw "javac failed: $LASTEXITCODE" }
$javaClasspath = "$classes;$classpath"
$scenarioArgs = @('--deadline-ms',"$DeadlineMs",'--partition-overhead-ms',"$PartitionOverheadMs",
    '--merge-overhead-ms',"$MergeOverheadMs",'--wan-latency-ms',"$WanLatencyMs",'--watchdog-ms',"$WatchdogMs")
& $java -cp $javaClasspath org.fog.test.perfeval.OffloadingActionV2ContractTest
if ($LASTEXITCODE -ne 0) { throw "Java contract tests failed: $LASTEXITCODE" }
$actions = @('LOCAL','EDGE_PARTIAL_25','EDGE_PARTIAL_50','EDGE_PARTIAL_75','EDGE_FULL',
             'CLOUD_PARTIAL_25','CLOUD_PARTIAL_50','CLOUD_PARTIAL_75','CLOUD_FULL')
foreach ($name in $actions) {
    $output = Join-Path $RunRoot $name
    New-Item -ItemType Directory -Force -Path $output | Out-Null
    $runArgs = @('-cp',$javaClasspath,'org.fog.test.perfeval.RlOffloadingV2PartialIntegrationExperiment',
        '--output',$output,'--python',$PythonExe,'--rl-root',$rlRoot,
        '--run-id',("v2-partial-" + $name.ToLower()),'--action',$name,'--tasks','2','--inter-arrival-ms','1')
    $runArgs += $scenarioArgs
    & $java @runArgs
    if ($LASTEXITCODE -ne 0) { throw "iFogSim action case $name failed: $LASTEXITCODE" }
}
$trainOutput = Join-Path $RunRoot 'train_policy'
New-Item -ItemType Directory -Force -Path $trainOutput | Out-Null
$trainArgs = @('-cp',$javaClasspath,'org.fog.test.perfeval.RlOffloadingV2PartialIntegrationExperiment',
    '--output',$trainOutput,'--python',$PythonExe,'--rl-root',$rlRoot,
    '--run-id','v2-partial-learned-policy','--mode','train','--tasks','30','--inter-arrival-ms','1')
$trainArgs += $scenarioArgs
& $java @trainArgs
if ($LASTEXITCODE -ne 0) { throw "iFogSim learned-policy training case failed: $LASTEXITCODE" }
$faultOutput = Join-Path $RunRoot 'failure_drop_edge'
New-Item -ItemType Directory -Force -Path $faultOutput | Out-Null
$faultArgs = @('-cp',$javaClasspath,'org.fog.test.perfeval.RlOffloadingV2PartialIntegrationExperiment',
    '--output',$faultOutput,'--python',$PythonExe,'--rl-root',$rlRoot,
    '--run-id','v2-partial-fault-drop-edge','--action','EDGE_PARTIAL_50',
    '--tasks','1','--drop-branch','edge')
$faultArgs += $scenarioArgs
& $java @faultArgs
$faultExit = $LASTEXITCODE
if ($faultExit -ne 2) { throw "Fault-injection case must fail closed with Java exit 2; received $faultExit" }
& $PythonExe $validator --root $RunRoot
if ($LASTEXITCODE -ne 0) { throw "V2 partial integration validation failed: $LASTEXITCODE" }
Remove-Item -LiteralPath $classes -Recurse -Force
Write-Host "PASS: all nine v2 actions plus 30-task learned-policy training executed through live Python+iFogSim. Artifacts: $RunRoot"
