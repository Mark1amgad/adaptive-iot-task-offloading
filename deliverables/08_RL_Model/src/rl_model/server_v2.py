"""Protocol-v2 JSONL server for feasibility-masked nine-action task offloading.

Run with:
  python -m rl_model.server_v2 --mode train --config config/v2.json
  python -m rl_model.server_v2 --mode eval --config config/v2.json --model-in artifacts/v2.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .agent_v2 import V2MaskedTabularAgent
from .config_v2 import V2RuntimeConfig
from .offloading import ACTION_NAMES
from .persistence_v2 import V2CompatibilityError, load_v2_model, save_v2_model
from .protocol_v2 import (
    PROTOCOL_VERSION_V2, V2ProtocolError, action_message_v2,
    parse_observation_v2, parse_outcome_v2,
)
from .reward import RewardError, compute_reward
from .risk import (
    RiskCalibrator, RiskError, filter_feasible_actions, predict_legal_actions,
)


@dataclass
class PendingV2:
    state_index: int
    features: dict
    mask: tuple[int, ...]
    action_id: int
    model_version: str
    predicted_completion_ms: dict[str, Optional[float]]
    decision_sim_time_ms: Optional[float]
    risk_forced_fallback: bool


class V2Session:
    def __init__(self, config: V2RuntimeConfig, mode: str = "train", policy: Optional[str] = None,
                 model_in: Optional[str] = None, model_out: str = "artifacts/model_v2.json",
                 risk_state_in: Optional[str] = None, risk_state_out: Optional[str] = None):
        if mode not in ("train", "eval", "baseline"):
            raise ValueError("mode must be train, eval, or baseline")
        if mode == "baseline" and policy not in ("random", "local", "edge", "cloud") + tuple(name.lower() for name in ACTION_NAMES):
            raise ValueError("baseline policy must be local, edge, cloud, random, or one of the nine v2 action names")
        if mode == "eval" and not model_in:
            raise ValueError("eval mode requires --model-in")
        self.config, self.mode, self.policy = config, mode, policy
        self.model_out = Path(model_out)
        self.risk_state_out = Path(risk_state_out or (str(self.model_out) + ".risk.json"))
        self.risk_calibrator = RiskCalibrator(config.risk)
        if risk_state_in is None and model_in:
            candidate = Path(str(model_in) + ".risk.json")
            if candidate.exists():
                risk_state_in = str(candidate)
        if risk_state_in:
            self.risk_calibrator = RiskCalibrator.load(risk_state_in, config.risk)
        if model_in:
            self.agent = load_v2_model(
                model_in, config.space.n_states, config.space.fingerprint(),
                config.agent, config.reward.fingerprint(),
            )
        else:
            self.agent = V2MaskedTabularAgent(config.space.n_states, config.agent)
        if mode != "train":
            self.agent.freeze()
        self.pending: dict[str, PendingV2] = {}
        self.hello = False
        self.should_exit = False
        self.tasks_reported = 0

    def model_version(self) -> str:
        return f"q2-{self.config.space.fingerprint()[:8]}-u{self.agent.updates}"

    def _error(self, code: str, message: str, task_id: Optional[str] = None, fatal: bool = False) -> dict:
        result = {"protocol_version": PROTOCOL_VERSION_V2, "type": "error",
                  "code": code, "message": message, "fatal": fatal}
        if task_id is not None:
            result["task_id"] = task_id
        if fatal:
            self.should_exit = True
        return result

    def handle_line(self, line: str) -> str:
        try:
            msg = json.loads(line, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
            if not isinstance(msg, dict):
                raise V2ProtocolError("message must be a JSON object")
            reply = self._dispatch(msg)
        except (ValueError, TypeError, KeyError) as exc:
            reply = self._error("invalid_message", str(exc))
        except Exception as exc:
            reply = self._error("internal_error", repr(exc))
        return json.dumps(reply, separators=(",", ":"), allow_nan=False)

    def _dispatch(self, msg: dict) -> dict:
        if msg.get("protocol_version") != PROTOCOL_VERSION_V2:
            return self._error("protocol_version_mismatch", "server requires protocol 2.0", fatal=True)
        kind = msg.get("type")
        if kind == "ping":
            return {"protocol_version": PROTOCOL_VERSION_V2, "type": "pong"}
        if kind == "hello":
            return self._hello(msg)
        if not self.hello:
            return self._error("handshake_required", "send hello before task messages")
        if kind == "observation":
            return self._observation(msg)
        if kind == "outcome":
            return self._outcome(msg)
        if kind == "save":
            if self.mode != "train":
                return self._error("not_allowed", "save is available only in train mode")
            self._save()
            return {"protocol_version": PROTOCOL_VERSION_V2, "type": "saved",
                    "model_path": str(self.model_out), "model_version": self.model_version()}
        if kind == "shutdown":
            return self._shutdown()
        return self._error("unknown_type", f"unknown message type {kind!r}")

    def _hello(self, msg: dict) -> dict:
        if self.hello:
            return self._error("duplicate_hello", "hello already completed")
        required = {"protocol_version", "type", "run_id", "phase"}
        optional = {"sim_seed", "simulator"}
        if set(msg) - required - optional or required - set(msg):
            return self._error("invalid_hello", "hello fields do not match protocol v2")
        run_id, phase = msg["run_id"], msg["phase"]
        if not isinstance(run_id, str) or not run_id or len(run_id) > 64:
            return self._error("invalid_hello", "run_id must be non-empty and <=64 chars")
        allowed = ("train", "dev") if self.mode == "train" else ("test", "dev")
        if phase not in allowed:
            return self._error("phase_mode_mismatch", f"{self.mode} mode cannot run phase {phase!r}", fatal=True)
        self.hello = True
        return {
            "protocol_version": PROTOCOL_VERSION_V2, "type": "hello_ack",
            "model_version": self.model_version(), "mode": self.mode,
            "policy": "qlearning" if self.mode != "baseline" else self.policy,
            "updates_enabled": self.mode == "train",
            "state_count": self.config.space.n_states,
            "actions": list(ACTION_NAMES),
            "features": list(self.config.space.feature_names),
            "state_fingerprint": self.config.space.fingerprint(),
            "reward_fingerprint": self.config.reward.fingerprint(),
            "risk_enabled": self.config.risk.enabled,
            "risk_config_fingerprint": self.config.risk.fingerprint(),
            "risk_calibration_updates": self.risk_calibrator.updates,
            "risk_calibration_samples": self.risk_calibrator.sample_counts(),
        }

    def _observation(self, msg: dict) -> dict:
        obs = parse_observation_v2(msg)
        tid = obs["task_id"]
        if tid in self.pending:
            return self._error("duplicate_task", "task already has a pending decision", tid)
        try:
            state = self.config.space.encode(obs["features"])
        except ValueError as exc:
            return self._error("invalid_observation", str(exc), tid)

        legal_mask = obs["available_actions"]
        decision_mask = legal_mask
        risk_decision = None
        predictions: dict[str, Optional[float]] = {}
        context = obs["risk_context"]
        if context is not None:
            if not self.config.risk.enabled:
                return self._error("risk_disabled", "risk_context supplied while risk filter is disabled", tid)
            try:
                predictions = predict_legal_actions(
                    obs["features"], obs["task_constraints"], legal_mask, context
                )
                risk_decision = filter_feasible_actions(
                    legal_mask, predictions, context.remaining_deadline_ms,
                    self.risk_calibrator, self.config.agent.fallback_order,
                )
                decision_mask = risk_decision.allowed_actions
            except RiskError as exc:
                return self._error("invalid_risk_context", str(exc), tid)

        forced_risk_fallback = bool(risk_decision and risk_decision.no_feasible_action)
        baseline_override = False
        requested_baseline_action = None
        if forced_risk_fallback:
            selected = decision_mask[0]
            mode, epsilon = "risk_fallback", 0.0
        elif self.mode == "baseline":
            fixed = {"local": 0, "edge": 4, "cloud": 8,
                     **{name.lower(): index for index, name in enumerate(ACTION_NAMES)}}
            if self.policy == "random":
                selected = self.agent.rng.choice(decision_mask)
            else:
                selected = fixed[self.policy]
                if selected not in decision_mask:
                    if risk_decision is None:
                        return self._error("baseline_unavailable",
                                           f"{self.policy} baseline action is not available for this task", tid)
                    requested_baseline_action = ACTION_NAMES[selected]
                    selected = min(
                        decision_mask,
                        key=lambda action_id: (
                            math.inf if risk_decision.estimates[ACTION_NAMES[action_id]]["safe_completion_ms"] is None
                            else risk_decision.estimates[ACTION_NAMES[action_id]]["safe_completion_ms"],
                            action_id,
                        ),
                    )
                    baseline_override = True
                    forced_risk_fallback = True
                    mode = "risk_fallback"
                else:
                    mode = "baseline"
            epsilon = 0.0
        else:
            decision = self.agent.select_action(state, decision_mask)
            selected, mode, epsilon = decision.action_id, decision.mode, decision.epsilon

        version = self.model_version()
        self.pending[tid] = PendingV2(
            state_index=state,
            features=obs["features"],
            mask=decision_mask,
            action_id=selected,
            model_version=version,
            predicted_completion_ms=predictions,
            decision_sim_time_ms=obs["sim_time_ms"],
            risk_forced_fallback=forced_risk_fallback,
        )
        response = action_message_v2(tid, selected, version, mode, epsilon)
        response["state_index"] = state
        response["q_values"] = [round(value, 8) for value in self.agent.q[state]]
        if risk_decision is not None:
            response["risk"] = risk_decision.metadata(
                selected, context.remaining_deadline_ms, context.queue_wait_basis
            )
            if baseline_override:
                response["risk"]["baseline_action_override"] = True
                response["risk"]["baseline_action_requested"] = requested_baseline_action
                response["risk"]["fallback_reason"] = "BASELINE_ACTION_NOT_RISK_FEASIBLE"
        else:
            response["risk"] = {
                "filter_applied": False,
                "status": "missing_context" if self.config.risk.enabled else "disabled",
                "no_feasible_action": False,
                "calibration_updates": self.risk_calibrator.updates,
            }
        return response

    def _outcome(self, msg: dict) -> dict:
        out = parse_outcome_v2(msg)
        tid = out["task_id"]
        pending = self.pending.get(tid)
        if pending is None:
            return self._error("unknown_task", f"no pending decision for task {tid!r}", tid)
        if out["action_executed"] not in pending.mask:
            return self._error("invalid_outcome", "executed action was not in the task's feasible mask", tid)
        try:
            reward = compute_reward(
                self.config.reward, failed=out["failed"], latency_ms=out["latency_ms"],
                deadline_met=out["deadline_met"], resource_metrics=out["resource_metrics"],
                deadline_ms=pending.features.get("deadline_ms"),
            )
        except RewardError as exc:
            return self._error("invalid_outcome", str(exc), tid)

        agent_updated = self.mode == "train" and not pending.risk_forced_fallback
        if agent_updated:
            self.agent.update(pending.state_index, out["action_executed"], reward.reward)

        calibration_updated = False
        residual_ms = None
        executed_name = ACTION_NAMES[out["action_executed"]]
        predicted = pending.predicted_completion_ms.get(executed_name)
        if (self.mode == "train" and self.config.risk.enabled
                and self.config.risk.update_on_train_outcomes
                and not out["failed"] and predicted is not None
                and out["sim_time_ms"] is not None
                and pending.decision_sim_time_ms is not None):
            observed_duration = out["sim_time_ms"] - pending.decision_sim_time_ms
            if observed_duration < -1e-9:
                return self._error("invalid_outcome", "outcome sim_time_ms precedes its decision", tid)
            residual_ms = self.risk_calibrator.observe(
                out["action_executed"], predicted, max(0.0, observed_duration)
            )
            calibration_updated = True

        del self.pending[tid]
        self.tasks_reported += 1
        return {
            "protocol_version": PROTOCOL_VERSION_V2, "type": "outcome_ack",
            "task_id": tid, "updated": agent_updated, "agent_updated": agent_updated,
            "risk_calibration_updated": calibration_updated,
            "risk_residual_ms": None if residual_ms is None else round(residual_ms, 8),
            "risk_calibration_updates": self.risk_calibrator.updates,
            "reward": round(reward.reward, 8),
            "model_version": self.model_version(), "update_count": self.agent.updates,
        }

    def _save(self) -> None:
        save_v2_model(self.agent, self.config.space.fingerprint(), self.model_out,
                      self.config.reward.fingerprint())
        if self.config.risk.enabled:
            self.risk_calibrator.save(self.risk_state_out)

    def _shutdown(self) -> dict:
        if self.mode == "train" and self.hello:
            self._save()
        self.should_exit = True
        return {
            "protocol_version": PROTOCOL_VERSION_V2, "type": "shutdown_ack",
            "orphaned_tasks": len(self.pending), "tasks_reported": self.tasks_reported,
            "model_path": str(self.model_out) if self.mode == "train" and self.hello else None,
            "model_version": self.model_version(),
        }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/v2.json")
    parser.add_argument("--mode", choices=("train", "eval", "baseline"), required=True)
    parser.add_argument("--policy", choices=("random", "local", "edge", "cloud") + tuple(name.lower() for name in ACTION_NAMES))
    parser.add_argument("--model-in")
    parser.add_argument("--model-out", default="artifacts/model_v2.json")
    parser.add_argument("--risk-state-in")
    parser.add_argument("--risk-state-out")
    args = parser.parse_args(argv)
    try:
        config = V2RuntimeConfig.load(args.config)
        session = V2Session(
            config, args.mode, args.policy, args.model_in, args.model_out,
            args.risk_state_in, args.risk_state_out,
        )
    except (ValueError, V2CompatibilityError, RiskError, OSError) as exc:
        print(json.dumps({"protocol_version": PROTOCOL_VERSION_V2, "type": "error",
                          "code": "startup_failed", "message": str(exc), "fatal": True}), flush=True)
        return 2
    for line in sys.stdin:
        if not line.strip():
            continue
        print(session.handle_line(line.strip()), flush=True)
        if session.should_exit:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
