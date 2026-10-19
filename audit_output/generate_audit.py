"""Reproducible, read-only package audit.  Run from repository root with Python 3.10+."""
from __future__ import annotations
import csv, json, math, re, statistics, sys, zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "team-work" / "Mostafa" / "Dataset"
OUT = Path(__file__).resolve().parent

TEXT = {".md", ".txt", ".bib", ".py", ".json", ".jsonl"}
STRUCT = {".csv", ".tsv"}
DOC = {".pdf", ".docx"}

def kind(p):
    x=p.suffix.lower()
    if x in STRUCT: return "structured data"
    if x in {".xlsx", ".xls"}: return "spreadsheet"
    if x in {".zip", ".gz", ".tar", ".tgz"}: return "archive"
    if x in DOC: return "document"
    if x in TEXT: return "documentation/code/metadata"
    return "other"

def read_csv(p):
    raw=p.read_bytes()
    encoding="utf-8-sig"
    try: text=raw.decode(encoding)
    except UnicodeDecodeError:
        encoding="latin-1"; text=raw.decode(encoding)
    sample=text[:16384]
    try: dialect=csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error: dialect=csv.excel
    rows=list(csv.reader(text.splitlines(), dialect))
    if not rows: raise ValueError("empty file")
    header=rows[0]; body=rows[1:]
    malformed=sum(1 for r in body if len(r)!=len(header))
    body=[r for r in body if len(r)==len(header)]
    missing=[sum(1 for r in body if not r[i].strip()) for i in range(len(header))]
    dupe=len(body)-len({tuple(r) for r in body})
    cols=[]
    for i,n in enumerate(header):
        vs=[r[i].strip() for r in body if r[i].strip()]
        vals=[]; allnum=bool(vs)
        inf=0
        for v in vs:
            try:
                f=float(v); vals.append(f); inf += not math.isfinite(f)
            except ValueError: allnum=False
        typ="numeric" if allnum else "string"
        cols.append({"column":n,"dtype":typ,"missing":missing[i],"infinite":inf,"distinct":len(set(vs)),"values":vals if allnum else []})
    return {"encoding":encoding,"delimiter":repr(dialect.delimiter),"rows":len(body),"columns":len(header),"header":header,"missing":missing,"duplicates":dupe,"malformed":malformed,"cols":cols,"sample":body[:3]}

def q(xs,p):
    if not xs:return None
    z=sorted(xs); pos=(len(z)-1)*p; lo=int(pos); hi=math.ceil(pos)
    return z[lo] if lo==hi else z[lo]+(z[hi]-z[lo])*(pos-lo)
def fmt(v): return "" if v is None else (f"{v:.10g}" if isinstance(v,float) else str(v))

files=[]; analyses={}; failures=[]
for p in sorted(DATA.rglob("*")):
    if not p.is_file(): continue
    rel=p.relative_to(ROOT).as_posix(); entry={"relative_path":rel,"file_type":kind(p),"size_bytes":p.stat().st_size,"inspected":"yes","classification":"documentation/metadata"}
    try:
        if p.suffix.lower() in STRUCT:
            a=read_csv(p); analyses[rel]=a; entry["classification"]="data"; entry["notes"]=f"{a['rows']} data rows; {a['columns']} columns; parsed {a['encoding']} {a['delimiter']}"
        elif p.suffix.lower()==".json": json.loads(p.read_text(encoding="utf-8")); entry["classification"]="metadata/schema"
        elif p.suffix.lower() in {".zip"}:
            with zipfile.ZipFile(p) as z: entry["notes"]=f"archive readable; {len(z.infolist())} entries; nested archives: {sum(x.filename.lower().endswith('.zip') for x in z.infolist())}"
        elif p.suffix.lower() in {".xlsx", ".docx"}:
            with zipfile.ZipFile(p) as z:
                names=z.namelist(); entry["notes"]=f"OOXML container readable; {len(names)} entries"
                if p.suffix.lower()==".xlsx":
                    wb=z.read("xl/workbook.xml").decode("utf-8",errors="replace"); entry["notes"] += "; sheets: " + ", ".join(re.findall(r'<sheet[^>]* name="([^"]+)',wb))
        elif p.suffix.lower()==".pdf":
            if not p.read_bytes().startswith(b"%PDF"): raise ValueError("missing PDF signature")
            entry["notes"]="PDF signature verified; text/layout not extracted because no PDF parser is declared/available"
    except Exception as e:
        entry["inspected"]="partial"; entry["notes"]=f"parse issue: {type(e).__name__}: {e}"; failures.append(rel+": "+entry["notes"])
    files.append(entry)

def write_csv(name, fields, rows):
    with (OUT/name).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
write_csv("DATASET_FILE_INVENTORY.csv",["relative_path","file_type","size_bytes","inspected","classification","notes"],files)

quality=[]; summary=[]; uci=[]
for rel,a in analyses.items():
    quality.append({"relative_path":rel,"parse_status":"ok","encoding":a["encoding"],"delimiter":a["delimiter"],"rows":a["rows"],"columns":a["columns"],"column_names":" | ".join(a["header"]),"missing_values":" | ".join(f"{n}:{m}" for n,m in zip(a["header"],a["missing"])),"duplicate_rows":a["duplicates"],"malformed_rows":a["malformed"],"notes":"exact full-file read"})
    for c in a["cols"]:
        if c["dtype"]=="numeric" and c["values"]:
            xs=c["values"]; summary.append({"relative_path":rel,"column":c["column"],"count":len(xs),"mean":fmt(statistics.mean(xs)),"median":fmt(statistics.median(xs)),"stddev":fmt(statistics.stdev(xs)) if len(xs)>1 else "","min":fmt(min(xs)),"p25":fmt(q(xs,.25)),"p75":fmt(q(xs,.75)),"p95":fmt(q(xs,.95)),"max":fmt(max(xs)),"units":"unknown unless stated in source documentation","notes":"exact; numeric parse of non-empty cells"})
    if "08_UCI_Image_Recognition_MEC/raw/uci_extracted/final/TATDescriptionDataset/" in rel and "Execution Time" in a["header"]:
        c=next(x for x in a["cols"] if x["column"]=="Execution Time"); xs=c["values"]
        uci.append({"file":Path(rel).name,"environment_inferred_from_filename":Path(rel).stem,"metric":"Execution Time","count":len(xs),"mean":fmt(statistics.mean(xs)),"median":fmt(statistics.median(xs)),"stddev":fmt(statistics.stdev(xs)),"min":fmt(min(xs)),"p25":fmt(q(xs,.25)),"p75":fmt(q(xs,.75)),"p95":fmt(q(xs,.95)),"max":fmt(max(xs)),"units":"seconds per local documentation; verify against official PDF","missing":c["missing"],"duplicate_rows":a["duplicates"]})
write_csv("DATASET_QUALITY_REPORT.csv",["relative_path","parse_status","encoding","delimiter","rows","columns","column_names","missing_values","duplicate_rows","malformed_rows","notes"],quality)
write_csv("DATASET_SUMMARY.csv",["relative_path","column","count","mean","median","stddev","min","p25","p75","p95","max","units","notes"],summary)
if uci: write_csv("UCI_DEVICE_STATISTICS.csv",list(uci[0]),uci)

uci_table="\n".join("| {file} | {count} | {mean} | {median} | {stddev} | {min} | {p25} | {p75} | {p95} | {max} |".format(**x) for x in uci) or "No readable local UCI execution-time CSV was found."
data_report=f'''# Dataset audit\n\n## Scope and method\n\nInspected every file under `team-work/Mostafa/Dataset` ({len(files)} files), parsed all accessible CSV/TSV files ({len(analyses)}) in full with a standard-library CSV reader, parsed JSON, inspected ZIP/OOXML containers, and verified PDF signatures. Exact per-file inventory, quality results, and numeric results are in the companion CSVs. No original teammate file was modified. External websites were **not independently verified** in this audit.\n\n## Locally present data\n\nThe actual measurement data are the four UCI CSVs below and three EUA CSVs. Google Cluster has only JSON schema files. The other named candidate datasets are represented by research documentation/metadata and mapping workbooks, not their raw records. Network-security traffic data must not be treated as computational task traces.\n\n## UCI Image Recognition MEC (local, fully parsed)\n\nThe extracted archive contains `MacBookPro1.csv`, `MacBookPro2.csv`, `VM.csv`, and `RasberryPi.csv`. The filename supports only an environment label, not Local/Edge/Cloud semantics. The documentation states that `Execution Time` is turnaround time for an image-recognition task; it must therefore not be decomposed into, or added to, separate network and computation delays without a source-supported methodology. It has no action label, task size, deadline, bandwidth, energy, or resource-utilization field. It is calibration/reference data, not a complete offloading dataset.\n\n| File | n | mean | median | sd | min | p25 | p75 | p95 | max |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n{uci_table}\n\nUnits are retained as documented locally (seconds) and should be checked against the experimental-description PDF before publication. The full computed values, missing counts, duplicates, and schema are in `UCI_DEVICE_STATISTICS.csv` and `DATASET_QUALITY_REPORT.csv`.\n\n## Candidate suitability\n\n| Dataset | Verified local availability | Relevant fields available | Missing fields | Measured vs derived | Confidence | Role / recommendation |\n|---|---|---|---|---|---|---|\n| UCI Image Recognition MEC | Four parsed execution-time CSVs + nested archives | time, execution time | task size, action/location, network, deadline, energy, utilization | measured turnaround time; no derived labels | local files high; external license/source not independently checked | Calibration/reference only; do not invent tiers |\n| EUA | Three parsed location/user CSVs | user/site coordinates/context | task execution/outcomes, network measurements, actions | local tabular records; mapping requires assumptions | local availability high | topology/context, not policy labels |\n| Google Cluster | schemas only | field definitions only | raw records locally | metadata only | local availability low | download/verify before workload use |\n| ToN-IoT, CICIoT2023, UNSW-IoTraffic, Bot-IoT, UNSW-NB15 | documentation/metadata only | security/network context described | computational task outcomes and tier actions | no local raw data inspected | documentation-only | security/network traffic only; not direct offloading evidence |\n\n## Practical strategy and provenance\n\n1. **Immediate:** use UCI only to sanity-check a simulated image-recognition turnaround-time distribution and EUA only for geography/topology context; retain file/environment provenance.\n2. **Further work:** verify official dataset pages, license/access conditions, and download a workload source only when its field definitions match the simulation.\n3. **Simulator-generated:** task MI, deadlines, tier placement, link delay/bandwidth, queueing, outcome, utilization, and energy must be generated/measured by iFogSim and recorded as `SIMULATED` unless a validated external measurement is used.\n4. **Derived:** any conversion/distribution fit must state the formula and source as `DERIVED`; manually selected values are `ASSUMED`; raw recorded values are `MEASURED`. Never merge these labels.\n\n## Quality notes\n\nCSV results are exact full-file values. Numeric type inference is conservative: an all-nonempty-numeric column is numeric; otherwise it is string. This audit did not silently discard malformed rows (their count is reported). Excel containers were inspected for workbook structure but not cell values because the declared `openpyxl` dependency was unavailable in the audit environment. PDF signatures were checked but content was not text-extracted for the same reason.\n'''
(OUT/"DATASET_AUDIT.md").write_text(data_report,encoding="utf-8")

rl='''# RL model audit\n\n## Actual implementation\n\n`team-work/Ayoub/rl_model/rl_model` is a Python 3.10+ tabular Q-table service. It exposes exactly `Local` (0), `Edge` (1), and `Cloud` (2), reads JSON Lines over stdin/stdout, records a pending decision by task id, and learns only after a separate outcome. The action, observation, and outcome schemas/examples plus unit tests are present. There is no Java/iFogSim source/client in the repository; `simulator/README.md` explicitly says production Java code is not committed.\n\nDefault enabled state: `task_mi`, `wan_latency_ms`, `edge_utilization`, `deadline_ms`. Their bin counts 3×3×3×2 yield 54 states. Threshold boundaries use `bisect_right`: a value equal to a threshold enters the higher bin. Inputs must be finite and satisfy declared min/max; unknown features and empty action masks are rejected. Disabled `device_utilization` is accepted only as disabled input and is not encoded.\n\n## Algorithm classification\n\nThe default config has `decision_model=contextual_bandit` and `gamma=0.0`; validation requires gamma zero for that mode. Thus its executed update is `Q(s,a) ← Q(s,a)+0.1*(reward-Q(s,a))`, not sequential Q-learning. The general bootstrapped rule exists for `decision_model=sequential`, positive gamma, non-terminal outcomes, and a valid next observation. That configuration needs a scientifically defined next decision point; it is not supplied by the repository. Training is epsilon-greedy (0.30 linearly to 0.02 over 16,000 decisions), while frozen evaluation is greedy with unvisited-state fallback Edge→Cloud→Local.\n\n## Reward\n\n`reward = -(1.0*clipped_latency + 2.0*deadline_miss + 0.5*resource_cost)`. Latency is clipped at 1 after normalizing by fixed 1000 ms; cost is a weighted capped combination of bandwidth (required, reference 1,000,000 bytes) and energy (optional, reference 10 J). Failures use max latency and a deadline miss; failure penalty is 0. All weights, references, task/deadline bins, and fallback order are placeholders or design choices—not calibrated scientific parameters. A completed task without required bandwidth is rejected, so no learning update occurs. There is no obvious arithmetic double count within the implemented reward, but using UCI turnaround time plus simulated communication time would double count if treated as separate components.\n\n## Protocol and integration readiness\n\nThe protocol correctly separates pre-decision observation, selected action, and post-execution outcome; it handles malformed messages, duplicate task/outcome IDs, action masks, terminal/next-state conditions, model compatibility, and atomic persistence. However the repository has no verified Java client, no actual routing/action application, no outcome collector, and no iFogSim run log. `latency_ms`, bandwidth scope, energy, node utilization, failure semantics, Python timeout/fallback, and units/timing remain Java-side confirmations. The root `integration/protocol/agent-message-schema.json` is a preliminary draft using different field names from the model protocol, so a single contract must be selected before integration.\n\n## Legacy code\n\n`legacy/toy_prototype_original.py` is a synthetic illustration: it hardcodes an invented `run_task` environment and prints a baseline comparison. It must not be cited as experimental evidence.\n\n## Test audit\n\nThe source contains pytest tests for actions, state, reward, agent, protocol, server, persistence, aggregation, and fixtures. This audit could not execute pytest because the workstation had no usable project interpreter and creation of an isolated venv failed (`venvlauncher.exe` missing from the only usable embedded Python distribution). No prior README claim is treated as a result. See `TEST_RESULTS.md`.\n'''
(OUT/"RL_MODEL_AUDIT.md").write_text(rl,encoding="utf-8")

tests='''# Test results\n\n## Environment discovery\n\n- Repository declared Python requirement: `>=3.10`.\n- System `python`: not found. `py -0p`: no installed Pythons.\n- An embedded Python 3.11.4 from Cinema 4D was usable for standard-library execution, but it had no pytest/jsonschema and could not create a venv: `Unable to copy ... venvlauncher.exe` / WinError 2.\n- No dependencies were installed and no source/test file was changed.\n\n## Attempted test setup\n\n```text\n<embedded-python> -m venv .audit_venv\nexit: 1\nUnable to copy ... venvlauncher.exe\n```\n\nTherefore `pytest -q` was **not run** and has no pass/fail result in this audit. The model was still syntax/import/protocol smoke-tested with the embedded standard-library Python; see the generated demonstration transcript/log files if present. A suitable Python install and `pip install -r requirements.txt` in a fresh project-local venv are required before claiming the suite result.\n'''
(OUT/"TEST_RESULTS.md").write_text(tests,encoding="utf-8")

check='''# Java/iFogSim integration checklist\n\n- [ ] Choose the canonical protocol; reconcile root draft fields (`task_size`, `network_latency`, `deadline_category`) with `rl_model` fields (`task_mi`, `wan_latency_ms`, `deadline_ms`).\n- [ ] Implement one persistent Python subprocess per simulation run; UTF-8 JSONL, one synchronous reply per line, drain stderr.\n- [ ] Before placement, send `hello` then an observation with finite, unit-consistent values and available actions.\n- [ ] Apply the returned Local/Edge/Cloud action to real iFogSim routing; record the actual executed destination.\n- [ ] After completion/failure, send measured `latency_ms`, `deadline_met`, status/reason, required `bandwidth_bytes`, and available energy/utilization.\n- [ ] Define latency endpoints, which network links count toward bandwidth, energy model, and edge-utilization sampling instant.\n- [ ] Calibrate state bins and reward references/weights from documented workload/topology ranges.\n- [ ] Decide contextual bandit versus sequential MDP. For sequential use, define valid episodes and next states.\n- [ ] Implement timeout/error fallback and ensure fallback tasks are not falsely reported as agent-selected outcomes.\n- [ ] Run a one-task end-to-end trace and verify task id, action, destination, and feedback match.\n- [ ] Run train/test separation with matched seeds and Local/Edge/Cloud fixed baselines; aggregate only genuine simulator logs.\n'''
(OUT/"INTEGRATION_CHECKLIST.md").write_text(check,encoding="utf-8")

brief='''# Supervisor briefing\n\n**Verified:** a local UCI execution-time package and EUA CSVs are present and parsed; a Python tabular contextual-bandit service, protocol, schemas, persistence, and test source exist.\n\n**Not verified:** official online provenance/licensing, Java/iFogSim integration, reward metrics from a simulator, or any comparative policy result. The default policy learner is a contextual bandit, not a sequential MDP.\n\n**Dataset support:** UCI supports turnaround-time calibration/reference by filename-labeled environment; it does not provide Local/Edge/Cloud labels, task size, network, deadline, energy, or decisions. Security datasets documented here are not computational offloading task records.\n\n**Supervisor decisions:** approve the task/deadline distributions; define metric units/endpoints; select/calibrate reward weights; choose bandit vs MDP; approve a fair seeds/baselines/repetitions plan.\n\n**Next:** implement and test one Java-to-Python-to-Java task loop, then generate measured run logs before making any performance claim.\n'''
(OUT/"DOCTOR_BRIEFING.md").write_text(brief,encoding="utf-8")

repro='''# Reproduce audit\n\nFrom repository root, use Python 3.10+ with no third-party dependencies required for the core dataset audit:\n\n```text\npython audit_output/generate_audit.py\n```\n\nFor model tests, create a working local virtual environment using a normal CPython distribution, then:\n\n```text\npython -m venv .audit_venv\n.audit_venv\\Scripts\\python -m pip install -r team-work\\Ayoub\\rl_model\\rl_model\\requirements.txt\ncd team-work\\Ayoub\\rl_model\\rl_model\n..\\..\\..\\..\\.audit_venv\\Scripts\\python -m pytest -q\n```\n\nThe generator uses full-file CSV reads and emits the inventory, quality report, numeric summary, UCI per-file statistics, and narrative reports in this directory. It does not modify source datasets or the model.\n'''
(OUT/"REPRODUCE_AUDIT.md").write_text(repro,encoding="utf-8")

final=f'''# Final audit report\n\n## Executive summary\n\nPaths audited: `team-work/Mostafa/Dataset` and `team-work/Ayoub/rl_model/rl_model`. Git branch: `main`; pre-existing unrelated modifications were present in `team-work/Astta-Abdo/adaptive_offloading/adaptive_offloading.py` and `test.py` and were not touched. No repository instruction (`AGENTS.md`) was found.\n\nThe dataset package contains useful research documentation plus local UCI execution-time and EUA context data, but no locally complete empirical Local/Edge/Cloud task-offloading dataset. The RL component is a substantially implemented tabular contextual-bandit service with a clear protocol and safeguards, but it has no Java/iFogSim client or genuine simulator evidence. It is code-ready for a controlled bridge implementation, not research-evaluation ready.\n\n## Dataset\n\nSee `DATASET_AUDIT.md`, `DATASET_FILE_INVENTORY.csv`, `DATASET_QUALITY_REPORT.csv`, `DATASET_SUMMARY.csv`, and `UCI_DEVICE_STATISTICS.csv`. All CSV/TSV data files were fully parsed. Exact summary values are generated from source files rather than copied from documentation.\n\n## Model and tests\n\nSee `RL_MODEL_AUDIT.md` and `TEST_RESULTS.md`. The test suite could not be executed because a compliant isolated environment could not be created; that is an environment blocker, not a pass/fail claim.\n\n## Fair experiment design\n\nCompare Local-only, Edge-only, Cloud-only, and frozen adaptive policy using identical generated workload traces, topology/dynamic-condition schedules, and simulator seeds. Record: end-to-end latency in ms (task creation to result at device), deadline violation rate (failed or deadline missed / all tasks), completion rate (completed / all), bandwidth bytes/task, node utilization (defined sampling/aggregation), and energy J/task only if the model truly supplies it. Run repeated distinct test seeds, separate training seeds, and never compare a learning policy while it is updating in test.\n\n## Priority next steps\n\n1. Reconcile and implement one canonical Java/Python protocol and prove a single task’s selected action changes iFogSim routing.\n2. Document/measure every state and reward metric’s units, endpoint, timing, and availability.\n3. Obtain supervisor approval for contextual bandit versus MDP, workload/deadline assumptions, and reward calibration.\n4. Install a normal CPython environment, run the complete pytest suite, and retain its actual output.\n5. Implement matched fixed baselines and repeated-seed simulator experiments before any performance conclusion.\n'''
(OUT/"FINAL_AUDIT_REPORT.md").write_text(final,encoding="utf-8")

summary={"audit_status":"completed_with_environment_test_blocker","paths":{"dataset":"team-work/Mostafa/Dataset","rl_model":"team-work/Ayoub/rl_model/rl_model"},"dataset_files_inspected":len(files),"structured_files_analyzed":len(analyses),"uci_statistics_generated":bool(uci),"tests":{"pytest":"not_run","reason":"no usable project interpreter; isolated venv creation failed"},"integration":{"java_client_present":False,"ifogsim_run_verified":False},"known_blockers":["missing committed Java/iFogSim integration","uncalibrated state/reward parameters","protocol draft mismatch","no executed test suite in this audit"],"changes_to_teammate_files":[]}
(OUT/"AUDIT_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps({"files":len(files),"csvs":len(analyses),"uci":len(uci),"failures":failures},indent=2))
