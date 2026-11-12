# deckagent

Notes on making an AI-assisted dev workflow portable across LLM coding
providers — today Claude Code, OpenAI Codex, and Google Gemini CLI /
Antigravity — so switching from one to another means replugging a config,
not rebuilding a setup.

## The six layers

Every agent CLI/app exposes roughly the same six layers. What differs is
whether a layer has converged on an open, shared format or stays
proprietary to one vendor.

| Layer | Claude Code | Codex | Gemini CLI / Antigravity | Portable today? |
|---|---|---|---|---|
| Project instructions | `CLAUDE.md` (falls back to `AGENTS.md` since v2.1.281, Sep 2026) | `AGENTS.md` (native) | `GEMINI.md`, or `AGENTS.md` if `context.fileName` is set | **Yes** — converge on `AGENTS.md` |
| Reusable workflows | Agent Skills (`.claude/skills/`) | Agent Skills (`.agents/skills/`) | Agent Skills (`~/.gemini/antigravity/skills/`) | **Yes, format** — `SKILL.md` is an open standard (Dec 2025), but each tool looks in a different directory |
| Tool integrations | MCP servers | MCP servers (`config.toml`) | MCP servers (`mcp_config.json`) | **Yes, protocol** — MCP is shared, but each tool's registered servers are separate and must be re-added per tool |
| Subagents | `.claude/agents/*.md` | no equivalent surfaced | no equivalent surfaced | **No** |
| Lifecycle hooks | `settings.json` hooks | not user-configurable in `config.toml` | `/hooks` (different event names/schema) | **No** — same idea, incompatible syntax |
| Marketplace plugins | Claude plugin marketplace | own OpenAI plugin marketplace | own extension system | **No** |
| Memory | file-based `MEMORY.md` (readable/editable) | internal sqlite (opaque) | writes into `GEMINI.md` via `/memory` | **No**, except Gemini happens to land in the same file as layer 1 |
| Org governance | Anthropic-side managed settings (server-pushed) | would need separate OpenAI org policy | would need separate Google org policy | **No** — does not propagate across vendors at all |

## What this means in practice

1. **Instructions**: ship one `AGENTS.md` per project instead of a
   `CLAUDE.md`. Claude Code reads it automatically when no `CLAUDE.md` is
   present (or set `"instructionFile": "claude-md-and-agents-md"` to load
   both); Gemini needs `context.fileName` in `~/.gemini/settings.json` to
   include `"AGENTS.md"`.

2. **Skills**: the `SKILL.md` format itself is portable, the install path
   is not. Syncing `claude/skills/global/*` into `.agents/skills/` (Codex)
   and `~/.gemini/antigravity/skills/` (Antigravity) is a copy/symlink
   step, not a rewrite.

3. **MCP servers**: the protocol is shared, the registration is not. Any
   server added for one tool (e.g. `motion`, `figma`) needs the equivalent
   entry re-added in each tool's own config file.

4. **Subagents, hooks, plugins**: no cross-tool equivalent exists today.
   Treat these as throwaway, tool-specific conveniences rather than
   portable config — rebuilding them per tool is the expected cost, not a
   gap to fix.

5. **Memory**: don't rely on any tool's built-in memory for continuity
   across providers — it's proprietary per tool (opaque sqlite for Codex,
   an open file for Claude, folded into `GEMINI.md` for Gemini). Durable
   facts that must survive a provider switch belong in `AGENTS.md` itself.

6. **Org governance**: policy enforced via one vendor's managed settings
   (e.g. an employer's Claude Code admin console policy) does not apply
   when working from a different provider. This is a policy question for
   whoever administers AI tooling, not something a dotfile can patch —
   the best available stopgap is duplicating the policy text into
   `AGENTS.md` so the *instructions* travel, with the caveat that no tool
   will enforce them the way managed settings do.

## Where this fits in denv

`claude/` is the first tool folder in this repo. The same shape — one
top-level folder per tool, split into self-contained, independently
adoptable units — should extend to `codex/` and `gemini/` (or
`antigravity/`) folders as those setups get built out, with `AGENTS.md`
and shared MCP server definitions as the pieces meant to be copied
identically into each.
