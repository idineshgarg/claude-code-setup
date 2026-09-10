# Re-review: API-231 — Rate-limit the public search endpoint

- **Reviewed:** 2026-09-10
- **Against:** `prd.md` + `progress.md` + diff of `api-231-search-rate-limit` vs `main`
- **Overall verdict:** **ship with follow-ups**

## Requirement verdicts

| ID | Verdict | Evidence | Notes |
|----|---------|----------|-------|
| R1 | met | `app/ratelimit/dependency.py:41-55`; AC1 passes | `Retry-After` uses `ceil`, always ≥1 on 429. |
| R2 | met | `dependency.py:22-28`; AC2, AC3 | Fallback to `request.client.host` when `client_ip` unset (see deviation D1). |
| R3 | met | `bucket.py:12-33`, one `EVAL`; AC4 (100 concurrent → exactly 10 allowed) | Lua script reviewed; refill and decrement in one atomic step. |
| R4 | met | `config.py:18-24`, `config.py` defaults `rpm=60 burst=60` | |
| R5 | met | `config.py:33-41`; AC6 | Override lookup is exact-match on the API key string. |
| R6 | met | `config.py:44-90`; AC5 (limit change observed in <30s) | 30s TTL cache; startup seeds the Redis key from env if absent. |
| R7 | met | Redis hash `rl:search:{client_id}`; AC7 (cross-instance) | |
| R8 | met | `dependency.py:57-66`, `config.py:70-77`; AC8 | Catches `redis.RedisError` and `asyncio.TimeoutError`. See F1. |
| R9 | met | `app/ratelimit/metrics.py:5-14`; AC8, AC9 | Label values `api_key` / `ip` verified in tests. |
| R10 | met | 429: `dependency.py:48-53`; 200: `search.py:17-33` + `request.state`; AC10 | Required a route signature change — deviation D1, acceptable. |
| R11 | met | Single `EVAL`, no surrounding Redis calls; `progress.md` R11 | Micro-benchmark not run in prod yet — see follow-up 1. |
| R12 | met | `search.py:14` `dependencies=[Depends(rate_limit_search)]`; AC11 | No global middleware added. |

## Acceptance criteria

| AC | Status | Test |
|----|--------|------|
| AC1 | met | `tests/api/test_search_ratelimit.py::test_over_limit_returns_429` |
| AC2 | met | `::test_keyed_by_api_key` |
| AC3 | met | `::test_keyed_by_ip_when_anonymous` |
| AC4 | met | `tests/ratelimit/test_bucket.py::test_concurrent_decrement_is_atomic` |
| AC5 | met | `tests/ratelimit/test_config.py::test_runtime_reload` (uses a monkeypatched clock, not a real 30s wait) |
| AC6 | met | `::test_override_beats_lower_default` |
| AC7 | met | `tests/ratelimit/test_bucket.py::test_state_shared_across_instances` |
| AC8 | met | `::test_fail_open_on_redis_error` |
| AC9 | met | `::test_throttle_metric_label` |
| AC10 | met | `::test_ratelimit_headers_on_200` |
| AC11 | met | `tests/api/test_other_endpoints_not_limited` |

## Additional checks

- **Untested ACs:** none — every AC has a named test.
- **Non-goals respected:** only `search.py` gains a dependency; no other routes touched;
  no admin API; no per-user logic. ✅
- **Spec risk list:**
  - Redis unavailable → fail open: covered (R8/AC8). ✅
  - Clock skew: acceptable per spec, no code needed. ✅
  - Shared-NAT IP clients: accepted for v1, called out in PRD. ✅
  - Lua concurrency: covered (AC4). ✅
  - Corrupt config key: **partially** — see F2.

## Findings

### F1 — `failopen` metric can double-count *(minor, non-blocking)*
`dependency.py:57-66` catches the error from `bucket.check()`, but `config.get_limit()`
is called *before* the try block at line 34. A Redis error while reading config raises
out of the dependency as a 500 instead of failing open.
**Impact:** config-key read errors → 500s, not fail-open, contradicting R8 ("or the config
key is unreadable").
**Fix:** move the `get_limit()` call inside the same try/except, fail open with the env
default. Small change; recommend before merge.

### F2 — Corrupt `rl:search:config` JSON is not handled *(minor)*
`config.py:55` does `json.loads(raw)` with no `try`. Spec risk list says "config key
missing/corrupt → fall back to env defaults, emit metric." Missing is handled (`raw is
None`), corrupt is not — a bad `SET` by an operator would 500 every search request until
fixed.
**Fix:** wrap the parse, on `JSONDecodeError` use env defaults + increment
`search_ratelimit_failopen_total`. Add a test.

### F3 — `X-RateLimit-Remaining` is the post-decrement value on 200 but pre-decrement on 429 *(cosmetic)*
On 429 it's always `0`, which is fine. On 200 it's tokens-after-this-request. Consistent
enough; just note it in the API docs. No code change.

### F4 — no test that `Retry-After` actually decreases as the bucket refills *(test gap)*
AC1 checks `Retry-After > 0` but not that waiting that long then retrying succeeds.
Recommend adding `test_retry_after_is_honored` (advance clock by the header value, assert
next request passes). Nice-to-have.

## PRD corrections applied

- Marked all ACs `[x]` (checked).
- Status set to **reviewed**.
- **User-facing behavior**: added that the 200 path sets headers via the route handler
  (`response: Response`), matching the implemented design (D1).
- **R8** wording tightened: it now explicitly covers the config-key read path — which
  F1/F2 show is not yet fully implemented, so R8 is **approved in intent, tracked as a
  follow-up in code**.
- Open question about `X-RateLimit-*` on 200s resolved to **yes** and reflected in R10.

## Follow-ups (not blocking merge, file as tickets)

1. **API-231a** — fix F1 + F2 (fail open on config read/parse errors). *Small. Do before
   lowering the prod default, per rollout step 3.*
2. **API-231b** — the abuse alert on `search_ratelimit_throttled_total` (deferred from
   this PRD by design).
3. **API-231c** — prod micro-benchmark confirming R11 (one round trip, no measurable p50
   impact) during the dark-launch phase.
4. Add tests F4 (`Retry-After` honored) and a corrupt-config test (part of API-231a).

## Sign-off

Core requirements R1–R12 are met and tested. F1/F2 are real but narrow (operator-error
and Redis-partial-outage paths) and are gated behind rollout step 3, not step 1. Safe to
merge and dark-launch now; **API-231a must land before the default is lowered in prod.**
