"""Shared fixtures. NOTE: every outcome used in these tests is SYNTHETIC and exists only to exercise
the code. None of it is simulation evidence and nothing here is ever used for research results."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from rl_model.config import AgentConfig, Config  # noqa: E402
from rl_model.state import StateSpace  # noqa: E402

DEFAULT_CONFIG = ROOT / "config" / "default.json"


@pytest.fixture
def cfg() -> Config:
    return Config.load(DEFAULT_CONFIG)


@pytest.fixture
def space(cfg) -> StateSpace:
    return StateSpace(cfg.features)


@pytest.fixture
def raw_cfg() -> dict:
    return json.loads(DEFAULT_CONFIG.read_text())


def make_agent_cfg(**kw) -> AgentConfig:
    base = dict(alpha=0.5, gamma=0.0, epsilon_start=0.3, epsilon_end=0.02, epsilon_decay_steps=100,
                q_init=0.0, seed=7, decision_model="contextual_bandit")
    base.update(kw)
    return AgentConfig(**base)
