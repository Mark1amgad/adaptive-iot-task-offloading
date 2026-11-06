# Contributing

## Before changing files

1. Read [MARK_RESEARCH_SPECIFICATION_V2.md](MARK_RESEARCH_SPECIFICATION_V2.md).
2. Check [TASK_TRACKER.md](TASK_TRACKER.md) for current status and dependencies.
3. Work in the correct member or implementation folder.
4. Check `git status --short --branch` before editing; do not overwrite another person's changes.

## File placement

- Member-authored drafts and received packages: `team-work/<member>/`.
- Shared papers and research evidence: `research/`.
- Reproducible implementation and experiment artifacts: `deliverables/`.
- Short validation records: `audit_output/`.

Keep one canonical copy of a file. Use links from indexes and READMEs instead of copying identical Markdown documents.

## Evidence and claims

- Record the exact command, configuration, input, and output for validation.
- Separate measured values from configured values and illustrative examples.
- A successful one-task test does not establish multi-task correctness or comparative performance.
- Do not claim a feature is implemented unless its source and test evidence are present.
- Do not modify upstream iFogSim core code as part of project changes.

## Git workflow

Use a focused branch and pull request for substantive changes. Review the diff, run relevant tests, and check:

```bash
git diff --check
git status --short
```

Do not commit generated classes, caches, local IDE state, virtual environments, or credentials.
