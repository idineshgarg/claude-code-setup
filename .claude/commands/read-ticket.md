---
description: Stage 1 — fetch a Jira ticket via the jira CLI and save it to the workflow directory
argument-hint: <TICKET-KEY>
allowed-tools: Bash(jira issue view:*), Bash(jira me:*), Bash(mkdir:*), Read, Write
---

## Stage 1: Read the Jira ticket

Ticket key: **$ARGUMENTS** (if empty, ask the user for it).

1. Fetch the ticket as plain text:

   ```
   jira issue view $ARGUMENTS --plain --comments 10
   ```

   - If the `jira` command is not found, tell the user to install and configure
     [`jira-cli`](https://github.com/ankitpokhrel/jira-cli) (`brew install jira-cli`
     then `jira init`), or to paste the ticket contents directly. Do not invent ticket data.
   - If the command fails with an auth error, tell the user to run `jira init` or refresh
     their API token.

2. Create `.workflow/$ARGUMENTS/` if it does not exist.

3. Write `.workflow/$ARGUMENTS/ticket.md` containing:
   - A header line with the key, summary, type, status, assignee, and a link.
   - The full description.
   - Acceptance criteria if present.
   - The most relevant comments (skip noise).
   - Linked issues / sub-tasks.

4. Print a 3-5 line summary and list anything ambiguous that the spec stage will need
   to resolve. Do not start the spec.
