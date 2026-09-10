---
description: Stage 2 — turn the saved ticket into a technical spec
argument-hint: <TICKET-KEY>
allowed-tools: Read, Write, Grep, Glob, Bash(git log:*), Bash(git grep:*)
---

## Stage 2: Create a spec file

Ticket key: **$ARGUMENTS** (if empty, use the most recently modified dir under `.workflow/`).

1. Read `.workflow/$ARGUMENTS/ticket.md`. If it is missing, tell the user to run
   `/read-ticket $ARGUMENTS` first and stop.

2. Explore the codebase for the areas the ticket touches: find the relevant files,
   current behavior, data models, and tests. Base the "Current behavior" section on
   what you actually read, citing `path:line`.

3. Write `.workflow/$ARGUMENTS/spec.md` using the structure in
   `.claude/skills/dev-workflow/templates/spec.md`. Fill every section; write "none"
   where a section does not apply rather than deleting it.

4. Keep the spec at design altitude — approach, components, trade-offs. No code dumps.

5. Stop and present:
   - The proposed change in 3-4 sentences.
   - The **Open questions** list.
   - The **Risks and edge cases** list.

   Wait for the user to resolve open questions before moving to the PRD.
