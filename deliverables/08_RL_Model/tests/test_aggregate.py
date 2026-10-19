import json
import math

import pytest

from helpers import feats, hello, msg, obs, outcome, send
from rl_model.aggregate import (T95, AggregationError, aggregate, check_separation, read_run, run_metrics,
                                summarize, to_markdown)
from rl_model.run_plan import build_plan
from rl_model.server import Session
from rl_model.train_offline import train_from_logs


def make_run(cfg, tmp, run_id, phase, seed, mode, policy=None, model_in=None, tasks=(), sub=None):
    """Produces a run log through the real Session. Outcomes are SYNTHETIC (test fixture only)."""
    d = tmp / (sub or run_id)
    s = Session(cfg, mode, policy, model_in=model_in, log_dir=str(d / "l"), artifacts_dir=str(d / "a"))
    assert send(s, hello(run_id, phase, seed))[0]["type"] == "hello_ack"
    for i, t in enumerate(tasks):
        a = send(s, obs(f"t{i}", features=t.get("features", feats())))[0]
        kw = {k: v for k, v in t.items() if k != "features"}
        send(s, outcome(f"t{i}", action=a["action"], **kw))
    send(s, msg("shutdown"))
    return str(d / "l" / f"run_{run_id}.jsonl")


TASKS = [dict(latency=100.0, met=True, rm={"bandwidth_bytes": 1000, "executing_node_utilization": 0.5}),
         dict(latency=300.0, met=False, rm={"bandwidth_bytes": 3000, "executing_node_utilization": 0.7}),
         dict(status="failed", latency=None, met=False, rm={"bandwidth_bytes": 2000}),
         dict(latency=200.0, met=True, rm={"bandwidth_bytes": 2000})]


def test_run_metrics_hand_computed(cfg, tmp_path):
    p = make_run(cfg, tmp_path, "r", "test", 1, "baseline", "edge", tasks=TASKS)
    m = run_metrics(read_run(p))
    assert m["n_tasks"] == 4
    assert m["completion_rate"] == 0.75                        # 3 of 4 completed
    assert m["avg_latency_ms"] == pytest.approx(200.0)         # (100+300+200)/3, failed excluded
    assert m["deadline_violation_rate"] == 0.5                 # 1 miss + 1 failure
    assert m["avg_bandwidth_bytes"] == pytest.approx(2000.0)   # (1000+3000+2000+2000)/4
    assert m["avg_node_utilization"] == pytest.approx(0.6)     # only 2 tasks report it
    assert m["avg_energy_joules"] is None                      # nobody reported -> n/a, not 0


def test_summarize_and_t_table():
    s = summarize([1, 2, 3])
    assert s["mean"] == 2 and s["std"] == 1 and s["ci95"] == pytest.approx(4.303 / math.sqrt(3))
    assert summarize([5])["ci95"] is None and summarize([None])["mean"] is None
    scipy_stats = pytest.importorskip("scipy.stats")
    for df, t in enumerate(T95, start=1):
        assert t == pytest.approx(scipy_stats.t.ppf(0.975, df), abs=1e-3)


def test_full_aggregation_across_seeds_and_policies(cfg, tmp_path):
    paths = []
    for seed in (101, 102, 103):
        for pol in ("local", "edge", "cloud"):
            paths.append(make_run(cfg, tmp_path, f"{pol}-{seed}", "test", seed, "baseline", pol, tasks=TASKS))
    res = aggregate(paths)
    assert set(res["policies"]) == {"local", "edge", "cloud"} and not res["warnings"]
    e = res["policies"]["edge"]
    assert e["n_runs"] == 3 and e["sim_seeds"] == [101, 102, 103] and e["total_tasks"] == 12
    assert e["metrics"]["avg_latency_ms"]["mean"] == pytest.approx(200.0)
    assert e["metrics"]["avg_latency_ms"]["std"] == pytest.approx(0.0)
    md = to_markdown(res)
    assert "| edge | 3 | 12 |" in md and "n/a" in md           # energy not reported -> n/a


def test_train_runs_are_excluded_but_used_for_separation(cfg, tmp_path):
    tr = make_run(cfg, tmp_path, "tr", "train", 7, "train", tasks=TASKS)
    te = make_run(cfg, tmp_path, "te", "test", 8, "baseline", "edge", tasks=TASKS)
    res = aggregate([tr, te])
    assert list(res["policies"]) == ["edge"]


def test_seed_overlap_between_train_and_test_is_refused(cfg, tmp_path):
    tr = make_run(cfg, tmp_path, "tr", "train", 7, "train", tasks=TASKS)
    te = make_run(cfg, tmp_path, "te", "test", 7, "baseline", "edge", tasks=TASKS)
    with pytest.raises(AggregationError, match="also used for training"):
        aggregate([tr, te])
    te2 = make_run(cfg, tmp_path, "te2", "test", 9, "baseline", "edge", tasks=TASKS)
    with pytest.raises(AggregationError, match="also used for training"):
        aggregate([te2], extra_train_seeds=[9])


def test_unfrozen_qlearning_test_run_is_refused(cfg, tmp_path):
    p = make_run(cfg, tmp_path, "bad", "dev", 5, "train", tasks=TASKS)
    lines = open(p).read().splitlines()
    rec = json.loads(lines[0])
    rec["phase"] = "test"                                      # simulate a mislabeled run
    lines[0] = json.dumps(rec)
    open(p, "w").write("\n".join(lines) + "\n")
    assert any("not frozen" in x for x in check_separation([read_run(p)]))
    with pytest.raises(AggregationError):
        aggregate([p])


def test_mismatched_seed_sets_warn_and_duplicates_fail(cfg, tmp_path):
    a = make_run(cfg, tmp_path, "a", "test", 1, "baseline", "edge", tasks=TASKS)
    b = make_run(cfg, tmp_path, "b", "test", 2, "baseline", "cloud", tasks=TASKS)
    assert aggregate([a, b])["warnings"]
    a2 = make_run(cfg, tmp_path, "a2", "test", 1, "baseline", "edge", tasks=TASKS)
    with pytest.raises(AggregationError, match="duplicate sim_seed"):
        aggregate([a, a2])


def test_no_test_runs_or_empty_runs_error(cfg, tmp_path):
    tr = make_run(cfg, tmp_path, "tr", "train", 7, "train", tasks=TASKS)
    with pytest.raises(AggregationError, match="no phase='test'"):
        aggregate([tr])
    empty = make_run(cfg, tmp_path, "e", "test", 3, "baseline", "edge", tasks=[])
    with pytest.raises(AggregationError, match="no task records"):
        aggregate([empty])


def test_corrupt_log_reports_file_and_line(tmp_path):
    p = tmp_path / "x.jsonl"
    p.write_text("{oops\n")
    with pytest.raises(AggregationError, match="x.jsonl:1"):
        read_run(p)


# -------------------------------------------------------- end-to-end: train -> frozen eval
def test_train_then_frozen_eval_pipeline_is_separated(cfg, tmp_path):
    train_tasks = [dict(latency=100 + 50 * (i % 3), met=True,
                        rm={"bandwidth_bytes": 1000}) for i in range(40)]
    tr = make_run(cfg, tmp_path, "tr", "train", 1, "train", tasks=train_tasks)
    model = str(tmp_path / "tr" / "a" / "model_latest.json")
    ev = make_run(cfg, tmp_path, "ev", "test", 2, "eval", model_in=model, tasks=TASKS, sub="ev")
    base = make_run(cfg, tmp_path, "bl", "test", 2, "baseline", "edge", tasks=TASKS)
    res = aggregate([tr, ev, base])
    assert set(res["policies"]) == {"qlearning", "edge"}
    assert res["policies"]["qlearning"]["sim_seeds"] == res["policies"]["edge"]["sim_seeds"] == [2]


# ------------------------------------------------------------------ offline replay
def test_offline_training_replays_logged_transitions(cfg, tmp_path):
    tasks = [dict(features=feats(task_mi=500 + 1500 * i), latency=100.0 * (i + 1), met=True,
                  rm={"bandwidth_bytes": 0}) for i in range(3)]
    p = make_run(cfg, tmp_path, "tr", "train", 1, "train", tasks=tasks)
    ag = train_from_logs(cfg, [p], epochs=1)
    assert ag.updates == 3 and sum(map(sum, ag.visits)) == 3
    recs = [json.loads(l) for l in open(p) if '"record":"task"' in l]
    for r in recs:                      # each distinct (s,a): Q = alpha * reward
        assert ag.q[r["state_index"]][["Local", "Edge", "Cloud"].index(r["action_executed"])] == \
            pytest.approx(cfg.agent.alpha * r["reward"]["reward"])


def test_offline_training_refuses_test_phase_logs(cfg, tmp_path):
    p = make_run(cfg, tmp_path, "te", "test", 1, "baseline", "edge", tasks=TASKS)
    with pytest.raises(AggregationError, match="refusing to train on test-phase"):
        train_from_logs(cfg, [p])


# ---------------------------------------------------------------------- run plan
def test_run_plan_enforces_disjoint_seeds():
    with pytest.raises(ValueError, match="overlap"):
        build_plan([1, 2], [2, 3])
    with pytest.raises(ValueError, match="duplicate"):
        build_plan([1, 1], [3])
    plan = build_plan([1, 2], [10, 11])
    assert [r["phase"] for r in plan].count("train") == 2
    assert sum(r["run_id"].startswith("test-q") for r in plan) == 2
    assert "--model-in artifacts/train_seed1.json" in plan[1]["cmd"]
    assert all("train_seed2.json" in r["cmd"] for r in plan if r["run_id"].startswith("test-q"))
