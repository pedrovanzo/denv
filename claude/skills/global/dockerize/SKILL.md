---
name: dockerize
description: Scan a project with no Docker setup yet, propose a dockerization plan scoped to what the user actually wants (local image / dev hot-reload / prod-hardened / database), then implement it once approved. Use when the user explicitly asks to dockerize, containerize, or "add Docker to" a project. Does not auto-trigger.
disable-model-invocation: true
---

# Dockerize

Take a project with no Docker setup and add one, scoped to what the user actually needs — not everything at once.

## 1. Scan

### Host tooling

Check the host has what's needed to actually build/run what this skill generates:

- `docker --version`
- `docker compose version`
- `docker info` (confirms the daemon is actually running, not just installed)

If anything is missing or fails:

- Report exactly what's missing.
- Suggest the standard install for the detected OS: **macOS/Windows** → Docker Desktop (docker.com); **Linux** → Docker Engine + the `docker-compose-plugin` via the distro's package manager or `get.docker.com`.
- Ask whether to pause here until it's installed, or continue generating files now and skip the verify step (4) until tooling is in place. Don't silently pick one.

### Existing Docker setup

Check for a `Dockerfile` or any `docker-compose*.yml` already in the project.

If found: **stop here.** Tell the user a Docker setup already exists and this skill is for projects starting from zero. Suggest the `dockerization-review` skill by name as the likely better fit — as a suggestion only. Do not invoke it, do not chain into it, do not take any further action. The user decides the next step manually.

### Project stack

Once host tooling is confirmed (or the user opted to continue anyway) and no existing Docker setup blocks progress, establish:

- **Language/framework**: read the manifest (`package.json`, `requirements.txt`/`pyproject.toml`, `go.mod`, `Gemfile`, `pom.xml`/`build.gradle`, etc.) and lockfile. Identify the framework (Next.js, Express, Django, Rails, Spring, plain Go binary, ...) — it drives build steps, the run command, and the port.
- **Entry point / start command**: how the app is normally run in dev (`npm run dev`, `python manage.py runserver`, ...) and in prod (`npm start`, a compiled binary, gunicorn, ...).
- **Runtime dependencies**: a database, cache, queue, or other service the app talks to. Check for a `DATABASE_URL`-shaped env var, an ORM config, references to a service the app expects to reach, etc.
- **Existing env handling**: `.env` / `.env.example` files, and which vars are build-time (baked into a client bundle) vs runtime (read by the server process). This distinction matters later — get it right now, don't guess at build time.
- **Language/runtime version pinning**: `engines` field, `.nvmrc`, `go.mod`'s `go` directive, etc. — the base image tag should match, not float on `latest`.

Summarize the scan back to the user in a few lines before moving on. Don't skip this even if the stack looks obvious — a wrong assumption here (wrong start command, missed DB dependency) propagates into every file generated next.

## 2. Prompt scope — required, explicit step

Never assume the scope. Ask the user which of the following they want, and let them pick more than one — tiers are stackable: requesting both Dev and Prod-hardened in the same session generates both `docker-compose.override.yml` and `docker-compose.prod.yml`, so both modes exist afterward and you choose which to invoke each time, not one instead of the other.

1. **Local** — Dockerfile + `.dockerignore` only; build and run by hand with plain `docker build`/`docker run`.
2. **Compose base** — `docker-compose.yml` replacing raw `docker run`; worth it once there's more than one thing to start together, the run command's getting unwieldy, or a Dev setup's volume flags (bind mount plus `node_modules`/`.next` exclusions — see tier 3) are easier kept as reviewable config than retyped on every `docker run`.
3. **Dev** — bind-mounted hot reload, host edits show up without a rebuild, and without ever bundling `node_modules` into the image itself — the container uses its own build-time install, the host's source just layers on top. Via `docker-compose.override.yml` if tier 2 is also picked, or a standalone raw `docker run -v` flow if not — offered alongside Local, never replacing it.
4. **Prod-hardened** — multi-stage build, non-root user, healthcheck, restart policy, minimal runtime image.
5. **Database** — DB service in Compose, migrations either auto-run on boot or left as a documented manual step.

If the user doesn't choose, default to **Local** only (tier 1).

## 3. Implement

Generate files matching the confirmed scope. Prefer multi-stage builds even for "Local"-only scope if the framework has a build step (compiles to static output, bundles a server) — it's not extra work and avoids a rewrite when the user later adds "Prod-hardened".

General shape, regardless of stack:

- **Non-root user** in the runner/final stage — exact `useradd`/`adduser` syntax differs (Debian/Ubuntu vs Alpine vs distroless has no shell at all, set `USER` numerically instead).
- **Healthcheck target**: use whatever endpoint the app actually exposes (`/health`, `/`, `/-/ready`); confirm it responds without auth before wiring the healthcheck to it. Confirm the base image actually has the tool the healthcheck command needs (`curl`/`wget`) before assuming it — minimal images often ship neither.
- **Database service**: official image, named volume, healthcheck via the DB's own readiness command (`pg_isready`, `mysqladmin ping`, `redis-cli ping`). Wire the app's `depends_on: { db: { condition: service_healthy } }`, not a bare `depends_on` (which only waits for container start, not readiness).
- **Migrations**: if the user asked for auto-run-on-boot, wire it into the dev/prod start command; if they asked for explicit/manual, document the command instead and leave the start command untouched.
- **`container_name`**: always set it — findable in Docker Desktop / `docker ps` instead of an auto-generated name.
- **Healthcheck IP**: use `127.0.0.1`, not `localhost`, inside the container — in a minimal image, `localhost` can resolve to `::1` first and fail if the app isn't also listening on IPv6.
- **Base image size**: when there's a real choice between base images for the same job (e.g. `nginx` vs `nginx-unprivileged` vs `caddy`; `slim` vs `alpine` vs `distroless`), or the user's request signals size-consciousness ("lean", "small image", "minimal"), surface compressed size before pulling — `docker manifest inspect <image>` works without a full pull. Let the user react to the number before committing to a base image, don't just report it after the fact.

### Stack-specific reference

A proven, concrete pattern (real Dockerfile/Compose, not just principles) lives in a separate file per stack, read only when that stack is the one detected in step 1 — keeps this file from bloating with code irrelevant to whatever project is actually being dockerized right now:

- Node / Next.js (and adaptable to other Node frameworks) → `references/node.md`
- Python — Flask/Django/FastAPI → `references/python.md`
- Plain static files, no framework, no build step → `references/static.md`

Read the matching file from the same directory as this SKILL.md before generating files for that stack.

If the detected stack has no matching reference file, apply the general shape above directly using judgment for that ecosystem's own conventions (base image, package manager, venv/module system, non-root syntax). After a successful build+verify, ask the user whether to save the pattern just used as a new `references/<stack>.md` for reuse next time — don't add one unprompted.

## 4. Verify before declaring done

Skip this step (and say so explicitly) if host tooling was missing in step 1 and the user chose to continue without it.

- `docker build` the image(s) for every stage/scope actually generated.
- `docker compose up` (with whichever override files match the confirmed scope) and confirm the app responds — curl the root path or the healthcheck endpoint.
- If a database was added, confirm the app can actually reach it (a real read or write, not just "container is running").
- If dev scope was added, make a trivial source edit and confirm it's reflected without a rebuild (hot reload actually works, not just "bind mount exists").

## 5. Generate docs

Default output path: `DOCKER.md` at the project root. Ask the user to confirm this default or specify a different path/name before writing it — don't assume silently, same rule as the scope prompt in step 2.

**Before writing, check whether that file already exists** (this happens whenever the skill is re-run to add a tier to a project it already dockerized):

- If it doesn't exist, write fresh — proceed as below.
- If it does exist, don't overwrite based only on this session's newly-picked tier(s) — a prior tier's section would silently disappear, and this actually happened once (Dev-tier instructions erased after a later session added Compose base). Instead, derive the *full currently-implemented* scope from what's actually on disk right now — `Dockerfile` present → tier 1, `docker-compose.yml` → tier 2, `docker-compose.override.yml` → tier 3, `docker-compose.prod.yml` → tier 4, a db service in compose → tier 5 — union that with whatever this session just added, and regenerate **every** section from that full union. This also fixes sections whose underlying commands change shape once another tier is added (e.g. Dev's commands switch from raw `docker run -v` to the Compose-override flow once Compose base shows up later) — a stale command left standing next to a new one is worse than a dropped section, so regenerate rather than literally appending.
- Before writing the regenerated file, show the user a short summary of what's changing (sections added, sections whose commands changed) and confirm — never silently replace a `DOCKER.md` the user didn't know was about to change.

Structure as numbered, mirrored flows — same step count and order across sections, so they read as a checklist and diff cleanly against each other. Every section's run step must show the **exact, complete command to type**, not just name which compose files are involved — "which mode am I in" must be answered by which command the user runs, never by which filenames exist on disk.

- **Section 1 — Manual**: build image, run it (raw `docker run` for Local-only scope; `docker compose up` for Compose-based scope), stop, remove container, remove image.
  - If a `docker-compose.override.yml` exists (tier 3 with Compose base): say explicitly that plain `docker compose up` already auto-merges it — no `-f` flags needed — so this is the section that's actually in dev mode whenever that file is present. Don't leave that implicit.
  - If `docker-compose.prod.yml` exists (tier 4): give the exact `docker compose -f docker-compose.yml -f docker-compose.prod.yml up` invocation as its own explicit line — this is the only way to opt into the prod overlay, since Compose never auto-merges a file that isn't literally named `docker-compose.override.yml`.
  - Image removal: `docker image ls` to find the id, then `docker rmi <id>` — never a blanket `docker system prune` / `docker image prune -a`, which touches images and cache unrelated to this project. For Compose-based scopes, `docker compose down --rmi local` is the scoped equivalent.
  - If this section has no bind mount (pure Local, or Compose base without the Dev override), explicitly call out the rebuild-vs-stale-cache gotcha: editing source and re-running the *existing* container/image will not pick up the change — a rebuild comes first. This is the most common first confusion for anyone used to a live-reload dev setup, so it goes in the doc unconditionally, not only when asked.

- **Section 2 — Dev / live-edit** (only if tier 3 was selected in step 2, in either its Compose-override or Local-only-bind-mount form): same step numbering as Section 1, substituting the bind-mount run command. Label this section with the exact command that puts the app in this mode (`docker compose up`, or the full `docker run -v ...` line) right at the top, not buried after the explanation.
  - If the run command is `$(pwd)`-based, warn that it resolves relative to the caller's current directory — `cd` into the project root first, or anchor with an absolute path / `${PWD}`.
  - Include a `curl` snippet against the served endpoint as the way to confirm server-side state independent of browser cache — a page that "isn't updating" is often a browser cache/ETag issue, not a broken mount, and curl isolates which one it is.

Report back what was generated, mapped to the scope the user confirmed in step 2 — not a longer list than what they asked for.
