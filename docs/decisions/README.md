# Decision Log

This folder records **design decisions** for the project as short, dated notes
(often called Architecture Decision Records, ADRs). Capturing decisions here keeps
the reasoning visible to all three members and prevents silently reversing
agreements.

## Why a decision log?

Several project choices are currently **open** and must be agreed between the
right people before implementation, for example:

- Decision-process framing: contextual bandit vs. sequential MDP.
- Final state feature set (and whether **network load** is added → 54 vs. 162 states).
- Feature units and **discretization boundaries**.
- Reward terms, weights, normalization, and where reward is computed.
- Integration protocol: field names, transport, timeout/fallback policy.
- Project license choice (see `LICENSE_STATUS.md`).

Interface/protocol decisions **require agreement between Ayoub and Ibrahim** before
they are recorded as accepted.

## How to add a decision

1. Copy the template file [`0000-template.md`](0000-template.md) into a new file
   named `NNNN-short-title.md` (zero-padded increasing number, e.g.
   `0001-choose-mdp.md`).
2. Fill in the sections (Context, Decision, Consequences, Alternatives).
3. Set the status (`Proposed` / `Accepted` / `Superseded`) and list the deciders.
4. Open a PR and get review from the relevant members.

> No decisions have been finalized yet. Files added here will document agreements
> as the team reaches them.
