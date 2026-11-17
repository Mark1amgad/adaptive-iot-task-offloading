param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$IFogSimRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim',
    [string]$JdkHome = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot',
    [string]$PythonExe = 'C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.15.0b1-windows-x86_64-none\python.exe',
    [int]$Tasks = 4,
    [double]$InterArrivalMs = 1.0,
    [string]$RunRoot = ''
)
$ErrorActionPreference = 'Stop'
$sourceRoot = $PSScriptRoot
$source = Join-Path $sourceRoot 'org\fog\test\perfeval\MultiTaskPartialOffloadingSpike.java'
$validator = Join-Path $sourceRoot 'validate_multi_task_partial.py'
$jarRoot = Join-Path $IFogSimRoot 'jars'
$simSource = Join-Path $IFogSimRoot 'src'
$javac = Join-Path $JdkHome 'bin\javac.exe'
$java = Join-Path $JdkHome 'bin\java.exe'
if ($Tasks -lt 1 -or $Tasks -gt 100) { throw 'Tasks must be between 1 and 100' }
if ($InterArrivalMs -le 0) { throw 'InterArrivalMs must be positive' }
if (-not (Test-Path $source)) { throw "Source not found: $source" }
if (-not (Test-Path $PythonExe)) { throw "Python not found: $PythonExe" }
if (-not $RunRoot) { $RunRoot = Join-Path $ProjectRoot ('audit_output\multi_task_partial_' + (Get-Date -Format 'yyyyMMdd_HHmmss')) }
if (Test-Path $RunRoot) { throw "Refusing to reuse existing run directory: $RunRoot" }
New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
$classes = Join-Path $RunRoot 'classes'
New-Item -ItemType Directory -Force -Path $classes | Out-Null
$classpath = "$jarRoot\*;$jarRoot\commons-math3-3.5\commons-math3-3.5.jar"
& $javac -encoding UTF-8 -cp $classpath -sourcepath "$simSource;$sourceRoot" -d $classes $source
if ($LASTEXITCODE -ne 0) { throw "javac failed: $LASTEXITCODE" }

$repeatRoot = Join-Path $RunRoot 'repeat'
foreach ($target in @($RunRoot, $repeatRoot)) {
    if ($target -eq $repeatRoot) { New-Item -ItemType Directory -Force -Path $target | Out-Null }
    & $java -cp "$classes;$classpath" org.fog.test.perfeval.MultiTaskPartialOffloadingSpike $target $Tasks $InterArrivalMs
    if ($LASTEXITCODE -ne 0) { throw "Partial multi-task simulation failed in $target" }
    & $PythonExe $validator --root $target --tasks $Tasks
    if ($LASTEXITCODE -ne 0) { throw "Partial multi-task trace validation failed in $target" }
}
foreach ($name in @('partial_trace.csv', 'partial_summary.csv')) {
    $first = Get-Content -LiteralPath (Join-Path $RunRoot $name) -Raw
    $second = Get-Content -LiteralPath (Join-Path $repeatRoot $name) -Raw
    if ($first -cne $second) { throw "Fixed-seed repeatability mismatch: $name" }
}
[ordered]@{
    task_count = $Tasks
    inter_arrival_ms = $InterArrivalMs
    primary_validator = 'PASS'
    repeat_validator = 'PASS'
    trace_byte_identical = $true
    summary_byte_identical = $true
} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $RunRoot 'repeatability.json')
if (Test-Path $classes) { Remove-Item -LiteralPath $classes -Recurse -Force }
Write-Host "PASS: multi-task partial acceptance and deterministic repeat written to $RunRoot"
