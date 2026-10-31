---
name: scan-ports
description: Scan for processes running on this Mac that occupy memory/CPU without a visible window — either host-level (macOS listening TCP ports, defaulting to common local dev ports like 3000, 5173, 8080, 5432, 6379, 11434, etc., with an option to widen to every listening port) or Docker containers (running containers, their published ports, CPU%, and memory usage). Then offer to stop/kill selected ones. Use this whenever the user asks what's running on a port, why a port is already in use, wants to find or kill a stray/orphaned dev server or leftover process, mentions "port already in use" or "address already in use" errors, asks to check localhost ports, wants a census of what's currently listening on their machine, or asks what Docker containers are running / using resources right now.
disable-model-invocation: true
---

## What this does

Two separate scan modes for "what's running that I can't see but is using memory/CPU":

- **Host scan** (default) — every process listening on a TCP port directly on the Mac's own network stack. Built for the common "something's still bound to port 3000 and I don't know what" situation after a dev server or a Claude Code session doesn't clean up after itself.
- **Docker scan** — running containers, since Docker on macOS runs everything inside its own Linux VM. Container processes never appear in a host-level port scan (every published container port shows up there as the single opaque `com.docker.backend` VM proxy, not the actual container), so this needs Docker's own CLI instead of `lsof`/`ps`.

These are kept as two separate paths on purpose rather than merged into one scan — they pull from genuinely different sources (macOS process table vs. Docker's own bookkeeping) and mixing their parsing logic together would make both harder to get right.

## Deciding which mode to run

Default to the **host scan**. Switch to the **Docker scan** only when the user's request clearly points at Docker — mentions "docker," "container(s)," or names a specific container/image. When genuinely unclear, host is the safer default since it's the more common ask.

## Host scan

```bash
python3 ~/.claude/skills/scan-ports/scripts/scan_ports.py
```

By default this only scans a curated list of common local dev ports (Next.js, Vite, common API ports, Postgres, Redis, Mongo, RabbitMQ, Ollama, etc — see `DEV_PORTS` in the script). If the user's request implies they want everything — phrases like "scan everything," "all ports," "widen the scan," "what's running on my machine" — pass `--all`:

```bash
python3 ~/.claude/skills/scan-ports/scripts/scan_ports.py --all
```

Use your judgment on which scope matches what they're asking; don't ask them to name a flag, just interpret the request.

The script prints one JSON object to stdout: `scope`, `ports_scanned` (null when `--all`), and `results` — an array of objects with `port`, `protocol`, `pid`, `process`, `app` (resolved parent `.app` bundle name, or null if not inferable), `command` (full path + args), `ppid`, `started` (wall-clock start time), `elapsed`.

Render the results as a markdown table, ordered by port. If `results` is empty, just say so — nothing is listening in the scanned range, nothing further to do.

Worth noting to the user, briefly, if relevant: the `process` field is lsof's own column and can be truncated (e.g. `ControlCe` for ControlCenter) — `command` and `app` are the reliable fields for actually identifying what something is. There is no reliable way to tell whether something was specifically left behind by a Claude Code session; use `ppid` to show lineage (does it trace back to a shell/terminal, or is it a standalone daemon?) so the user can judge for themselves rather than asserting it either way.

**Stopping a host-scan result:**

```bash
kill <pid>
```

Wait a moment, then check whether it's still alive: `kill -0 <pid> 2>/dev/null && echo still-running || echo gone`. If still running, escalate to `kill -9 <pid>`.

## Docker scan

No bundled script needed here — Docker's own `--format` flag already gives clean, structured JSON, unlike `lsof`'s raw text. Run both, one JSON object per line:

```bash
docker ps --format '{{json .}}'
docker stats --no-stream --format '{{json .}}'
```

`docker ps` gives `Names`, `Image`, `State`, `Status`, `Ports`, `RunningFor`. `docker stats` gives `Name`, `CPUPerc`, `MemUsage`, `MemPerc`, `PIDs`. Join the two on the container name and present one table: container, image, ports, uptime, CPU%, memory. This only scans **running** containers, matching the host scan's "only show things actually active," not every container that merely exists — a stopped container uses no CPU or memory, so it's out of scope for what this skill is for. If the user specifically wants to see stopped/exited containers too, that's a `docker ps -a` question, a different ask from resource usage.

**Stopping a Docker-scan result:** `docker stop` already handles graceful-then-forceful escalation internally (SIGTERM, then SIGKILL after its own timeout), so there's no need to reimplement the manual check-then-escalate dance used for host processes:

```bash
docker stop <container-name>
```

Verify afterward with `docker ps --filter name=<container-name> --filter status=running` — empty output means it stopped.

## Confirming before stopping/killing anything

Same rule for both modes: if there's at least one result, ask which (if any) the user wants stopped, using `AskUserQuestion` with multi-select enabled. Label each option clearly enough to identify at a glance — e.g. "Port 3000 — node (PID 12345), running 2h15m" for host, "scan-ports-probe — postgres:16-alpine, 55MB, 0.7% mem" for Docker. Always make it easy to select none — leaving everything untouched is a completely valid outcome and should be the assumed default if the user doesn't pick anything or says to leave things alone. Don't skip straight to stopping/killing without this step, even if the user's original phrasing sounded like they wanted things cleaned up — confirm which ones first.

Report back clearly what was stopped/killed and what was left alone.
