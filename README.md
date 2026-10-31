# denv

Personal environment configuration, portable across machines. This repo stores the settings, config snippets, and instructions needed to replicate my personal and working setup (editors, CLI tools, shell, app configs, etc.) on a new computer.

It intentionally contains **no secrets** — no passwords, API keys, tokens, credentials, or anything similarly sensitive. Only configuration, scripts, and documented setup steps.

## Intent

Each top-level folder covers one tool/environment. Inside, configuration is split into self-contained units (one concern each), so pieces can be adopted independently.

Content here is written to be picked up and applied automatically by an LLM coding agent (e.g. Claude Code) running on the target machine, while still being readable by a human doing the same setup manually.

## Contents

- `claude/` — Claude Code setup (terminal UI, settings, skills).

More tool setups will be added over time.
