# iFogSim Research Topology GUI

This package uses iFogSim's existing GUI classes `Bridge`, `Graph`, and `GraphView`
to display the Local → Edge → Cloud topology used by the research integration.

## Files

- `ResearchTopologyGUI.java`: GUI entry point.
- `research_topology.json`: graph in the same general JSON structure as the supplied
  `routerTopology` example (`nodes` and `links`).

## Topology values

- Cloud: 44,800 MIPS, RAM 40,000 MB, up/down bandwidth 100,000.
- Edge: 2,800 MIPS, RAM 4,000 MB, up/down bandwidth 10,000.
- Local: 1,000 MIPS, RAM 2,000 MB, up/down bandwidth 10,000.
- Edge ↔ Cloud link latency: 45 ms.
- Local ↔ Edge link latency: 2 ms.

## Compile and run (PowerShell)

Run from the external iFogSim project folder. Adjust JDK and JAR paths if needed:

```powershell
$jdk = "C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot\bin"
$srcRoot = (Get-Location).Path + "\src"
$jarRoot = (Get-Location).Path + "\jars"
$out = Join-Path (Get-Location).Path "topology-gui-classes"

New-Item -ItemType Directory -Force $out | Out-Null

& "$jdk\javac.exe" -encoding UTF-8 `
  -cp "$jarRoot\*;$jarRoot\commons-math3-3.5\commons-math3-3.5.jar" `
  -sourcepath $srcRoot `
  -d $out `
  "$srcRoot\org\fog\gui\example\ResearchTopologyGUI.java"

if ($LASTEXITCODE -ne 0) { throw "Compilation failed." }

& "$jdk\java.exe" `
  -cp "$out;$srcRoot;$jarRoot\*;$jarRoot\commons-math3-3.5\commons-math3-3.5.jar" `
  org.fog.gui.example.ResearchTopologyGUI `
  (Join-Path (Get-Location).Path "research_topology.json")
```

## Important distinction

This opens a visual topology using iFogSim's GUI graph classes. It is **not** a simulation run,
does not connect to the Python RL agent, and does not produce experimental measurements.
The metrics shown are configuration labels; use `../Topology_Description.md` and the
experiment source as the authoritative implementation record. GUI layout/label wrapping
depends on the iFogSim GUI version.
