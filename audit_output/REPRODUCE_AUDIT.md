# Reproduce audit

From repository root, use Python 3.10+ with no third-party dependencies required for the core dataset audit:

```text
python audit_output/generate_audit.py
```

For model tests, create a working local virtual environment using a normal CPython distribution, then:

```text
python -m venv .audit_venv
.audit_venv\Scripts\python -m pip install -r team-work\Ayoub\rl_model\rl_model\requirements.txt
cd team-work\Ayoub\rl_model\rl_model
..\..\..\..\.audit_venv\Scripts\python -m pytest -q
```

The generator uses full-file CSV reads and emits the inventory, quality report, numeric summary, UCI per-file statistics, and narrative reports in this directory. It does not modify source datasets or the model.
