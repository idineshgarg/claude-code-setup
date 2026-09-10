---
description: Stage changes and create well-formed commit(s) for the current work
argument-hint: "[optional scope note, e.g. 'just the ratelimit module']"
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git log:*), Bash(git commit:*), Bash(git branch:*), Read
---

## Commit

Optional scope note: **$ARGUMENTS**

1. Run `git status` and `git diff` (staged + unstaged) to see everything that changed.
   Also `git log --oneline -8` to match the repo's commit-message style.

2. **Branch check:** if the current branch is `main` / `master`, stop and ask the user
   to name a branch (suggest `<ticket-key>-<slug>` if a `.workflow/` ticket is active).
   Do not commit to the default branch.

3. Decide on grouping:
   - If the changes are one coherent unit, make a single commit.
   - If they span clearly separable concerns (e.g. a refactor + a feature, or two
     unrelated fixes), stage and commit them separately. Never split so finely that a
     commit doesn't build or pass tests on its own.
   - Honor the scope note if the user gave one.

4. For each commit:
   - Stage only the relevant paths (`git add <paths>`), not `git add -A`, unless it's
     genuinely everything.
   - Message: a concise summary line (imperative mood, ~50 chars, no trailing period),
     a blank line, then a body explaining **why** when it isn't obvious. Wrap at 72.
   - If a `.workflow/<TICKET>/` is active, prefix the summary with the ticket key
     (`API-231: ...`) and reference the requirement IDs in the body where relevant.
   - End the message with:
     ```
     Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
     Claude-Session: https://claude.ai/code/session_014W3gFu2fNbFwM7yrzQKqUv
     ```

5. Do not push and do not create a PR — that's `/pr`. Report the commit hashes and
   one-line summaries.

Never use `git commit --no-verify`. If a pre-commit hook fails, fix the cause or tell
the user.
