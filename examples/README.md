# Worked example

`API-231/` is a complete run of the workflow for one ticket, so you can judge the
output without running anything. The ticket, spec, and codebase references are
fictional but realistic (a FastAPI service).

| File | Stage | What to look at |
|------|-------|-----------------|
| `ticket.md` | 1 — `/read-ticket` | The raw input: acceptance criteria + two constraining comments from PM and Staff Eng. |
| `spec.md` | 2 — `/make-spec` | Design-altitude approach, alternatives with reasons, a risk list, and open questions — two already resolved from the ticket, two left for a human. |
| `prd.md` | 3 — `/make-prd` | Numbered requirements (R1–R12) with priorities, 11 testable acceptance criteria each tracing to a requirement, and a staged rollout with a reverse plan. |
| `progress.md` | 4 — `/implement` | Per-requirement checklist with `path:line` evidence, real test output, and a **PRD deltas** section where implementation forced three small doc corrections. |
| `review.md` | 5 — `/review-prd` | Per-requirement verdict table, four findings (two worth fixing before the prod rollout), PRD corrections applied, and follow-up tickets. Verdict: *ship with follow-ups*. |
| `pull_request.md` | `/pr` | The PR body generated from the three docs above — summary, per-requirement change list, real test output, and the unresolved findings surfaced (not buried) as blocking follow-ups. |

The thing to notice across the five files: the PRD is not write-once. Stage 4 flags
where it was wrong, stage 5 corrects it and downgrades one requirement to "approved in
intent, tracked as a follow-up." That feedback loop is the point of the workflow.
