# Team Workspaces

This directory contains the five named member workspaces. It is for drafts,
working notes, research material, dataset work, and deliverables submitted for
review. Shared approved material belongs in [../shared/](../shared/), not in a
second copy under a member directory.

Each member directory has the same workflow folders:

```text
drafts/       unfinished work and exploratory material
research/     papers, notes, and analysis owned by the member
datasets/     dataset-specific work and references
deliverables/ completed submissions awaiting or after review
notes/        decisions, questions, and handover notes
```

Existing files remain where they were unless their ownership and purpose are
reviewed. See [../TEAM_GUIDE.md](../TEAM_GUIDE.md) for the review workflow.

## Workflow

1. Work on your own Git branch.
2. Put draft work in your named folder here when it is useful for review.
3. Use the small metadata convention in deliverable notes: Owner, Status, Last Updated, Related Paper, Related Dataset, and Dependencies.
4. Open a Pull Request and describe what changed, how to test it, and what remains incomplete.
5. After approval, link or copy the final document into the appropriate shared folder; do not move executable source directories as part of this workflow.

Do not upload secrets, credentials, private data, or fabricated experimental results.
