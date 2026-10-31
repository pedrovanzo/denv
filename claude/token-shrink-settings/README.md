# token-shrink-settings

Claude Code settings that cut the token cost of *every* session's system prompt, by turning off built-in features/tools I don't use. Each disabled tool/feature means its definition isn't loaded into context at session start — this adds up across a long session.

## What's here

`settings.snippet.json` — keys to merge into `~/.claude/settings.json`:

- `disableBundledSkills: true` — skip loading Claude Code's bundled/default skills. I bring my own (see `../skills/`).
- `disableClaudeAiConnectors: true` — disable claude.ai connector integrations (not used).
- `disableRemoteControl: true` — disable remote-control session features (not used).
- `disableWorkflows: true` — disable the workflows feature (not used).
- `disableArtifact: true` — disable the Artifact tool (not used).
- `permissions.deny` — an explicit deny list for built-in tools/capabilities I never use: `EnterPlanMode`, `ExitPlanMode`, `DesignSync`, `NotebookEdit`, `SendMessage`, `PushNotification`, `RemoteTrigger`, `ReportFindings`, `ScheduleWakeup`, `AskUserQuestion`, `CronCreate`, `CronDelete`, `CronList`. Denying a tool keeps it out of the active toolset.

## Setup steps (for the agent applying this)

1. Merge these keys into `~/.claude/settings.json`.
2. For `permissions.deny` specifically: merge as a **union** with any existing `permissions.deny` array already in the target's `settings.json` (don't duplicate entries, don't drop entries from another transported setup).
3. For the top-level `disable*` booleans: only apply if the user confirms they also want these features off on the new machine — they're a deliberate trade-off (less functionality, fewer tokens), not a universal default.

## Why this trade-off

Every one of these is a feature/tool I don't use day to day. Disabling what you don't use is the highest-leverage way to shrink the fixed token overhead Claude Code pays on every single message.
