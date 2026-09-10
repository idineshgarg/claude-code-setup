<!-- The PR body /pr would generate for API-231, from prd.md + progress.md + review.md. -->

## Summary

Adds per-client rate limiting to `GET /v1/search`, the API's most expensive
unauthenticated read path. A token-bucket limiter backed by the existing Redis cluster
caps each client (by API key, or by IP when anonymous) at a configurable default of
60 req/min, with per-key overrides for high-volume partners. Over-limit requests get a
429 with `Retry-After`. Limits are adjustable at runtime without a deploy. This closes
the gap that let a single client push API-wide p99 from 180ms to 2.1s on 2026-09-02.

## Ticket

Closes API-231

## What changed

- **`app/ratelimit/bucket.py`** — `TokenBucket` with lazy refill; check-and-decrement is
  a single atomic `EVAL` (Lua) so it's race-free across the 6 app servers. *(R3, R7, R11)*
- **`app/ratelimit/config.py`** — limit resolution (per-key override → default), with a
  30s in-process cache over the `rl:search:config` Redis key for no-deploy changes; env
  vars seed the key on startup. *(R4, R5, R6)*
- **`app/ratelimit/dependency.py`** — `rate_limit_search` FastAPI dependency: resolves the
  client key (`api_key` else `ip:{client_ip}`), calls the bucket, raises 429 +
  `Retry-After` on rejection, fails open on Redis errors. *(R1, R2, R8)*
- **`app/ratelimit/metrics.py`** — `search_ratelimit_throttled_total{key_type}` and
  `search_ratelimit_failopen_total`. *(R9)*
- **`app/api/routes/search.py`** — wires the dependency onto the route only (not global
  middleware) and sets `X-RateLimit-*` headers on the 200 path. *(R10, R12)*
- **`app/config.py` / `app/main.py`** — new settings + startup seed of the Redis config key.

## Testing

```
$ pytest tests/ratelimit tests/api/test_search_ratelimit.py -q
20 passed in 3.14s

$ pytest -q          # full suite
412 passed in 41.7s

$ ruff check app tests && mypy app
All checks passed!
Success: no issues found in 9 source files
```

- [x] Unit / integration tests added or updated (`tests/ratelimit/`, `tests/api/test_search_ratelimit.py`) — 11 ACs, each with a named test
- [x] Full suite passes locally
- [x] Lint / type checks pass

## Behavioral change

`GET /v1/search` can now return `429 Too Many Requests` with `Retry-After`,
`X-RateLimit-Limit`, and `X-RateLimit-Remaining`. 200s also carry the two
`X-RateLimit-*` headers. Partners on overrides are unaffected at their configured rate.
Under-limit requests add one Redis round trip (~0.3ms local).

## Rollout

1. Deploy dark: `RATELIMIT_SEARCH_RPM=100000` — nothing throttled, confirm `EVAL` path
   and metrics in prod.
2. Set the 5 partner keys in `RATELIMIT_SEARCH_OVERRIDES`.
3. Lower the default to 60 by writing `rl:search:config` (no deploy). Watch
   `search_ratelimit_throttled_total` and p99.
- **Reverse:** raise the Redis config default, or drop the route dependency and redeploy.
  No data migration to undo.

## Review notes

Verdict from `review.md`: **ship with follow-ups**. R1–R12 are met and tested.

Shipping with two known narrow gaps (operator-error / Redis-partial-outage paths):
- **API-231a** — fail open on config-key *read* and *parse* errors (F1, F2). Currently a
  Redis error while reading config, or a malformed `rl:search:config`, 500s instead of
  failing open. **Must land before rollout step 3** (lowering the prod default).
- **API-231b** — abuse alert on `search_ratelimit_throttled_total` (deferred from the PRD
  by design; metric ships here).
- **API-231c** — prod micro-benchmark confirming the one-round-trip claim (R11).

## Checklist

- [x] PRD acceptance criteria met (deviations D1–D3 documented in `prd.md` / `progress.md`)
- [x] No unrelated changes bundled in
- [x] Docs / comments updated where behavior changed
- [x] Follow-up tickets filed for deferred work (API-231a/b/c)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
