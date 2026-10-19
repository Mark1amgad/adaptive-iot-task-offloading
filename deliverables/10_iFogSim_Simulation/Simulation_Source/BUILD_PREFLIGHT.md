# Integration prototype build preflight

## Result

The current iFogSim source closure for both existing entry points compiled successfully with JDK 25 into the isolated directory `audit_output/integration_prototype/classes_preflight`. The external project output directory `C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\out\production\iFogSim` was not written.

Command executed from the main repository root:

```powershell
$srcRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\src'
$outRoot = 'audit_output\integration_prototype\classes_preflight'
$jdk = 'C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot\bin\javac.exe'
$jarRoot = 'C:\Users\DELL\OneDrive\Desktop\Research\iFogSim\jars'
$classpath = "$jarRoot\*;$jarRoot\commons-math3-3.5\commons-math3-3.5.jar"
& $jdk -encoding UTF-8 -cp $classpath -sourcepath $srcRoot -d $outRoot `
  "$srcRoot\org\fog\test\perfeval\AdaptiveOffloadingFog.java" `
  "$srcRoot\org\fog\test\perfeval\DCNSFog.java"
```

Observed compiler result: exit code 0. JDK emitted only deprecation/unchecked-operation notes.

The existing Java 25 launch also remains verified for the precompiled baseline: AdaptiveOffloadingFog and DCNSFog both exited 0. This does not constitute an RL-integration result.
