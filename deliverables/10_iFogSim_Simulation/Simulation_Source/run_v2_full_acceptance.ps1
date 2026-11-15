param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$IFogSimRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim',
    [string]$PythonExe = 'C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.15.0b1-windows-x86_64-none\python.exe',
    [string]$JdkHome = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot',
    [string]$RunRoot = ''
)

$ErrorActionPreference = 'Stop'
$simulationSource = $PSScriptRoot
$source = Join-Path $simulationSource 'org\fog\test\perfeval\RlOffloadingV2IntegrationExperiment.java'
$contractTest = Join-Path $simulationSource 'org\fog\test\perfeval\OffloadingActionV2ContractTest.java'
$validator = Join-Path $simulationSource 'validate_v2_integration.py'
$jarRoot = Join-Path $IFogSimRoot 'jars'
$sourceRoot = Join-Path $IFogSimRoot 'src'
$rlRoot = Join-Path $ProjectRoot 'deliverables\08_RL_Model'
$javac = Join-Path $JdkHome 'bin\javac.exe'
$java = Join-Path $JdkHome 'bin\java.exe'

if (-not (Test-Path $source)) { throw "V2 experiment source not found: $source" }
if (-not (Test-Path $rlRoot)) { throw "RL model root not found: $rlRoot" }
if (-not (Test-Path $PythonExe)) { throw "Python executable not found: $PythonExe" }
if (-not (Test-Path $javac)) { throw "JDK compiler not found: $javac" }
if (-not $RunRoot) {
    $RunRoot = Join-Path $ProjectRoot ('audit_output\v2_full_acceptance_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
if (Test-Path $RunRoot) { throw "Refusing to reuse existing output directory: $RunRoot" }
New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
$classes = Join-Path $RunRoot 'classes'
New-Item -ItemType Directory -Force -Path $classes | Out-Null

$classpath = "$jarRoot\*;$jarRoot\commons-math3-3.5\commons-math3-3.5.jar"
& $javac -encoding UTF-8 -cp $classpath -sourcepath "$sourceRoot;$simulationSource" -d $classes $source $contractTest
if ($LASTEXITCODE -ne 0) { throw "javac failed with exit code $LASTEXITCODE" }

$javaClasspath = "$classes;$classpath"
& $java -cp $javaClasspath org.fog.test.perfeval.OffloadingActionV2ContractTest
if ($LASTEXITCODE -ne 0) { throw "Java v2 action contract tests failed with exit code $LASTEXITCODE" }
$cases = @(
    @{ Name = 'train_multi_task'; Mode = 'train'; Policy = 'edge'; Tasks = 4; Expected = $null },
    @{ Name = 'baseline_local'; Mode = 'baseline'; Policy = 'local'; Tasks = 2; Expected = 'LOCAL' },
    @{ Name = 'baseline_edge'; Mode = 'baseline'; Policy = 'edge'; Tasks = 2; Expected = 'EDGE_FULL' },
    @{ Name = 'baseline_cloud'; Mode = 'baseline'; Policy = 'cloud'; Tasks = 2; Expected = 'CLOUD_FULL' }
)
foreach ($case in $cases) {
    $output = Join-Path $RunRoot $case.Name
    $arguments = @('-cp', $javaClasspath, 'org.fog.test.perfeval.RlOffloadingV2IntegrationExperiment',
        '--output', $output, '--python', $PythonExe, '--rl-root', $rlRoot,
        '--run-id', ('v2-' + $case.Name), '--mode', $case.Mode, '--policy', $case.Policy,
        '--tasks', [string]$case.Tasks, '--inter-arrival-ms', '1')
    & $java @arguments
    if ($LASTEXITCODE -ne 0) { throw "Java case $($case.Name) failed with exit code $LASTEXITCODE" }
}
& $PythonExe $validator --root $RunRoot
if ($LASTEXITCODE -ne 0) { throw "V2 trace validation failed with exit code $LASTEXITCODE" }
if (Test-Path $classes) { Remove-Item -LiteralPath $classes -Recurse -Force }
Write-Host "PASS: v2 full-placement acceptance artifacts written to $RunRoot"
