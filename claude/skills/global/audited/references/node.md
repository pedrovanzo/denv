# Node — npm audit

Run against the project's committed lockfile, not a re-resolved one:

```
npm audit --json
```

`--json` gives structured output (per-finding severity, advisory id/link, affected package, version range, dependency path, fix availability) — parse it rather than the human-readable table, since it needs to merge with Trivy's findings into one combined, reachability-sorted report (see `SKILL.md` step 5).

## Reachability heuristic

For each finding, check the dependency path npm audit reports:

- **Likely-inert**: the flagged package only appears in `devDependencies`, or its only path into the tree is through build-only tooling (a bundler, linter, test runner, codegen step) that never ships into the running container's final image. This project's own Level 9 scan hit exactly this — 5 of 6 findings lived in tooling never invoked at runtime.
- **Reachable candidate**: the flagged package is in `dependencies` (or a transitive dependency of one) and the container's runtime start command actually executes code that imports it. Confirm with a quick `grep`/search for the package name in the app's own source (`import`/`require`) before calling it reachable — being a runtime dependency in the manifest doesn't guarantee the specific vulnerable function is ever called, but an import is a reasonable proxy for "worth prioritizing" without doing full static call-graph analysis.

## Fix guidance to surface per finding

- If a semver-compatible patched version exists: surface the plain `npm audit fix` path.
- If only a breaking major-version fix exists: say so explicitly and flag it as a breaking change (`--force`) rather than recommending it silently — this is exactly the kind of fix that shouldn't be applied without the user knowing it might break something.
