# API-231 — Rate-limit the public search endpoint

- **Type:** Story
- **Status:** In Progress
- **Assignee:** Dinesh Garg
- **Priority:** High
- **Sprint:** 2026-09 S2
- **Link:** https://example.atlassian.net/browse/API-231

## Description

`GET /v1/search` is unauthenticated and is our most expensive read path (fans out to
Elasticsearch + Postgres). Last week a single client sent ~4k req/min from one IP for
six hours and drove p99 latency on the whole API from 180ms to 2.1s. On-call mitigated
by blocking the IP at the load balancer by hand.

We need per-client rate limiting on this endpoint so a single abuser can't degrade
service for everyone. Limits should be configurable without a deploy.

## Acceptance criteria

- Requests over the limit get HTTP 429 with a `Retry-After` header.
- Limit is keyed by API key when present, otherwise by client IP.
- Default limit is 60 requests / minute / client; overridable via config.
- Rate-limit state survives a single app-server restart (i.e. not purely in-process).
- Normal traffic (< limit) sees no measurable added latency.
- Metric emitted for throttled requests so we can alert on abuse.

## Comments

**PM (2026-09-08):** Please make sure legitimate high-volume partners aren't caught by
this. We have ~5 partner keys that do 200-300 rpm sustained. Per-key overrides are fine.

**Staff Eng (2026-09-08):** We already run Redis for session cache — reuse that cluster,
don't stand up new infra. Token bucket over fixed window please, the burst behavior of
fixed windows has bitten us before.

## Linked issues

- Relates to API-198 (API key middleware — already shipped, provides `request.state.api_key`)
