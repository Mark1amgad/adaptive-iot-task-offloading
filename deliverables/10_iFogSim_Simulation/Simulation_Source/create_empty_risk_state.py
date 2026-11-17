#!/usr/bin/env python3
"""Create an empty residual-calibration sidecar for the analytical-only ablation arm."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rl-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rl_root = args.rl_root.resolve()
    sys.path.insert(0, str(rl_root / "src"))
    from rl_model.config_v2 import V2RuntimeConfig
    from rl_model.risk import RiskCalibrator

    config_path = args.config.resolve() if args.config else (rl_root / "config" / "v2.json")
    runtime = V2RuntimeConfig.load(config_path)
    if not runtime.risk.enabled:
        raise ValueError("risk.enabled must be true for the analytical feasibility filter")
    if runtime.risk.uncalibrated_margin_ms != 0:
        raise ValueError(
            "analytical-only ablation requires uncalibrated_margin_ms=0; "
            f"found {runtime.risk.uncalibrated_margin_ms}"
        )

    calibrator = RiskCalibrator(runtime.risk)
    output = calibrator.save(args.output)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(json.dumps({
        "status": "PASS",
        "arm": "analytical_only_zero_residual_margin",
        "risk_config_fingerprint": runtime.risk.fingerprint(),
        "calibration_updates": calibrator.updates,
        "sample_counts": calibrator.sample_counts(),
        "uncalibrated_margin_ms": runtime.risk.uncalibrated_margin_ms,
        "risk_state_sha256": digest,
        "output": str(output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, ImportError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
