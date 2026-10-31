# claude

Setup pieces for Claude Code (the CLI). Each subfolder is one independent concern — apply any subset without needing the others. All subfolders target files under `~/.claude/` on the machine being set up.

Because several subfolders touch the same file (`~/.claude/settings.json`), **always merge JSON keys into the existing file — never overwrite it wholesale.** If `~/.claude/settings.json` doesn't exist yet, create it with just the keys from the subfolder(s) being applied.

## Subfolders

- `statusline-context-usage/` — custom statusline showing live context-window usage (tokens + %) in the terminal UI.
- `token-shrink-settings/` — settings that reduce the token footprint of every session's system prompt by disabling unused built-in features/tools.
- `skills/` — custom Claude Code skills (slash-command-style reusable instructions), organized by scope.

More subfolders will be added as other Claude setups get transported here.
