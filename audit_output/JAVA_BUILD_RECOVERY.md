# Java build recovery plan

## Evidence

- Project is Eclipse-based: `.project` and `.classpath`; no Maven/Gradle build descriptor.
- Source root: `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src`.
- Existing output: `...\out\production\iFogSim`.
- `.classpath` lists a generic Eclipse JRE container and bundled JARs; it specifies no Java source/target release.
- Installed JDKs: Temurin 8 (`jdk-8.0.504.1-hotspot`) and Temurin 25 (`jdk-25.0.3.9-hotspot`).
- Existing class files report version 69.0 (Java 25). Java 8 accepts only through version 52.0, explaining the earlier `UnsupportedClassVersionError`.

## Verified recovery

Launching the existing compiled output with the installed Java 25 executable and existing classpath succeeded:

- `AdaptiveOffloadingFog`: exit 0, topology creation.
- `DCNSFog`: exit 0, simulation and aggregate reports.

No source rebuild occurred. The failure was an invocation/JDK selection mismatch, not evidence of a source failure.

## Safe strategy

1. **Use JDK 25 for the current precompiled baseline.** Configure Eclipse/IntelliJ run configuration to `C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot` and retain the existing source/classpath. This is the safest way to reproduce the current baseline.
2. **Do not rebuild into `out\production\iFogSim`.** It contains pre-existing compiled worktree changes and local experiment artifacts.
3. **For any source rebuild, create a separate output directory** such as an external temporary or explicitly approved `build-audit\classes`, retain source/JAR classpath, and capture compiler/JDK/exit output. First compile only after the team approves a build-output location.
4. **Do not assume Java 8 compatibility.** The source has not been clean-built with either JDK in this audit. If a Java 8 build is desired, do it separately with explicit `-source/-target` or IDE settings only after resolving third-party library compatibility.
5. **Before integration development, pin the JDK in project documentation/run configuration** and record the exact classpath. Prefer JDK 25 until a clean build proves another target.

## Example non-destructive launch

```powershell
$root = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim'
$java = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot\bin\java.exe'
$cp = "$root\out\production\iFogSim;$root\jars\*;$root\jars\commons-math3-3.5\commons-math3-3.5.jar"
& $java -cp $cp org.fog.test.perfeval.DCNSFog
```

This runs existing artifacts only; it does not compile or overwrite them.
