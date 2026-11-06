# Standalone Topology Presentation

## Purpose

`TopologyPresentation.java` is a standalone demonstration of the same three-device topology used by the existing research integration experiment. It is for explaining the topology and is **not** the RL integration run; it does not launch Python, send JSONL observations, or execute a research task. When run from Eclipse, it opens the existing iFogSim `GraphView` Swing window after printing the console report.

## Source

```text
C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src\org\fog\test\perfeval\TopologyPresentation.java
```

The source reuses the existing iFogSim constructors and creates actual `FogDevice` objects named `cloud`, `edge`, and `local`. It does not modify `DCNSFog.java`, `FogDevice.java`, `Controller.java`, the integration experiment, or teammate files.

## Build

Run from the research repository root:

```powershell
$out = 'audit_output\topology-work\presentation-classes'
$jdk = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot\bin\javac.exe'
$jarRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\jars'
$srcRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src'
New-Item -ItemType Directory -Force $out | Out-Null
& $jdk -encoding UTF-8 `
  -cp "$jarRoot\*;$jarRoot\commons-math3-3.5\commons-math3-3.5.jar" `
  -sourcepath $srcRoot -d $out `
  "$srcRoot\org\fog\test\perfeval\TopologyPresentation.java"
```

The build is isolated and does not write to iFogSim's existing compiled output.

## Run

```powershell
$java = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot\bin\java.exe'
$jarRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\jars'
& $java -cp "audit_output\topology-work\presentation-classes;$jarRoot\*;$jarRoot\commons-math3-3.5\commons-math3-3.5.jar" `
  org.fog.test.perfeval.TopologyPresentation `
  | Tee-Object audit_output\topology-work\presentation-run\console_output.txt
```

The demonstration initializes CloudSim, constructs the devices, creates the same executor module mapping, constructs a Controller to register child latency maps, prints the report, and stops without running a task simulation.

## Eclipse GUI Run

Import the external iFogSim folder as an Eclipse Java project, ensure the existing `jars` directory is on the project build path, then run:

```text
src/org/fog/test/perfeval/TopologyPresentation.java
Run As -> Java Application
```

The program generates a temporary GUI-compatible JSON file from the runtime device objects, passes it through `Bridge.jsonToGraph(...)`, and opens `GraphView`. The window shows the `cloud`, `edge`, and `local` FogDevices and their hierarchy. The footer labels the 2 ms and 45 ms Controller-derived links; Python is labeled outside the simulated topology as an external control plane.

An optional first program argument can be supplied to retain the generated GUI JSON at a chosen path. Without an argument, it uses a temporary file.

## Interpretation

The report's `host storage runtime: 990000` is the value returned by the runtime host object. The audited constructor passes `1000000` to `PowerHost`; this known discrepancy is documented in `VALIDATION_REPORT.md` and is not hidden.
