# Spec: API-231 — Rate-limit the public search endpoint

- **Ticket:** https://example.atlassian.net/browse/API-231
- **Author:** Dinesh Garg
- **Status:** draft
- **Last updated:** 2026-09-10

## Problem

`GET /v1/search` is unauthenticated and the most expensive read path in the API. A single
client sending ~4k req/min recently drove API-wide p99 from 180ms to 2.1s for six hours;
mitigation was a manual load-balancer IP block. There is no per-client throttling today.

## Goal

A single client cannot consume enough `/v1/search` capacity to degrade latency for other
clients, and operators can tune the limit without a deploy.

## Current behavior

- Routing: `app/api/routes/search.py:14` — `@router.get("/search")`, no throttling.
- Middleware stack: `app/main.py:38-52` adds `APIKeyMiddleware` (from API-198), which sets
  `request.state.api_key` (str or `None`) and `request.state.client_ip` (str, already
  X-Forwarded-For aware).
- Redis: `app/cache/redis.py:9` exposes a shared `redis_client` (async, `redis.asyncio`),
  currently used only for session cache under the `sess:` key prefix.
- Config: `app/config.py:Settings` — pydantic `BaseSettings`, env-driven. No hot reload;
  values are read once at startup.
- Metrics: `app/observability/metrics.py` — Prometheus client, `REGISTRY` plus helpers
  like `counter(name, doc, labels)`.
- Tests: `tests/api/test_search.py`, fixtures in `tests/conftest.py` (`client`, plus a
  `fakeredis` fixture `redis_stub` already wired for the session-cache tests).

## Proposed change

Add a token-bucket rate limiter backed by the existing Redis cluster, applied as a
FastAPI dependency on the search route (not global middleware — scope stays narrow and
we avoid touching other endpoints).

### Components

1. **`app/ratelimit/bucket.py`** — `TokenBucket` implementation. One Redis key per client:
   `rl:search:{client_id}` holding `{tokens, updated_at}` as a hash. Refill computed
   lazily on each request from elapsed time. Atomicity via a small Lua script (`EVAL`)
   so check-and-decrement is a single round trip and race-free across app servers.

2. **`app/ratelimit/config.py`** — limit resolution. Order: per-key override → default.
   - Default: `RATELIMIT_SEARCH_RPM` (int, default 60), `RATELIMIT_SEARCH_BURST`
     (int, default = rpm, i.e. bucket capacity).
   - Per-key overrides: `RATELIMIT_SEARCH_OVERRIDES` as JSON `{"<api_key>": rpm}`.
   - **Hot reload:** overrides + default are cached in-process with a 30s TTL and
     re-read from a Redis key `rl:search:config` that ops can `SET`. Env vars are the
     bootstrap/fallback value written into that key on startup if absent.

3. **`app/ratelimit/dependency.py`** — `rate_limit_search` FastAPI dependency:
   resolves `client_id` (`api_key` if present else `ip:{client_ip}`), calls the bucket,
   and on rejection raises `HTTPException(429)` with `Retry-After` (seconds until one
   token is available, ceil).

4. Wire the dependency into `app/api/routes/search.py`.

### Data model changes

None (relational). New Redis keys under a `rl:` prefix.

### API changes

`GET /v1/search` gains a `429 Too Many Requests` response with headers:
- `Retry-After: <seconds>`
- `X-RateLimit-Limit: <rpm>`
- `X-RateLimit-Remaining: <int>`

### Behavioral changes

Clients over their limit get 429s until the bucket refills. Partners with overrides are
unaffected at their configured rate. Under the limit, one extra Redis round trip
(~0.3ms local) per search request.

## Alternatives considered

- **Global middleware instead of a route dependency** — rejected: widens blast radius to
  every endpoint, and the other routes have different cost profiles.
- **Fixed-window counter** — rejected per Staff Eng: window-boundary bursts (2x limit
  across a boundary) have caused incidents before.
- **In-process limiter (e.g. `slowapi` default)** — rejected: state doesn't survive
  restart and isn't shared across the 6 app servers, so effective limit is 6x intended.
- **Sliding-window log in Redis** — more accurate but O(n) memory per client and heavier;
  token bucket is sufficient for abuse prevention.

## Risks and edge cases

- **Redis unavailable:** fail open (allow the request) and emit a metric. A limiter
  outage must not become an API outage.
- **Clock skew across app servers:** refill math uses `time.time()` on each box; skew of
  a few seconds only slightly over/under-fills. Acceptable.
- **IP-keyed clients behind shared NAT:** could collectively hit the IP limit. Accepted
  for v1 — API-key clients (partners) are keyed separately; anonymous users sharing an
  egress IP is exactly the abuse case we're bounding.
- **Lua script correctness** under concurrent access — needs a test with parallel calls.
- **Config key missing/corrupt in Redis:** fall back to env-var defaults, emit a metric.

## Open questions

- [x] Reuse session Redis cluster? — **Yes** (Staff Eng, ticket comment).
- [x] Token bucket vs fixed window? — **Token bucket** (Staff Eng).
- [ ] Should `X-RateLimit-*` headers also be sent on successful (200) responses, or only
  on 429? *(Leaning: always — clients can self-throttle. Confirm with PM.)*
- [ ] Do we alert on throttling now, or just emit the metric and add the alert later?

## Out of scope

- Rate-limiting any endpoint other than `/v1/search`.
- A general-purpose rate-limit framework for all routes (follow-up if this pattern works).
- Per-user (as opposed to per-key / per-IP) limits.
- A UI or admin API for editing limits — ops edit the Redis key directly for v1.
