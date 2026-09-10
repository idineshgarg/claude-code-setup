# claude-code-setup

A ticket-to-implementation dev workflow for Claude Code.

## The workflow

```
/read-ticket PROJ-123   →  .workflow/PROJ-123/ticket.md
/make-spec   PROJ-123   →  .workflow/PROJ-123/spec.md      (stops for open questions)
/make-prd    PROJ-123   →  .workflow/PROJ-123/prd.md       (stops for approval)
/implement   PROJ-123   →  code + .workflow/PROJ-123/progress.md
/review-prd  PROJ-123   →  .workflow/PROJ-123/review.md    (verdict + PRD corrections)
```

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
  commands/
    read-ticket.md        stage 1
    make-spec.md          stage 2
    make-prd.md           stage 3
    implement.md          stage 4
    review-prd.md         stage 5
```

## Prerequisites

- **jira-cli** for stage 1: `brew install jira-cli` then `jira init`.
  Without it, paste ticket contents into the prompt instead.

## Install

**Per project (recommended):** copy the `.claude/` directory into the repo you work in.
Commands and skills are picked up automatically.

**Global:** copy `commands/` and `skills/` into `~/.claude/` to use them everywhere.

## Notes

- All generated docs live under `.workflow/<TICKET>/`. Add `.workflow/` to `.gitignore`
  unless your team wants specs and PRDs committed.
- Each stage checks that the previous stage's output exists before running.
