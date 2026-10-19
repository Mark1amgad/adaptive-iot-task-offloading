# Test results

## Environment discovery

- Repository declared Python requirement: `>=3.10`.
- System `python`: not found. `py -0p`: no installed Pythons.
- An embedded Python 3.11.4 from Cinema 4D was usable for standard-library execution, but it had no pytest/jsonschema and could not create a venv: `Unable to copy ... venvlauncher.exe` / WinError 2.
- No dependencies were installed and no source/test file was changed.

## Attempted test setup

```text
<embedded-python> -m venv .audit_venv
exit: 1
Unable to copy ... venvlauncher.exe
```

Therefore `pytest -q` was **not run** and has no pass/fail result in this audit. The model was still syntax/import/protocol smoke-tested with the embedded standard-library Python: `python -m compileall -q src` exited 0; a config/state import check exited 0; and the supplied JSONL example session completed with one update and a saved model. See `DEMONSTRATION_RESULTS.md`. A suitable Python install and `pip install -r requirements.txt` in a fresh project-local venv are required before claiming the suite result.
