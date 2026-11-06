"""Summarize measured one-task policy traces; this is not an RL evaluation."""

import argparse
import json
from pathlib import Path


CASES = (("one_task_train_pass", "RL train"),
         ("regression_local", "Local baseline"),
         ("regression_edge", "Edge baseline"),
         ("regression_cloud", "Cloud baseline"))


def read_trace(path):
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    find = lambda record: next(row for row in rows if row["record"] == record)
    return {
        "case": path.parent.name,
        "decision": find("decision").get("action"),
        "execution": find("execution").get("action_executed"),
        "device": find("execution").get("device"),
        "latency_ms": find("terminal").get("latency_ms"),
        "deadline_met": find("terminal").get("deadline_met"),
        "bandwidth_bytes": find("terminal").get("bandwidth_bytes"),
        "status": find("acceptance").get("status"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = []
    for name, label in CASES:
        result = read_trace(args.root / name / "java_trace.jsonl")
        result["label"] = label
        results.append(result)
    document = {
        "scope": "one task per run; integration demonstration, not RL performance evaluation",
        "source_root": str(args.root),
        "results": results,
        "interpretation": "The RL row demonstrates real action control. Baseline rows are deterministic routing references; no superiority claim is made.",
    }
    rendered = json.dumps(document, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()