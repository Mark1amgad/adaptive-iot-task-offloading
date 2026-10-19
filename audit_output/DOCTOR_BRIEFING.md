# Supervisor briefing

**Verified:** a local UCI execution-time package and EUA CSVs are present and parsed; a Python tabular contextual-bandit service, protocol, schemas, persistence, and test source exist.

**Not verified:** official online provenance/licensing, Java/iFogSim integration, reward metrics from a simulator, or any comparative policy result. The default policy learner is a contextual bandit, not a sequential MDP.

**Dataset support:** UCI supports turnaround-time calibration/reference by filename-labeled environment; it does not provide Local/Edge/Cloud labels, task size, network, deadline, energy, or decisions. Security datasets documented here are not computational offloading task records.

**Supervisor decisions:** approve the task/deadline distributions; define metric units/endpoints; select/calibrate reward weights; choose bandit vs MDP; approve a fair seeds/baselines/repetitions plan.

**Next:** implement and test one Java-to-Python-to-Java task loop, then generate measured run logs before making any performance claim.
