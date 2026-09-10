---
description: Stage 4 — implement the approved PRD, tracking progress per requirement
argument-hint: <TICKET-KEY>
---

## Stage 4: Implement the PRD

Ticket key: **$ARGUMENTS** (if empty, use the most recently modified dir under `.workflow/`).

1. Read `.workflow/$ARGUMENTS/prd.md`. If it is missing, tell the user to run
   `/make-prd $ARGUMENTS` first and stop. If its Status is still `draft`, ask the user
   to approve it first.

2. Create `.workflow/$ARGUMENTS/progress.md` with a checklist of every requirement (R1…)
   and acceptance criterion (AC1…) from the PRD.

3. Implement requirement by requirement, in priority order (must → should → could):
   - Follow the surrounding code's conventions.
   - Add or update tests for each acceptance criterion.
   - After each requirement, run the relevant tests/linters and check it off in
     `progress.md` with a one-line note on what changed and where.

4. If implementation reveals the PRD is wrong or incomplete, stop and note it in
   `progress.md` under a "PRD deltas" heading, then ask the user how to proceed rather
   than quietly diverging.

5. When done, update the PRD Status to **implemented** and report:
   - What was built, by requirement.
   - Test/lint results (actual output — if something fails, say so).
   - Any deferred items or PRD deltas.

Do not run stage 5 automatically.
