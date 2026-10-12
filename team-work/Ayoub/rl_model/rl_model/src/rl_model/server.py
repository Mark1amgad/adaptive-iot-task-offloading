"""Persistent Python process that Java talks to over stdin/stdout (JSON lines).

    python -m rl_model.server --config config/default.json --mode train --model-out artifacts/model.json
    python -m rl_model.server --mode eval --model-in artifacts/model.json
    python -m rl_model.server --mode baseline --policy edge

stdout carries ONLY protocol messages. Logs go to files (and warnings to stderr).
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

from . import PROTOCOL_VERSION
from .actions import ACTION_NAMES, action_id, action_name
from .agent import QLearningAgent
from .config import Config
from .logging_utils import EventLogger
from .persistence import (CompatibilityError, load_model, save_checkpoint, save_model)
from .protocol import (ProtocolError, action_msg, dumps, error_msg, hello_ack, outcome_ack,
                       parse_hello, parse_line, parse_observation, parse_outcome)
from .reward import RewardError, compute_reward
from .state import StateSpace

MODES = ("train", "eval", "baseline")
POLICIES = ("local", "edge", "cloud", "random")
COMPLETED_MEMORY = 10000


@dataclass
class Pending:
    features: Dict[str, Any]
    state_index: int
    action: int
    mode: str
    epsilon: float
    mask: Tuple[int, ...]
    model_version: str


class Session:
    """Pure message handler (no I/O besides log/model files) so it is directly testable."""

    def __init__(self, cfg: Config, mode: str, policy: Optional[str] = None,
                 model_in: Optional[str] = None, model_out: Optional[str] = None,
                 log_dir: str = "logs", artifacts_dir: str = "artifacts",
                 seed: Optional[int] = None, allow_reward_mismatch: bool = False):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        if mode == "baseline" and policy not in POLICIES:
            raise ValueError(f"baseline mode needs --policy in {POLICIES}")
        self.cfg = cfg
        if seed is not None:
            self.cfg = dataclasses.replace(cfg, agent=dataclasses.replace(cfg.agent, seed=seed))
        self.mode, self.policy = mode, policy
        self.space = StateSpace(self.cfg.features)
        self.log_dir, self.artifacts_dir = Path(log_dir), Path(artifacts_dir)
        self.model_out = Path(model_out) if model_out else self.artifacts_dir / "model_latest.json"
        self.logger = EventLogger()
        if model_in:
            self.agent = load_model(model_in, self.space, self.cfg.agent, self.cfg.reward,
                                    allow_reward_mismatch=allow_reward_mismatch)
        elif mode == "eval":
            raise ValueError("eval mode requires --model-in (a trained model)")
        else:
            self.agent = QLearningAgent(self.space, self.cfg.agent)
        if mode != "train":
            self.agent.freeze()
        self.pending: Dict[str, Pending] = {}
        self._completed: Deque[str] = deque(maxlen=COMPLETED_MEMORY)
        self._completed_set: set = set()
        self.hello = None
        self.run_fh = None
        self.should_exit = False
        self.exit_code = 0
        self.n_tasks = 0
        self.closed = False

    # ------------------------------------------------------------ labels
    @property
    def policy_label(self) -> str:
        return "qlearning" if self.mode in ("train", "eval") else str(self.policy)

    @property
    def updates_enabled(self) -> bool:
        return self.mode == "train"

    # --------------------------------------------------------------- IO
    def handle_line(self, line: str) -> List[str]:
        try:
            msg = parse_line(line)
            replies = self._dispatch(msg)
        except ProtocolError as e:
            self.logger.warning("protocol_error", code=e.code, message=e.message, task_id=e.task_id)
            if e.fatal:
                self.should_exit, self.exit_code = True, 2
            return [dumps(error_msg(e.code, e.message, e.task_id, e.fatal))]
        except Exception as e:  # defensive: never kill the persistent process on one bad message
            self.logger.error("internal_error", message=repr(e))
            return [dumps(error_msg("internal_error", repr(e)))]
        return [dumps(r) for r in replies]

    def _dispatch(self, msg: Dict[str, Any]) -> List[Dict[str, Any]]:
        t = msg.get("type")
        if t == "ping":
            return [{"protocol_version": PROTOCOL_VERSION, "type": "pong"}]
        if t == "hello":
            return [self._on_hello(msg)]
        if t in ("observation", "outcome", "save", "shutdown"):
            if self.hello is None:
                raise ProtocolError("handshake_required", "send 'hello' first")
            return getattr(self, f"_on_{t}")(msg)
        raise ProtocolError("unknown_type", f"unknown message type {t!r}")

    # ------------------------------------------------------------ hello
    def _on_hello(self, msg) -> Dict[str, Any]:
        if self.hello is not None:
            raise ProtocolError("duplicate_hello", "handshake already completed")
        h = parse_hello(msg)
        ok = ("train", "dev") if self.mode == "train" else ("test", "dev")
        if h.phase not in ok:
            raise ProtocolError("phase_mode_mismatch",
                                f"mode '{self.mode}' cannot run in phase '{h.phase}' (allowed: {ok})",
                                fatal=True)
        self.hello = h
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger.attach(self.log_dir / f"events_{h.run_id}.jsonl")
        self.run_fh = open(self.log_dir / f"run_{h.run_id}.jsonl", "a", encoding="utf-8")
        ph = self.space.placeholder_features()
        self._run_record({"record": "run_start", "run_id": h.run_id, "policy": self.policy_label,
                          "mode": self.mode, "phase": h.phase, "agent_seed": self.cfg.agent.seed,
                          "sim_seed": h.sim_seed, "simulator": h.simulator,
                          "updates_enabled": self.updates_enabled,
                          "model_version": self.agent.model_version(),
                          "state_fingerprint": self.space.fingerprint(),
                          "reward_fingerprint": self.cfg.reward.fingerprint(),
                          "placeholder_features": ph})
        if ph:
            self.logger.warning("placeholder_thresholds", features=ph)
        return hello_ack(model_version=self.agent.model_version(), mode=self.mode,
                         policy=self.policy_label, updates_enabled=self.updates_enabled,
                         state_count=self.space.n_states, actions=list(ACTION_NAMES),
                         features=list(self.space.feature_names), placeholder_features=ph,
                         decision_model=self.cfg.agent.decision_model)

    def _run_record(self, rec: Dict[str, Any]) -> None:
        if self.run_fh:
            self.run_fh.write(json.dumps(rec, separators=(",", ":"), allow_nan=False) + "\n")
            self.run_fh.flush()

    # ------------------------------------------------------ observation
    def _on_observation(self, msg) -> List[Dict[str, Any]]:
        obs = parse_observation(msg, self.space)
        if obs.task_id in self.pending:
            raise ProtocolError("duplicate_task", "task_id already has an undecided/unreported action",
                                obs.task_id)
        s = obs.state_index
        if self.mode == "baseline":
            a = action_id({"local": "Local", "edge": "Edge", "cloud": "Cloud"}[self.policy]) \
                if self.policy != "random" else self.agent.random_action(obs.available)
            mode_, eps = "baseline", 0.0
        else:
            d = self.agent.select_action(s, obs.available)
            a, mode_, eps = d.action, d.mode, d.epsilon
        mv = self.agent.model_version()
        self.pending[obs.task_id] = Pending(obs.features, s, a, mode_, eps, obs.available, mv)
        self.logger.log("decision", task_id=obs.task_id, state=s, action=action_name(a), mode=mode_)
        return [action_msg(obs.task_id, a, action_name(a), mv, s, mode_, eps, self.agent.q[s])]

    # ---------------------------------------------------------- outcome
    def _on_outcome(self, msg) -> List[Dict[str, Any]]:
        out = parse_outcome(msg, self.space)
        tid = out.task_id
        p = self.pending.get(tid)
        if p is None:
            code = "duplicate_outcome" if tid in self._completed_set else "unknown_task"
            raise ProtocolError(code, f"no pending decision for task {tid!r}", tid)
        try:
            rb = compute_reward(self.cfg.reward, failed=out.failed, latency_ms=out.latency_ms,
                                deadline_met=out.deadline_met, resource_metrics=out.resource_metrics,
                                deadline_ms=p.features.get("deadline_ms"))
        except RewardError as e:     # pending stays: Java may resend a corrected outcome
            raise ProtocolError("invalid_outcome", str(e), tid) from e
        if out.action_executed != p.action:
            self.logger.warning("action_override", task_id=tid, decided=action_name(p.action),
                                executed=action_name(out.action_executed))
        dl = p.features.get("deadline_ms")
        if dl is not None and not out.failed and out.latency_ms is not None \
                and (out.latency_ms <= dl) != out.deadline_met:
            self.logger.warning("deadline_flag_inconsistent", task_id=tid, latency_ms=out.latency_ms,
                                deadline_ms=dl, deadline_met=out.deadline_met)
        if not out.terminal and self.cfg.agent.decision_model == "contextual_bandit":
            self.logger.warning("terminal_false_ignored", task_id=tid,
                                note="decision_model=contextual_bandit: no bootstrapping")
        updated = False
        if self.updates_enabled:
            self.agent.update(p.state_index, out.action_executed, rb.reward, out.next_state_index,
                              out.terminal or out.next_state_index is None
                              or self.cfg.agent.decision_model == "contextual_bandit",
                              out.next_available)
            updated = True
            c = self.cfg.agent
            if c.checkpoint_every and self.agent.updates % c.checkpoint_every == 0:
                path = save_checkpoint(self.agent, self.cfg.reward, self.artifacts_dir / "checkpoints",
                                       c.checkpoint_keep_last)
                self.logger.log("checkpoint", path=str(path), updates=self.agent.updates)
        del self.pending[tid]
        if len(self._completed) == self._completed.maxlen:
            self._completed_set.discard(self._completed[0])
        self._completed.append(tid)
        self._completed_set.add(tid)
        self.n_tasks += 1
        self._run_record({"record": "task", "task_id": tid, "state_index": p.state_index,
                          "observation": p.features, "available_mask": list(p.mask),
                          "action_decided": action_name(p.action), "action_executed": action_name(out.action_executed),
                          "decision_mode": p.mode, "model_version_at_decision": p.model_version,
                          "outcome": {k: v for k, v in msg.items() if k not in ("protocol_version", "type")},
                          "reward": rb.as_dict(), "updated": updated})
        return [outcome_ack(tid, updated, rb.reward, self.agent.model_version(), self.agent.updates)]

    # ------------------------------------------------------ save / stop
    def _on_save(self, msg) -> List[Dict[str, Any]]:
        if not self.updates_enabled:
            raise ProtocolError("not_allowed", "nothing to save outside train mode")
        path = save_model(self.agent, self.cfg.reward, self.model_out)
        return [{"protocol_version": PROTOCOL_VERSION, "type": "saved", "path": str(path),
                 "model_version": self.agent.model_version()}]

    def _on_shutdown(self, msg) -> List[Dict[str, Any]]:
        orphans = len(self.pending)
        path = self.close()
        self.should_exit = True
        return [{"protocol_version": PROTOCOL_VERSION, "type": "shutdown_ack",
                 "orphaned_tasks": orphans, "model_path": str(path) if path else None,
                 "model_version": self.agent.model_version(), "tasks_reported": self.n_tasks}]

    def close(self) -> Optional[Path]:
        """Idempotent: save model (train mode), write run_end, close files."""
        if self.closed:
            return None
        self.closed = True
        path = None
        if self.updates_enabled and self.hello is not None:
            path = save_model(self.agent, self.cfg.reward, self.model_out)
        if self.pending:
            self.logger.warning("orphaned_tasks", count=len(self.pending), task_ids=list(self.pending)[:20])
        self._run_record({"record": "run_end", "tasks_reported": self.n_tasks,
                          "orphaned_tasks": len(self.pending), "updates": self.agent.updates})
        if self.run_fh:
            self.run_fh.close()
        self.logger.close()
        return path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", default="config/default.json")
    p.add_argument("--mode", choices=MODES, required=True)
    p.add_argument("--policy", choices=POLICIES, help="baseline mode only")
    p.add_argument("--model-in")
    p.add_argument("--model-out")
    p.add_argument("--log-dir", default="logs")
    p.add_argument("--artifacts-dir", default="artifacts")
    p.add_argument("--seed", type=int, help="override agent.seed from the config")
    p.add_argument("--allow-reward-mismatch", action="store_true")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = Config.load(args.config)
        sess = Session(cfg, args.mode, args.policy, args.model_in, args.model_out, args.log_dir,
                       args.artifacts_dir, args.seed, args.allow_reward_mismatch)
    except (ValueError, CompatibilityError, OSError) as e:
        print(dumps(error_msg("startup_failed", str(e), fatal=True)), flush=True)
        return 2
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            for r in sess.handle_line(line):
                sys.stdout.write(r + "\n")
            sys.stdout.flush()
            if sess.should_exit:
                break
    finally:
        sess.close()          # EOF / crash of Java side: still persist the model
    return sess.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
