param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path,
    [string]$IFogSimRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim',
    [string]$PythonExe = 'C:\Users\DELL\AppData\Roaming\uv\python\cpython-3.15.0b1-windows-x86_64-none\python.exe',
    [string]$JdkHome = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot',
    [string]$WorkloadFile = '',
    [string]$ModelIn = '',
    [string]$RiskStateIn = '',
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
$rlRoot = Join-Path $ProjectRoot 'deliverables\08_RL_Model'
$jarRoot = Join-Path $IFogSimRoot 'jars'
$sourceRoot = Join-Path $IFogSimRoot 'src'
$javac = Join-Path $JdkHome 'bin\javac.exe'
$java = Join-Path $JdkHome 'bin\java.exe'
foreach ($required in @($action,$plan,$contract,$experiment,$analyzer,$PythonExe,$javac,$WorkloadFile,$ModelIn)) {
    if (-not (Test-Path $required)) { throw "Required file not found: $required" }
}
if (-not $RiskStateIn) { $RiskStateIn = "$ModelIn.risk.json" }
if (-not (Test-Path $RiskStateIn)) { throw "Risk calibration state not found: $RiskStateIn. Train with --risk-filter first." }
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
$workloadRows = @(Get-Content -LiteralPath $WorkloadFile | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json })
if (-not $workloadRows -or $workloadRows.Count -lt 1) { throw "Workload is empty or invalid: $WorkloadFile" }
$seedValues = @($workloadRows | ForEach-Object { [string]$_.seed } | Select-Object -Unique)
$profileValues = @($workloadRows | ForEach-Object { [string]$_.profile } | Select-Object -Unique)
if ($seedValues.Count -ne 1 -or $profileValues.Count -ne 1) {
    throw "Workload rows must share exactly one seed and one profile."
}
$gitCommit = (& git -C $ProjectRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or -not $gitCommit) { throw "Cannot resolve source Git commit." }
$javaVersion = (Get-Content -LiteralPath (Join-Path $JdkHome 'release') |
    Where-Object { $_ -like 'JAVA_VERSION=*' } | Select-Object -First 1)
# Hash the actual source files used, not only Git HEAD: this also captures local edits
# in a working tree whose commit may be behind the remote branch.
$sourceFiles = @(
    Get-Item -LiteralPath @($action,$plan,$contract,$experiment,$analyzer,$PSCommandPath)
    Get-ChildItem -LiteralPath (Join-Path $rlRoot 'src') -Recurse -File -Filter '*.py'
    Get-ChildItem -LiteralPath (Join-Path $rlRoot 'config') -Recurse -File |
        Where-Object { $_.Extension -in @('.json','.yaml','.yml') }
) | Sort-Object FullName -Unique
$rootPrefix = $ProjectRoot.TrimEnd([char[]]@('\','/')) + [IO.Path]::DirectorySeparatorChar
$sourceInventory = @($sourceFiles | ForEach-Object {
    [ordered]@{
        path = $_.FullName.Substring($rootPrefix.Length).Replace([IO.Path]::DirectorySeparatorChar, '/')
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
    }
})
$manifest = [ordered]@{
    schema_version = "v1"
    experiment_id = [IO.Path]::GetFileName($OutputRoot)
    evaluation_split = "test"
    workload_seed = $seedValues[0]
    workload_profile = $profileValues[0]
    workload_file = [IO.Path]::GetFileName($WorkloadFile)
    workload_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $WorkloadFile).Hash.ToLowerInvariant()
    model_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $ModelIn).Hash.ToLowerInvariant()
    risk_state_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $RiskStateIn).Hash.ToLowerInvariant()
    source_git_commit = $gitCommit
    source_inventory = $sourceInventory
    java_version = $javaVersion
    simulator_root = [IO.Path]::GetFullPath($IFogSimRoot)
    simulator_jar_inventory = @(
        Get-ChildItem -LiteralPath $jarRoot -Filter '*.jar' -File |
        Sort-Object Name |
        ForEach-Object { [ordered]@{ name = $_.Name; sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant() } }
    )
    parameters = [ordered]@{
        partition_overhead_ms = $PartitionOverheadMs
        merge_overhead_ms = $MergeOverheadMs
        wan_latency_ms = $WanLatencyMs
        watchdog_ms = $WatchdogMs
    }
    policies = @('local','edge','cloud','random','rl_eval')
    created_at_utc = [DateTime]::UtcNow.ToString('o')
}
$manifestPath = Join-Path $OutputRoot 'experiment_manifest.json'
$manifestJson = $manifest | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText($manifestPath, $manifestJson + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
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
$rlArgs = @('-cp',$javaClasspath,'org.fog.test.perfeval.RlOffloadingV2PartialIntegrationExperiment','--output',$rlOut,'--run-id','paired-rl-eval','--mode','eval','--model-in',$ModelIn,'--evaluation-mode') + $common + @('--risk-filter','--risk-state-in',$RiskStateIn)
& $java @rlArgs
if ($LASTEXITCODE -ne 0) { throw "RL evaluation policy failed: $LASTEXITCODE" }
& $PythonExe $analyzer --root $OutputRoot --workload $WorkloadFile --manifest $manifestPath
if ($LASTEXITCODE -ne 0) { throw "Policy comparison analysis failed: $LASTEXITCODE" }
Write-Host "PASS: paired policy comparison completed. Artifacts: $OutputRoot"
