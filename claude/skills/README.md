# skills

Custom Claude Code skills — reusable instruction sets Claude loads on demand (via `/skill-name` or auto-trigger on matching intent).

Claude Code skills live in a filesystem location that determines their scope:

- **global** — `~/.claude/skills/<name>/`. Available in every project, on this machine, under this account.
- **project** — `<repo>/.claude/skills/<name>/`, committed to the project's own repo. Shared with anyone working on that project.
- **machine-local** — same shape as global, but meant to never leave this specific machine (e.g. hardware-specific tooling).

## What's here

Only `global/` exists in this batch — every custom skill on my account currently lives at the global (`~/.claude/skills/`) scope. No project-scoped (`<repo>/.claude/skills/`) or machine-local skill directories were found on this machine during this transport. If any show up later (new project repos, etc.), they get their own `project/<repo-name>/` or `machine-local/` folder here.

## Setup steps (for the agent applying this)

1. Copy each folder under `global/` into `~/.claude/skills/` on the target machine.
2. Leave `disable-model-invocation: true` frontmatter as-is — those skills only run when explicitly invoked (e.g. `/skill-name`), not auto-triggered.
3. Skills without that flag can auto-trigger based on their `description`; no extra setup needed beyond copying.

## Skipped skills (not transported)

- **`add-corp-auth`** — skipped on purpose. It's Rede Gazeta-specific (hardcodes the company's Azure AD / corporate SSO portal as the OAuth redirect provider). Not appropriate for a public, general-purpose repo. If needed on another machine, set it up separately through work channels, not via this repo.

## Dependencies not yet transported

The `caveman*` skills (`caveman`, `caveman-commit`, `caveman-compress`, `caveman-help`, `caveman-review`, `caveman-stats`) are copied here as skill definitions, but the full caveman-mode *feature* also relies on hook scripts (`~/.claude/hooks/caveman-activate.js`, `caveman-mode-tracker.js`, `caveman-config.js`, `caveman-stats.js`, `cavecrew-model-overrides.js`) and matching `SessionStart`/`UserPromptSubmit` hook entries in `~/.claude/settings.json`. Those weren't part of this batch — they'll come in a future "claude setting" transport. Until then, the caveman skills here work as plain on-demand skills, just without the automatic session-wide mode persistence.
