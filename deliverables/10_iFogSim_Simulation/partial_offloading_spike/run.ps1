param(
    [string]$SimulatorRoot = (Join-Path (Split-Path (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path -Parent) 'iFogSim')
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$sourceFile = Join-Path $PSScriptRoot 'src\org\fog\test\perfeval\PartialOffloadingFeasibilitySpike.java'
$classOutput = Join-Path $PSScriptRoot 'build\classes'
$jarRoot = Join-Path $SimulatorRoot 'jars'
$simSource = Join-Path $SimulatorRoot 'src'

$jdkRoot = if ($env:JAVA_HOME) {
    $env:JAVA_HOME
} else {
    'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot'
}
$javac = Join-Path $jdkRoot 'bin\javac.exe'
$java = Join-Path $jdkRoot 'bin\java.exe'

foreach ($required in @($sourceFile, $javac, $java, $simSource, $jarRoot)) {
    if (-not (Test-Path $required)) {
        throw "Required path not found: $required"
    }
}

New-Item -ItemType Directory -Force -Path $classOutput | Out-Null
$runId = Get-Date -Format 'yyyyMMdd_HHmmss'
$runOutput = Join-Path $PSScriptRoot ("results\run_" + $runId)
New-Item -ItemType Directory -Force -Path $runOutput | Out-Null

$classpath = "$jarRoot\*;$jarRoot\commons-math3-3.5\commons-math3-3.5.jar"

Write-Host "Compiling isolated PartialOffloadingFeasibilitySpike..."
Write-Host "Simulator source: $simSource"
Write-Host "Class output: $classOutput"

Push-Location $repoRoot
try {
    & $javac -encoding UTF-8 -cp $classpath -sourcepath $simSource -d $classOutput $sourceFile
    if ($LASTEXITCODE -ne 0) {
        throw "javac failed with exit code $LASTEXITCODE"
    }

    $runtimeClasspath = "$classOutput;$classpath"
    Write-Host "Running spike; output: $runOutput"
    & $java -cp $runtimeClasspath org.fog.test.perfeval.PartialOffloadingFeasibilitySpike $runOutput
    if ($LASTEXITCODE -ne 0) {
        throw "Spike failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

Write-Host "PARTIAL_SPIKE_STATUS=PASS"
Write-Host "Artifacts: $runOutput"
