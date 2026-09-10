# claude-code-setup

[![CI](https://github.com/idineshgarg/claude-code-setup/actions/workflows/ci.yml/badge.svg)](https://github.com/idineshgarg/claude-code-setup/actions/workflows/ci.yml)

A ticket-to-implementation dev workflow for Claude Code.

## The workflow

```
/read-ticket PROJ-123   →  .workflow/PROJ-123/ticket.md
/make-spec   PROJ-123   →  .workflow/PROJ-123/spec.md      (stops for open questions)
/make-prd    PROJ-123   →  .workflow/PROJ-123/prd.md       (stops for approval)
/implement   PROJ-123   →  code + .workflow/PROJ-123/progress.md
/review-prd  PROJ-123   →  .workflow/PROJ-123/review.md    (verdict + PRD corrections)
/commit                 →  grouped commits on a feature branch
/pr          PROJ-123   →  pushes + opens a PR, body filled from the PRD & review
```

`/commit` and `/pr` also work standalone on any change, not just workflow output.

Or just tell Claude "run the dev workflow for PROJ-123" and the `dev-workflow` skill
drives all five stages, pausing for review after the spec, the PRD, and the review.

See [`examples/API-231/`](examples/) for a full worked run of all five stages.

## Layout

```
.claude/
  skills/dev-workflow/
    SKILL.md              orchestration + conventions
    templates/spec.md
    templates/prd.md
    templates/pull_request.md
  commands/
    read-ticket.md        stage 1
    make-spec.md          stage 2
    make-prd.md           stage 3
    implement.md          stage 4
    review-prd.md         stage 5
    commit.md             grouped commits
    pr.md                 open a PR
.github/
  pull_request_template.md   repo default PR body (copy of the template)
```

## Prerequisites

- **jira-cli** for stage 1: `brew install jira-cli` then `jira init`.
  Without it, paste ticket contents into the prompt instead.
- **gh** for `/pr`: `brew install gh` then `gh auth login`. Without it, `/pr` prints
  the `git push` command and stops.

## Install

**Per project (recommended):** copy the `.claude/` directory into the repo you work in.
Commands and skills are picked up automatically.

**Global:** copy `commands/` and `skills/` into `~/.claude/` to use them everywhere.

## CI

`.github/workflows/ci.yml` runs on every PR and on merge to `main`:

| Job | What it checks |
|-----|----------------|
| `markdown-lint` | Markdown is well-formed (`markdownlint-cli2`, config in `.markdownlint-cli2.jsonc`). |
| `validate-workflow` | `scripts/validate_workflow.py` — every command has valid frontmatter with a description, the skill references every command, templates named by the skill exist, and the worked example has all six stage files with its acceptance criteria checked off. Failures show as inline PR annotations and a job summary. |
| `shellcheck` | Any `scripts/*.sh` pass ShellCheck. |
| `post-merge` | Runs only on push to `main`, after the gates pass. Writes a job summary (commit, files changed, message) and emits a structured log line — the seam where a real pipeline would trigger a deploy. |

Run the validator locally: `python3 scripts/validate_workflow.py`

## Notes

- All generated docs live under `.workflow/<TICKET>/`. Add `.workflow/` to `.gitignore`
  unless your team wants specs and PRDs committed.
- Each stage checks that the previous stage's output exists before running.
