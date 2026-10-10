# Contributing Guide

This guide is for the three-person team (**Mark**, **Ayoub**, **Ibrahim**) working
on this research repository. It describes the Git workflow we intend to follow so
that each member can work independently and merge safely.

---

## 1. Basic workflow

1. **Pull the latest changes** from the shared branch.
2. **Create a feature branch** for your work.
3. **Make changes** in small, focused increments.
4. **Run relevant tests** (once tests exist for your area).
5. **Commit** your changes with clear messages.
6. **Push** your feature branch to `origin`.
7. **Open a pull request (PR)** against `main`.
8. **Review and merge** the changes (at least one other member should review).

### Example commands

```bash
git pull
git switch -c feature/short-description
# ... edit files ...
git add .
git commit -m "Describe the change"
git push -u origin feature/short-description
```

Then open a pull request on GitHub from `feature/short-description` into `main`,
fill in the PR template, and request a review.

---

## 2. Branch naming

- Branch names must be **unique** and **descriptive** of the work.
- Use a prefix to indicate the area, e.g. `feature/`, `fix/`, `docs/`, `experiment/`.
- Keep the description short but specific:
  - `feature/qlearning-agent-core`
  - `feature/ifogsim-custom-topology`
  - `fix/integration-timeout-handling`

### Example long-lived feature branches (illustrative only)

These are **suggestions of typical areas** — do **not** create them automatically.
Each member creates a branch when they actually start work in that area:

- `feature/simulator` — Ayoub: iFogSim / Java simulation work.
- `feature/rl-agent` — Ibrahim: Python Q-Learning agent work.
- `feature/integration` — cross-cutting Java↔Python integration work.

Create a branch only when you have concrete changes to make, and prefer a more
specific name than these generic examples when possible.

---

## 3. Staying in sync

Before starting work and before opening a PR, pull the latest `main`:

```bash
git switch main
git pull
git switch feature/your-branch
git rebase main        # or: git merge main
```

Rebasing keeps your branch history linear; merging is also acceptable. Pick one
approach and be consistent. If you are unsure, ask before rewriting history that
has already been pushed.

---

## 4. Understanding merge conflicts

A **merge conflict** happens when two people (or two branches) change the **same
part of the same file** in different ways, and Git cannot automatically decide
which change to keep.

This is most common when **two people edit the same file at the same time** — for
example, both modifying `integration/protocol/agent-message-schema.json`, or both
editing a shared section of `README.md`, while working on different branches.

Git marks the conflict in the file:

```
<<<<<<< HEAD
your version of the line
=======
their version of the line
>>>>>>> feature/other-branch
```

To resolve a conflict:

1. Open the conflicted file.
2. Decide the correct final content (keep yours, keep theirs, or combine both).
3. Delete the `<<<<<<<`, `=======`, and `>>>>>>>` markers.
4. Stage the resolved file and continue:

```bash
git add <resolved-file>
git commit          # for a merge
# or, during a rebase:
git add <resolved-file>
git rebase --continue
```

### How to minimize conflicts

- **Respect ownership boundaries** (see `docs/team-responsibilities.md`):
  - Ayoub works mainly in `simulator/`.
  - Ibrahim works mainly in `rl-agent/`.
  - Mark maintains root docs, `integration/`, `experiments/`, `results/`.
- Keep changes **small and focused** per branch/PR.
- **Pull often** so your branch does not drift far from `main`.
- Coordinate **shared files** in advance — especially the integration protocol and
  interface decisions, which require agreement between Ayoub and Ibrahim before
  either changes them.
- Add new files rather than rewriting large shared blocks when possible.

---

## 5. Commit messages

Write concise, imperative messages that explain *what* and *why*:

```
Add draft JSON schema for agent request/response
Implement state discretization helpers in rl-agent
Document provisional reward weighting in state-action-reward.md
```

Avoid messages like `update`, `fix`, or `wip` on their own.

---

## 6. Pull request expectations

- Use the PR template in `.github/pull_request_template.md`.
- State clearly whether the change is **planned design documentation**, a
  **prototype**, or **verified working code**.
- Do not describe unverified functionality as working. Keep the distinction
  between *planned* and *implemented* honest in docs and PR descriptions.
- Link related issues where relevant.
- Wait for at least one review before merging.

---

## 7. Running tests (once implemented)

- Python agent tests live in `rl-agent/tests/`. Typical command (subject to the
  final setup defined in `rl-agent/README.md`):

  ```bash
  cd rl-agent
  python -m pytest
  ```

- Java/simulator tests live with the `simulator/` area and are run with the
  project's Java build tool (e.g. `mvn test`). To be confirmed by Ayoub.

Until test code exists, there is nothing to run — do not claim tests pass.

---

## 8. What to avoid

- Do **not** run destructive Git commands on shared branches
  (`git reset --hard`, `git clean -fd`, `git push --force`) without explicit team
  agreement.
- Do **not** rewrite pushed history casually.
- Do **not** modify the original iFogSim repository — it is out of scope.
- Do **not** commit large binaries, local datasets, IDE files, or build output
  (see `.gitignore`).
- Do **not** invent benchmark results or claim a feature works before it is
  verified.
