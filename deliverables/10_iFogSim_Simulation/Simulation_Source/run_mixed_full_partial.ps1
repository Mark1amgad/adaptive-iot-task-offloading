param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$IFogSimRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim',
    [string]$JdkHome = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot',
    [string]$PythonExe = 'C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.15.0b1-windows-x86_64-none\python.exe',
    [int]$Tasks = 6,
    [double]$InterArrivalMs = 1.0,
    [string]$RunRoot = ''
)
$ErrorActionPreference = 'Stop'
$sourceRoot = $PSScriptRoot
$source = Join-Path $sourceRoot 'org\fog\test\perfeval\MixedMultiTaskOffloadingSpike.java'
$validator = Join-Path $sourceRoot 'validate_mixed_full_partial.py'
$jarRoot = Join-Path $IFogSimRoot 'jars'
$simSource = Join-Path $IFogSimRoot 'src'
$javac = Join-Path $JdkHome 'bin\javac.exe'
$java = Join-Path $JdkHome 'bin\java.exe'
if ($Tasks -ne 6) { throw 'The current deterministic mixed fixture requires exactly 6 tasks (3 full + 3 partial)' }
if ($InterArrivalMs -le 0) { throw 'InterArrivalMs must be positive' }
if (-not (Test-Path $source)) { throw "Source not found: $source" }
if (-not (Test-Path $PythonExe)) { throw "Python not found: $PythonExe" }
if (-not $RunRoot) { $RunRoot = Join-Path $ProjectRoot ('audit_output\mixed_full_partial_' + (Get-Date -Format 'yyyyMMdd_HHmmss')) }
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
    & $java -cp "$classes;$classpath" org.fog.test.perfeval.MixedMultiTaskOffloadingSpike $target $Tasks $InterArrivalMs
    if ($LASTEXITCODE -ne 0) { throw "Mixed full/partial simulation failed in $target" }
    & $PythonExe $validator --root $target --tasks $Tasks
    if ($LASTEXITCODE -ne 0) { throw "Mixed full/partial validation failed in $target" }
}
foreach ($name in @('mixed_trace.csv', 'mixed_summary.csv')) {
    $first = Get-Content -LiteralPath (Join-Path $RunRoot $name) -Raw
    $second = Get-Content -LiteralPath (Join-Path $repeatRoot $name) -Raw
    if ($first -cne $second) { throw "Mixed full/partial repeatability mismatch: $name" }
}
[ordered]@{
    task_count = $Tasks
    full_tasks = 3
    partial_tasks = 3
    full_actions = @('Local', 'Edge', 'Cloud')
    inter_arrival_ms = $InterArrivalMs
    primary_validator = 'PASS'
    repeat_validator = 'PASS'
    trace_byte_identical = $true
    summary_byte_identical = $true
} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $RunRoot 'repeatability.json')
if (Test-Path $classes) { Remove-Item -LiteralPath $classes -Recurse -Force }
Write-Host "PASS: mixed full/partial lifecycle and deterministic repeat written to $RunRoot"
