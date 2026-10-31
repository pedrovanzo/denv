---
name: costed
description: Walk through a project's real cloud-cost gates one at a time — surface what's currently configured for each, ask why, then either validate it as a deliberate trade-off or map out how to avoid the cost. Not a pass/fail checklist. Use when the user wants to review cloud spend, cost gotchas, or billing risk for a deployed (or about-to-be-deployed) project. Does not auto-trigger.
disable-model-invocation: true
---

# Costed

Cost gates aren't bugs to flag — they're business decisions that may or may not have actually been made on purpose. For every gate below: find what's currently configured, ask the user why it's set that way, then either they confirm it's deliberate and justified, or the gate ends with a concrete cheaper alternative on the table. Never unilaterally declare a gate "wrong" — that's the user's call, not this skill's.

If a gate doesn't apply at all (the feature/service in question doesn't exist in this project), say so and skip the question — don't force an answer to something that isn't there.

## 1. Detect deploy context

Before walking the gates, find what's actually inspectable:

- Repo config: `docker-compose.yml`, `fly.toml`, `render.yaml`, Kubernetes manifests, CI workflow files (`.github/workflows/*.yml`), a `Dockerfile`.
- Live state, only if the matching CLI is already authenticated (don't prompt to set one up just for this): `gcloud run services describe`, `aws ecs describe-services`, `flyctl status`, `kubectl get`, etc. Live state is more accurate than repo config when the two might have drifted (a manual `gcloud run deploy` flag that was never written back to a script).

Summarize what was found before moving to the gates — which platform, and whether the answers below come from live state or repo files only.

## 2. Walk the gates

### Gate 1 — Minimum instances / always-on floor
Look for: `--min-instances` (Cloud Run) or equivalent (ECS desired-count floor, Fly `min_machines_running`, an always-on dyno). Anything above 0 means paying for idle time.
Ask: avoiding cold-start latency for real user-facing traffic, or a leftover default?

### Gate 2 — Maximum instances / scaling ceiling
Look for: `--max-instances` or equivalent. Unbounded means a traffic spike (bot storm, retry loop, actual DDoS) has no cost ceiling at all.
Ask: is there a deliberate ceiling sized against a real budget, or was this simply never set?

### Gate 3 — CPU/resource allocation mode
Look for: Cloud Run's CPU-always-allocated vs. request-only billing; the equivalent reserved-vs-burstable choice elsewhere.
Ask: does the app do background work between requests that genuinely needs always-allocated CPU, or is request-only enough?

### Gate 4 — Resource sizing vs. actual usage
Look for: memory/CPU limits in the service config, Dockerfile, or compose file, compared against real observed usage (metrics if available; a rough sniff via `docker stats` under load otherwise).
Ask: sized from real usage data, or a copy-pasted default likely over- or under-provisioned?

### Gate 5 — Cold-start-vs-warm as its own deliberate trade-off
Distinct from Gate 1: even if scale-to-zero is chosen on purpose, is the resulting cold-start latency actually acceptable to these specific users?
Ask: has cold-start time been measured against real user tolerance, or is "scale to zero" assumed free of user-facing cost just because it's dollar-free?

### Gate 6 — Managed dependency tier (DB, cache, queue, search, etc.)
Look for: any managed service the app depends on, and its pricing tier — a fixed-floor paid tier vs. a real free/scale-to-zero tier for the same job.
Ask: was the tier picked by comparing floor cost against actual need, or defaulted to whatever the platform suggested first?

### Gate 7 — Registry/image retention
Look for: a cleanup/lifecycle policy on wherever images get pushed (Artifact Registry, GHCR, ECR) — doubly relevant if dual-pushing to more than one registry.
Ask: is old/untagged image storage actually being cleaned up, or growing unbounded?

### Gate 8 — Logging/observability volume
Look for: log level shipped to a paid ingestion sink (Cloud Logging, Datadog, etc.), and any trace/error-tracking sampling rate.
Ask: is debug-level output gated behind an environment check before it reaches a paid sink, or does it ship unconditionally?

### Gate 9 — Concurrency setting
Look for: `--concurrency` (Cloud Run) or the equivalent requests-per-instance setting.
Ask: does this match the app's actual capacity to handle concurrent requests — too low spins up more billed instances for the same load, too high risks overload?

### Gate 10 — Egress/network transfer
Look for: where large assets are served from (the app container itself vs. a CDN/object storage with its own egress allowance), and whether compute and its dependencies share a region.
Ask: is cross-region traffic or large-asset egress a deliberate choice, or just an accident of where things happened to get created?

### Gate 11 — CI/build minutes
Look for: whether CI reuses build cache/layers or rebuilds from scratch every run, and how close usage sits to the free-tier ceiling on a private repo.
Ask: has anyone actually checked CI minutes usage lately, or is it just assumed fine?

### Gate 12 — Duplicate environments
Look for: staging/dev/preview environments running as fully always-on, production-tier resources.
Ask: does a staging copy need to be always-on and full-sized, or would ephemeral/scale-to-zero cover its real (rarely-used, non-user-facing) usage pattern?

### Gate 13 — Retry/backoff amplification
Look for: client- or server-side retry logic without backoff, able to interact with an uncapped autoscaler (ties back to Gate 2) to self-amplify cost during an incident.
Ask: does a failure mode exist where retries could multiply cost during an outage, and is Gate 2's ceiling actually enough to bound that?

## 3. Report

Summarize every gate's outcome in one pass: validated-as-deliberate (with the stated reason), flagged-for-change (with the concrete cheaper alternative), or not-applicable. Report in the conversation — don't write findings to disk unless the user asks for that specifically this run.
