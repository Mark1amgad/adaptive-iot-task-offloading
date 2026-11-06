# iFogSim Research Topology GUI

This package uses the existing iFogSim GUI classes `Bridge`, `Graph`, and `GraphView`
to display the Local -> Edge -> Cloud topology tested in the research integration.

## Files
- `ResearchTopologyGUI.java`: GUI entry point.
- `research_topology.json`: graph in the same general JSON structure as the supplied
  `routerTopology` example (`nodes` and `links`).

## Topology values
- Cloud: 44,800 MIPS, RAM 40,000 MB, up/down bandwidth 100,000.
- Edge: 2,800 MIPS, RAM 4,000 MB, up/down bandwidth 10,000.
- Local: 1,000 MIPS, RAM 2,000 MB, up/down bandwidth 10,000.
- Edge <-> Cloud link latency label/value: 45 ms.
- Local <-> Edge link latency label/value: 2 ms.

## Put the files in iFogSim
Copy `ResearchTopologyGUI.java` to:
`iFogSim/src/org/fog/gui/example/ResearchTopologyGUI.java`

Copy `research_topology.json` to the iFogSim project root (the working directory
from which you launch the class), or pass its absolute path as the first argument.

## Compile and run (PowerShell)
Run from your iFogSim project folder. Adjust JDK and jar paths if yours differ:

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
This opens a visual topology using iFogSim's GUI graph classes. It is not itself a simulation
run and does not connect to the Python RL agent. The metrics are shown as node labels, and
the link JSON records contain the configured latencies. Graph layout/label wrapping depends
on the version of the iFogSim GUI code.
