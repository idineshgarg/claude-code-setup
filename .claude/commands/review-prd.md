---
description: Stage 5 — re-review the implementation against the PRD and record the verdict
argument-hint: <TICKET-KEY>
allowed-tools: Read, Write, Grep, Glob, Bash(git diff:*), Bash(git log:*)
---

## Stage 5: Re-review the PRD

Ticket key: **$ARGUMENTS** (if empty, use the most recently modified dir under `.workflow/`).

1. Read `.workflow/$ARGUMENTS/prd.md`, `.workflow/$ARGUMENTS/progress.md`, and the
   spec. Review the actual code changes (`git diff` against the base branch, or the
   files listed in `progress.md`).

2. For **each requirement (R#)** and **each acceptance criterion (AC#)**, judge:
   - `met` — code + tests satisfy it. Cite `path:line`.
   - `partial` — some of it is done. Say what is missing.
   - `missing` — not addressed.
   - `deviated` — built differently than the PRD says. Say whether the deviation is
     acceptable and whether the PRD should be updated.

3. Also check:
   - Acceptance criteria that have no corresponding test.
   - Non-goals that were accidentally touched.
   - Edge cases from the spec's risk list.
   - Whether the PRD itself now has gaps that implementation exposed.

4. Write `.workflow/$ARGUMENTS/review.md`:
   - A per-requirement table (ID | verdict | evidence | notes).
   - A "PRD corrections" section listing edits the PRD needs to match reality.
   - An overall verdict: **ship**, **ship with follow-ups**, or **not ready**, with
     the blocking items listed.

5. Apply the agreed PRD corrections to `prd.md` and set its Status to **reviewed**.

6. Report the verdict and the top action items.
