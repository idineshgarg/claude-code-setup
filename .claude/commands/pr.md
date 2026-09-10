---
description: Push the branch and open a pull request, filling the body from the PRD and review
argument-hint: "[optional TICKET-KEY, or leave blank to autodetect]"
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git push:*), Bash(git branch:*), Bash(git rev-parse:*), Bash(gh pr create:*), Bash(gh pr view:*), Bash(gh repo view:*), Read, Glob
---

## Open a pull request

Ticket key: **$ARGUMENTS** (if blank, use the most recently modified dir under
`.workflow/`, or skip ticket-specific sections if there is none).

1. **Preconditions:**
   - `git status` is clean (all work committed). If not, tell the user to run `/commit`.
   - Current branch is not `main` / `master`.
   - `gh auth status` succeeds. If `gh` is missing, print the branch name and a
     `git push` command and stop.

2. Gather context:
   - `git log main..HEAD --oneline` — the commits going into the PR.
   - `git diff main...HEAD --stat` — files touched.
   - If a ticket is active, read `.workflow/<TICKET>/prd.md` and
     `.workflow/<TICKET>/review.md`.

3. Push: `git push -u origin HEAD`.

4. Build the PR body from `.github/pull_request_template.md` if present, otherwise from
   `.claude/skills/dev-workflow/templates/pull_request.md`. Fill it in:
   - **Summary** from the PRD summary (2-3 sentences).
   - **Ticket** link.
   - **What changed** — bullet per requirement or per commit, with the key files.
   - **Testing** — the actual commands run and their results from `progress.md`.
   - **Review notes** — carry over the verdict and any unresolved findings / follow-ups
     from `review.md` (e.g. "API-231a must land before lowering the prod default").
   - **Rollout** from the PRD rollout section if non-trivial.
   - Leave checklist items unchecked that you can't verify; note which.

5. Create the PR:
   ```
   gh pr create --title "<TICKET>: <short title>" --body-file <tmpfile> --base main
   ```
   Use `--draft` if the review verdict was "not ready" or tests are failing.

6. End the PR body with:
   ```
   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   https://claude.ai/code/session_014W3gFu2fNbFwM7yrzQKqUv
   ```

7. Report the PR URL. Do not merge.
