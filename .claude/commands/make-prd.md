---
description: Stage 3 — turn the spec into a PRD with numbered requirements and acceptance criteria
argument-hint: <TICKET-KEY>
allowed-tools: Read, Write, Glob
---

## Stage 3: Create a PRD

Ticket key: **$ARGUMENTS** (if empty, use the most recently modified dir under `.workflow/`).

1. Read `.workflow/$ARGUMENTS/spec.md` and `.workflow/$ARGUMENTS/ticket.md`. If the spec
   is missing, tell the user to run `/make-spec $ARGUMENTS` first and stop.

2. Confirm the spec's open questions are resolved. If any are still open, list them and
   ask the user to answer before proceeding.

3. Write `.workflow/$ARGUMENTS/prd.md` using the structure in
   `.claude/skills/dev-workflow/templates/prd.md`:
   - Every requirement gets an ID (R1, R2, …) and a priority (must / should / could).
   - Acceptance criteria are concrete and testable — stage 5 checks each one against
     the code, so avoid vague language.
   - Fill in Non-goals explicitly from the spec's "Out of scope".
   - Set **Status: draft**.

4. Stop and present:
   - Summary paragraph.
   - Goals vs Non-goals.
   - The requirements table.

   Wait for an explicit go-ahead before implementation. On approval, update the PRD's
   Status line to **approved**.
