---
name: dev-workflow
description: Ticket-to-implementation dev workflow. Read a Jira ticket, write a spec, write a PRD, implement it, then re-review the PRD against the implementation. Use when the user references a Jira ticket key or asks to "run the dev workflow" / "start work on <TICKET>".
---

# Dev workflow

A five-stage pipeline that turns a Jira ticket into reviewed, implemented code.
Each stage is also runnable on its own as a slash command.

| # | Stage | Command | Output |
|---|-------|---------|--------|
| 1 | Read the Jira ticket | `/read-ticket <KEY>` | `.workflow/<KEY>/ticket.md` |
| 2 | Create a spec file | `/make-spec <KEY>` | `.workflow/<KEY>/spec.md` |
| 3 | Create a PRD | `/make-prd <KEY>` | `.workflow/<KEY>/prd.md` |
| 4 | Implement the PRD | `/implement <KEY>` | code changes + `.workflow/<KEY>/progress.md` |
| 5 | Re-review the PRD | `/review-prd <KEY>` | `.workflow/<KEY>/review.md` |

## Conventions

- **Working directory:** everything the workflow generates lives under `.workflow/<TICKET-KEY>/`.
  Add `.workflow/` to `.gitignore` unless the team wants these docs committed.
- **Ticket key:** every command takes the key as its argument (e.g. `PROJ-123`).
  If no key is given, use the most recently modified directory under `.workflow/`.
- **Stage gating:** each stage expects the previous stage's output file to exist.
  If it is missing, tell the user to run the earlier command first — do not silently skip ahead.
- **Human review points:** stop and summarize after stages 2, 3, and 5. Do not chain
  straight from spec to implementation without the user confirming the PRD.

## Running the whole pipeline

When the user asks to run the full workflow for a ticket:

1. Run stage 1, then show a 3-5 line summary of the ticket.
2. Run stage 2, then show the spec's open questions and wait for answers.
3. Run stage 3, then show the PRD scope + non-goals and wait for a go-ahead.
4. Run stage 4.
5. Run stage 5 and report the verdict.

## Templates

- `templates/spec.md` — technical spec skeleton
- `templates/prd.md` — PRD skeleton
