<!--
Reference PR template for the dev workflow. `/pr` fills this in from the PRD and review.
Copy to .github/pull_request_template.md to make it the repo default for every PR.
-->

## Summary

<!-- 2-3 sentences: what this PR does and why. Pull from the PRD summary. -->

## Ticket

<!-- e.g. Closes API-231 -->

## What changed

<!-- One bullet per requirement or logical change. Name the key files/modules. -->
-

## Testing

<!-- The actual commands run and their results. Not "tested locally". -->
```
```

- [ ] Unit / integration tests added or updated
- [ ] Full suite passes locally
- [ ] Lint / type checks pass

## Behavioral change

<!-- What a user, caller, or operator will observe differently. "None" if internal only. -->

## Rollout

<!-- Flags, migrations, sequencing, and how to reverse. Omit if it's a plain merge. -->

## Review notes

<!-- Verdict from review.md. List any known findings shipping as follow-ups and the
     conditions on them (e.g. "must land before X"). Don't hide these. -->

## Checklist

- [ ] PRD acceptance criteria met (or deviations documented in the PRD)
- [ ] No unrelated changes bundled in
- [ ] Docs / comments updated where behavior changed
- [ ] Follow-up tickets filed for deferred work
