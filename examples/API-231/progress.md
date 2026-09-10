# Progress: API-231

Tracking against PRD requirements and acceptance criteria. Base branch: `main`.
Branch: `api-231-search-rate-limit`.

## Requirements

- [x] **R1** 429 + `Retry-After` — `app/ratelimit/dependency.py:41-55`. `Retry-After` is
  `ceil(tokens_needed / refill_rate_per_sec)`.
- [x] **R2** key = api_key else `ip:{client_ip}` — `app/ratelimit/dependency.py:22-28`.
- [x] **R3** token bucket, atomic — `app/ratelimit/bucket.py:12-33` (`BUCKET_LUA`), single
  `EVAL`. Refill is lazy from `now - updated_at`.
- [x] **R4** defaults 60/60 via env — `app/config.py:61-63`, `app/ratelimit/config.py:18-24`.
- [x] **R5** per-key overrides win — `app/ratelimit/config.py:33-41`.
- [x] **R6** runtime reload via `rl:search:config`, 30s in-process TTL — 
  `app/ratelimit/config.py:44-78`. Env values written to the key on startup if absent
  (`app/ratelimit/config.py:81-90`, called from `app/main.py:57`).
- [x] **R7** state in shared Redis — keys `rl:search:{client_id}` hash, `bucket.py`.
- [x] **R8** fail open + metric on Redis / config error — `dependency.py:57-66`,
  `config.py:70-77`.
- [x] **R9** counters `search_ratelimit_throttled_total{key_type}` and
  `search_ratelimit_failopen_total` — `app/ratelimit/metrics.py:5-14`.
- [x] **R10** `X-RateLimit-*` on 200 and 429 — 429 path in `dependency.py:48-53`; 200 path
  needed a response hook, added via `Response` param in the route
  (`app/api/routes/search.py:17-33`).
- [x] **R11** one round trip — verified: exactly one `EVAL`, no `GET`/`SET` around it.
- [x] **R12** route dependency, not middleware — `app/api/routes/search.py:14`
  `dependencies=[Depends(rate_limit_search)]`.

## Acceptance criteria

AC1–AC11: all covered by tests in `tests/ratelimit/` and `tests/api/test_search_ratelimit.py`.
See review.md for the per-AC evidence table.

## Tests / checks run

```
$ pytest tests/ratelimit tests/api/test_search_ratelimit.py -q
....................                                                      [100%]
20 passed in 3.14s

$ pytest -q          # full suite, no regressions
............................................................................ [100%]
412 passed in 41.7s

$ ruff check app tests && mypy app
All checks passed!
Success: no issues found in 9 source files
```

## PRD deltas

1. **R10 needed a route signature change.** The PRD implied headers could be set entirely
   in the dependency. FastAPI dependencies can't mutate the final response headers for the
   200 path cleanly, so the route handler now takes `response: Response` and the
   dependency stashes limit/remaining on `request.state`. Documented; PRD "User-facing
   behavior" still accurate. No scope change.
2. **`Retry-After` rounding:** PRD said "seconds until one token is available"; chose
   `ceil` so the value is never 0 for a throttled request (a 0 would invite an immediate
   retry that also fails). Noted in AC1.
3. Discovered `request.state.client_ip` is `None` in unit tests that bypass
   `APIKeyMiddleware`. Added a fallback to `request.client.host` in `dependency.py:26`
   so the limiter is testable in isolation and safe if middleware order regresses.
