# Research-gap verdict v26 (28 October 2026)

## Decision
No new algorithmic research gap is confirmed by the current literature screen. The broad ideas “Q-learning for local/edge/cloud offloading”, “deadline-aware contextual offloading”, “risk-aware reward”, “adaptation to workload/network shifts”, “heterogeneous deadlines”, and “node-failure fallback” all have close prior art. See `prior_art_evidence_matrix.csv` for DOI, method, overlap, source and full-text access grade.

## Directly relevant evidence
- E2DA (IEEE GLOBECOM 2023; DOI 10.1109/GLOBECOM54140.2023.10437602): contextual neural bandit, partial observation, deadline-aware edge offloading.
- O2C/CCMAB (IEEE ICC 2026; DOI 10.1109/ICC59461.2026.11586921): learns delay distributions under chance-constrained latency reliability.
- Forecast-driven MEC (JNCA 2026; DOI 10.1016/j.jnca.2026.104494): TimesNet forecasts load/failures for LinUCB offloading.
- LITO (Sensors 2026; DOI 10.3390/s26051497): edge–fog–cloud, contextual-bandit feedback, EDF-DRS, heterogeneous task deadlines, feasibility filtering, fallback, and node-failure evaluation.
- H-DQAC (JESA 2025; DOI 10.18280/jesa.581016): hybrid DQL/Actor-Critic, QoS-aware offloading evaluated in iFogSim2.
- RELTO (Ad Hoc Networks 2026; DOI 10.1016/j.adhoc.2025.104065) and DNN-PPO/CVaR (Computer Communications 2026; DOI 10.1016/j.comcom.2026.108610) cover reliability-oriented multi-objective DRL and tail-risk/SLA control.
- Chance-constrained dependent-task offloading (Applied Soft Computing 2026; DOI 10.1016/j.asoc.2026.115710) and deadline-aware cell-free MEC (Computer Networks 2026; DOI 10.1016/j.comnet.2026.112219) add further direct overlap.

## Evidence grade / limitations
This is a focused, source-verified screening, not a claim of exhaustive systematic review. Full publisher text and equation-by-equation comparisons are available for some open-access papers (notably LITO and H-DQAC), but the full IEEE ICC text/equations for O2C and some paywalled papers were not independently extracted. Preprints (e.g., FleetGuard) are marked as preprints, not peer-reviewed proof.

## Defensible contribution path
If the supervisor accepts a comparative/reproducibility study, frame the contribution as a controlled iFogSim2 evaluation with: (1) explicit Sensor-emission-to-first-module-completion timing; (2) heterogeneous deadlines; (3) matched workload, network-latency, and Edge-capacity shifts; (4) Edge compute-service outage/recovery with action masking and failover; and (5) transparent per-run logs, paired seeds, and confidence intervals. This is a carefully scoped empirical contribution candidate, not guaranteed novelty. The novelty claim requires a final search log and supervisor approval.

If a new algorithm is mandatory, do not simply rename Q-learning or combine “deadline + risk + failure.” Define a mechanism that differs in equations from O2C, LITO, H-DQAC, forecast-driven LinUCB and CVaR methods; use development seeds for tuning and fresh held-out seeds for final testing.
