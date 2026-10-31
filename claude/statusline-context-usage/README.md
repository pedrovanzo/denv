# statusline-context-usage

Custom Claude Code statusline that shows live context-window usage in the terminal UI, as `12.3k (6.8%)` in yellow, next to Claude Code's built-in status text (e.g. "auto mode on").

It works by reading the session transcript's most recent token-usage entry and computing `tokens_used / context_window`.

## What's here

- `context-usage-statusline.js` — the statusline script. Reads JSON on stdin (Claude Code's statusline protocol), reads only the tail of the referenced transcript file, finds the last `message.usage` entry, computes the percentage, and prints a colored one-liner to stdout. Fails silently (prints nothing) on any error, so it can never break the terminal UI.
- `settings.snippet.json` — the `statusLine` key to merge into `~/.claude/settings.json`.

## Setup steps (for the agent applying this)

1. Create `~/.claude/hooks/` if it doesn't exist.
2. Copy `context-usage-statusline.js` into `~/.claude/hooks/context-usage-statusline.js`.
3. Ensure `~/.claude/hooks/package.json` exists with `{ "type": "commonjs" }` (create it if missing) — the script uses CommonJS `require`.
4. Merge the `statusLine` key from `settings.snippet.json` into `~/.claude/settings.json`. If `settings.json` already has a `statusLine` key (e.g. from another setup being transported), ask the user which one should win before overwriting it.
5. Start a new Claude Code session (or restart) to see the statusline take effect.

## Notes

- `CONTEXT_WINDOW` is hardcoded to `1000000` (1M), matching Sonnet 5 / Opus / Fable. If the target machine's default model has a different context window (e.g. Haiku 4.5 at 200k), adjust that constant in the script.
- Requires `node` to be available on PATH.
