import json
from typing import Any, Dict, List

V = "1.0"


def feats(task_mi=2500, wan=45.0, edge=0.62, deadline=400) -> Dict[str, Any]:
    return {"task_mi": task_mi, "wan_latency_ms": wan, "edge_utilization": edge, "deadline_ms": deadline}


def hello(run_id="r1", phase="dev", sim_seed=1) -> str:
    return json.dumps({"protocol_version": V, "type": "hello", "run_id": run_id, "phase": phase,
                       "sim_seed": sim_seed})


def obs(task_id="t1", features=None, **extra) -> str:
    m = {"protocol_version": V, "type": "observation", "task_id": task_id,
         "features": features or feats(), **extra}
    return json.dumps(m)


def outcome(task_id="t1", action="Edge", status="completed", latency=200.0, met=True, rm=None, **extra) -> str:
    m = {"protocol_version": V, "type": "outcome", "task_id": task_id, "action_executed": action,
         "status": status, "latency_ms": latency, "deadline_met": met,
         "resource_metrics": rm if rm is not None else {"bandwidth_bytes": 50000, "energy_joules": 1.0},
         **extra}
    return json.dumps(m)


def msg(type_, **kw) -> str:
    return json.dumps({"protocol_version": V, "type": type_, **kw})


def send(sess, line: str) -> List[dict]:
    return [json.loads(r) for r in sess.handle_line(line)]
