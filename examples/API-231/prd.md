# PRD: API-231 — Rate-limit the public search endpoint

- **Ticket:** https://example.atlassian.net/browse/API-231
- **Spec:** ./spec.md
- **Status:** reviewed <!-- draft | approved | implemented | reviewed -->
- **Last updated:** 2026-09-10

## Summary

Add per-client rate limiting to `GET /v1/search`, the API's most expensive unauthenticated
read path. A token-bucket limiter backed by the existing Redis cluster caps each client
(by API key, or by IP when anonymous) at a configurable default of 60 requests/minute,
with per-key overrides for high-volume partners. Requests over the limit receive a 429
with `Retry-After`. Limits are adjustable at runtime without a deploy. The goal is to
stop a single abuser from degrading latency for everyone, which happened in production
on 2026-09-02.

## Background

On 2026-09-02 one client sent ~4k req/min for six hours, pushing API-wide p99 from 180ms
to 2.1s until on-call manually blocked the IP. `/v1/search` fans out to Elasticsearch and
Postgres and has no throttling. See spec for the current request path and the Redis /
config / metrics facilities being reused.

## Goals

- Bound any single client's share of `/v1/search` capacity.
- Let operators change limits without a deploy.
- Keep well-behaved traffic (partners included) unaffected.
- Emit a signal that abuse is occurring.

## Non-goals

- Rate-limiting endpoints other than `/v1/search`.
- A general-purpose rate-limit framework for all routes.
- Per-user limits (as opposed to per-key / per-IP).
- An admin UI or API for editing limits — ops edit the Redis config key directly.
- Alerting rules themselves (metric now; alert is a follow-up — see Open questions).

## Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | Requests exceeding the client's limit return HTTP 429 with a `Retry-After` header (integer seconds until one token is available). | must |
| R2 | The rate-limit key is the API key from `request.state.api_key` when present, otherwise `ip:{request.state.client_ip}`. | must |
| R3 | Algorithm is a token bucket (lazy refill), not a fixed window. Check-and-decrement is atomic across app servers. | must |
| R4 | Default limit is 60 rpm with burst capacity 60, set via `RATELIMIT_SEARCH_RPM` / `RATELIMIT_SEARCH_BURST`. | must |
| R5 | Per-API-key overrides are supported and take precedence over the default. | must |
| R6 | The default and overrides can be changed at runtime (≤30s propagation) by writing the `rl:search:config` Redis key, with env vars as bootstrap/fallback. | must |
| R7 | Limiter state is in Redis (shared cluster), so it survives a single app-server restart and is consistent across servers. | must |
| R8 | If Redis is unavailable or the config key is unreadable, the limiter fails open (request proceeds) and emits a metric. | must |
| R9 | A Prometheus counter `search_ratelimit_throttled_total` (labels: `key_type` = `api_key`\|`ip`) increments on each 429. A counter `search_ratelimit_failopen_total` increments on limiter errors. | must |
| R10 | Successful and throttled responses both carry `X-RateLimit-Limit` and `X-RateLimit-Remaining`; 429s also carry `Retry-After`. | should |
| R11 | Added latency on under-limit requests is one Redis round trip and no more (single `EVAL`). | should |
| R12 | Limiting is scoped to the search route via a FastAPI dependency, not global middleware. | should |

## User-facing behavior

**Primary flow (under limit):** client calls `GET /v1/search?q=...` → dependency resolves
`client_id`, runs the bucket script, a token is available → handler runs → 200 with
`X-RateLimit-Limit: 60`, `X-RateLimit-Remaining: 41`.

**Over limit:** same call, bucket empty → dependency raises 429 before the handler runs →
body `{"detail": "Rate limit exceeded"}`, headers `Retry-After: 4`,
`X-RateLimit-Limit: 60`, `X-RateLimit-Remaining: 0`. Counter increments.

**Partner with override (`RATELIMIT_SEARCH_OVERRIDES={"pk_live_abc": 300}`):** limit
resolves to 300 rpm for that key; behaves as above at the higher threshold.

**Redis down:** dependency catches the connection error → request proceeds as 200 → no
rate-limit headers → `search_ratelimit_failopen_total` increments.

**Anonymous burst from one IP:** all requests share key `ip:203.0.113.7`; excess gets 429.

## Acceptance criteria

- [x] AC1: A client making 61 requests in a minute at default config gets ≥1 `429`, and the 429 has an integer `Retry-After` > 0. *(R1, R4)*
- [x] AC2: With `api_key` set, throttling is keyed by the key; a second client with a different key (same IP) is unaffected. *(R2)*
- [x] AC3: With no `api_key`, two requests from the same `client_ip` share a bucket; requests from a different IP are independent. *(R2)*
- [x] AC4: 100 concurrent requests against a bucket of capacity 10 result in exactly 10 allowed and 90 throttled (Lua atomicity). *(R3)*
- [x] AC5: Setting `rl:search:config` to `{"default_rpm": 5}` causes the effective limit to become 5 within 30s with no restart. *(R6)*
- [x] AC6: An override for key K is honored even when `rl:search:config` has a lower default. *(R5)*
- [x] AC7: Bucket state written by one process is observed by another (integration test with two client instances / shared fakeredis). *(R7)*
- [x] AC8: When the Redis client raises on `EVAL`, the request returns 200 and `search_ratelimit_failopen_total` increases by 1. *(R8, R9)*
- [x] AC9: Every 429 increments `search_ratelimit_throttled_total` with the correct `key_type` label. *(R9)*
- [x] AC10: A 200 response includes `X-RateLimit-Limit` and `X-RateLimit-Remaining`; the remaining value decreases across successive calls. *(R10)*
- [x] AC11: Only `/v1/search` is affected — a request to another endpoint at 100 rpm is never throttled. *(R12)*

## Rollout

1. Ship dark: deploy with `RATELIMIT_SEARCH_RPM` set very high (e.g. 100000) so nothing
   is throttled; confirm the `EVAL` path and metrics work in prod.
2. Set the 5 known partner keys in `RATELIMIT_SEARCH_OVERRIDES` before lowering the default.
3. Lower the default to 60 via the `rl:search:config` Redis key (no deploy). Watch
   `search_ratelimit_throttled_total` and p99.
4. **Reverse:** raise the Redis config default back to 100000, or remove the dependency
   from the route and redeploy. No data migration to undo.

## Metrics / success

- API-wide p99 stays flat during a synthetic 4k-rpm single-client load test (the
   2026-09-02 scenario).
- `search_ratelimit_throttled_total` is ~0 for partner keys after step 2.
- No increase in partner-reported errors in the week after step 3.

## Open questions

- [x] `X-RateLimit-*` on 200s too? — **Yes**, confirmed with PM 2026-09-10 (R10).
- [ ] Add the abuse alert now or later? — **Later.** Metric ships with this work
  (R9); alert threshold is a fast-follow once we see a week of baseline data.
