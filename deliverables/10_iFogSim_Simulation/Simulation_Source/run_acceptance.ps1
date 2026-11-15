param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$IFogSimRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim',
    [string]$PythonExe = 'C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.15.0b1-windows-x86_64-none\python.exe',
    [string]$JdkHome = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot',
    [string]$RunRoot = '',
    [switch]$RunErrorTests
)

$ErrorActionPreference = 'Stop'
$simulationSource = $PSScriptRoot
$source = Join-Path $simulationSource 'org\fog\test\perfeval\RlOffloadingIntegrationExperiment.java'
$validator = Join-Path $simulationSource 'validate_integration.py'
$jarRoot = Join-Path $IFogSimRoot 'jars'
$sourceRoot = Join-Path $IFogSimRoot 'src'
$rlRoot = Join-Path $ProjectRoot 'deliverables\08_RL_Model'
$javac = Join-Path $JdkHome 'bin\javac.exe'
$java = Join-Path $JdkHome 'bin\java.exe'

if (-not (Test-Path $source)) { throw "Experiment source not found: $source" }
if (-not (Test-Path $rlRoot)) { throw "RL model root not found: $rlRoot" }
if (-not (Test-Path $PythonExe)) { throw "Python executable not found: $PythonExe" }
if (-not (Test-Path $javac)) { throw "JDK compiler not found: $javac" }
if (-not $RunRoot) {
    $RunRoot = Join-Path $ProjectRoot ('audit_output\multi_task_acceptance_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
if (Test-Path $RunRoot) { throw "Refusing to reuse existing output directory: $RunRoot" }
New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
$classes = Join-Path $RunRoot 'classes'
New-Item -ItemType Directory -Force -Path $classes | Out-Null

$classpath = "$jarRoot\*;$jarRoot\commons-math3-3.5\commons-math3-3.5.jar"
& $javac -encoding UTF-8 -cp $classpath -sourcepath "$sourceRoot;$simulationSource" -d $classes $source
if ($LASTEXITCODE -ne 0) { throw "javac failed with exit code $LASTEXITCODE" }

$javaClasspath = "$classes;$classpath"
$cases = @(
    @{ Name = 'one_task_train_pass'; Mode = 'train'; Policy = 'edge'; Tasks = 1; Interval = 1 },
    @{ Name = 'regression_local'; Mode = 'baseline'; Policy = 'local'; Tasks = 1; Interval = 1 },
    @{ Name = 'regression_edge'; Mode = 'baseline'; Policy = 'edge'; Tasks = 1; Interval = 1 },
    @{ Name = 'regression_cloud'; Mode = 'baseline'; Policy = 'cloud'; Tasks = 1; Interval = 1 },
    @{ Name = 'multi_task_overlap'; Mode = 'baseline'; Policy = 'edge'; Tasks = 4; Interval = 1 },
    @{ Name = 'multi_task_train'; Mode = 'train'; Policy = 'edge'; Tasks = 4; Interval = 1 },
    @{ Name = 'multi_task_train_repeat'; Mode = 'train'; Policy = 'edge'; Tasks = 4; Interval = 1 }
)
$exitCodes = [ordered]@{}
foreach ($case in $cases) {
    $output = Join-Path $RunRoot $case.Name
    $arguments = @('-cp', $javaClasspath, 'org.fog.test.perfeval.RlOffloadingIntegrationExperiment',
        '--output', $output, '--python', $PythonExe, '--rl-root', $rlRoot,
        '--run-id', ('acceptance-' + $case.Name), '--mode', $case.Mode, '--policy', $case.Policy,
        '--tasks', [string]$case.Tasks, '--inter-arrival-ms', [string]$case.Interval)
    & $java @arguments
    $exitCodes[$case.Name] = $LASTEXITCODE
    if ($LASTEXITCODE -ne 0) { throw "Java case $($case.Name) failed with exit code $LASTEXITCODE" }
}

& $PythonExe $validator --root $RunRoot
if ($LASTEXITCODE -ne 0) { throw "trace validation failed with exit code $LASTEXITCODE" }
if ($RunErrorTests) {
    foreach ($fault in @('timeout', 'malformed')) {
        $output = Join-Path $RunRoot ('fallback_' + $fault)
        $arguments = @('-cp', $javaClasspath, 'org.fog.test.perfeval.RlOffloadingIntegrationExperiment',
            '--output', $output, '--python', $PythonExe,
            '--rl-root', $rlRoot,
            '--run-id', ('acceptance-fallback-' + $fault), '--mode', 'baseline', '--policy', 'edge',
            '--fault', $fault)
        & $java @arguments
        $exitCodes['fallback_' + $fault] = $LASTEXITCODE
        if ($LASTEXITCODE -ne 0) { throw "fallback case $fault failed with exit code $LASTEXITCODE" }
        & $PythonExe $validator --root $RunRoot --suite fallback --fault $fault
        if ($LASTEXITCODE -ne 0) { throw "fallback validation $fault failed with exit code $LASTEXITCODE" }
    }
    $deadlineOutput = Join-Path $RunRoot 'deadline_miss'
    $arguments = @('-cp', $javaClasspath, 'org.fog.test.perfeval.RlOffloadingIntegrationExperiment',
        '--output', $deadlineOutput, '--python', $PythonExe,
        '--rl-root', $rlRoot,
        '--run-id', 'acceptance-deadline-miss', '--mode', 'baseline', '--policy', 'local',
        '--deadline-ms', '0')
    & $java @arguments
    $exitCodes['deadline_miss'] = $LASTEXITCODE
    if ($LASTEXITCODE -ne 0) { throw "deadline case failed with exit code $LASTEXITCODE" }
    & $PythonExe $validator --root $RunRoot --suite deadline
    if ($LASTEXITCODE -ne 0) { throw "deadline validation failed with exit code $LASTEXITCODE" }
}
if (Test-Path $classes) { Remove-Item -LiteralPath $classes -Recurse -Force }
$exitCodes | ConvertTo-Json -Compress | Set-Content -Encoding UTF8 (Join-Path $RunRoot 'exit_codes.json')
Write-Host "PASS: acceptance artifacts written to $RunRoot"