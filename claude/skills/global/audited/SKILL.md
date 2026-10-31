---
name: audited
description: Rebuild a project's Docker image and scan it with Trivy (plus npm audit when the stack is Node), then triage combined findings by whether the vulnerable code is actually reachable at runtime — not just by severity label. Warning — this rebuilds the image and runs a full scan, can take several minutes. Use when the user asks to audit dependencies, scan for vulnerabilities, or check the image for CVEs. Does not auto-trigger.
disable-model-invocation: true
---

# Audited

Combine an image-level scan (Trivy) with a manifest-level scan (npm audit, when applicable) into one triaged report — reachable findings first, not severity alone. Assumes the project already has a Docker setup; if it doesn't, say so and suggest the `dockerize` skill by name as a prerequisite, don't chain into it.

## 1. Check for a prior run

Look for `.audited-last-run.json` in the project root.

- **Exists**: read it, report elapsed time since the last run, which image tag was scanned, and whether the Node step ran that time — before doing anything else.
- **Doesn't exist**: this is either the first run, or the user runs standalone one-off audits without persisting state. Ask explicitly: persist a last-run marker across sessions from now on, or keep this a standalone run with nothing left behind? Don't assume either way.
  - If persisting: create `.audited-last-run.json` now (populated at the end of this run, see step 7), and add it to `.gitignore` if not already covered by an existing pattern — create `.gitignore` if the project doesn't have one. Do **not** add it to `.dockerignore` — that file governs build-context inclusion, not git tracking, and doesn't apply here.
  - If standalone: don't create the marker at all, skip step 7 entirely.

Also check for `.audited-risk-acceptance.json` if present (see step 6). For any finding in the new scan that also appears in that file: check whether its re-check trigger/expiry has passed. If it has, flag it back to reachable-tier attention in the report instead of silently re-suppressing it — an accepted risk isn't accepted forever.

## 2. Rebuild the image

Always rebuild fresh before scanning — an existing/stale image gives a stale result, and accuracy matters more than the time cost here. Use the project's existing Dockerfile/Compose config to build the target image tag.

## 3. Scan with Trivy

```
trivy image <tag>
```

Ask once, briefly, whether to include misconfiguration and secret scanning (`trivy image --scanners vuln,misconfig,secret <tag>`) alongside the default vulnerability scan — not a full tiered prompt, just a yes/no, since Trivy's own scope here is simple.

## 4. Scan with npm audit — Node stacks only

If `package.json` exists in the project root, read `references/node.md` from this skill's directory and follow it to run npm audit and fold its findings into the same combined set. If there's no `package.json` (or equivalent for another ecosystem), skip this step entirely — don't load the reference file for a stack it doesn't apply to.

## 5. Triage by reachability, then report

For every finding, decide reachable vs. likely-inert before sorting:

- **Trivy OS/package findings**: is the flagged binary or library actually invoked by the app at runtime — referenced in the entrypoint/CMD, shelled out to by app code, part of the actual request path? If it's just sitting in the base image unused, it's likely-inert.
- **npm audit findings** (from step 4, using `references/node.md`'s heuristic): a flagged package only in `devDependencies` or pulled in by build-only tooling never shipped to the running container is likely-inert; a flagged package in `dependencies` and actually `import`ed/`require`d from reachable source is reachable.

Report combined findings **reachable-first**, severity as the secondary sort within each group — never severity alone, that's the whole point of this skill. State the reachability call and why for each finding, don't just label it silently.

Don't write findings to a file by default — report in the conversation. Only write a disk artifact if the user asks for one for this specific run.

## 6. Record risk acceptance for likely-inert findings

An accepted risk that only ever lived in a conversation message isn't accepted anywhere — it gets silently re-litigated (or silently forgotten) next run. Industry practice (CISA VEX, Snyk's `.snyk` policy, Dependabot dismissal, OWASP Dependency-Track) always writes the decision down with a reason, and a trigger to revisit it.

For every finding labeled likely-inert in step 5, ask the user once whether to persist a suppression record for it — don't assume. If yes, write (or append to) `.audited-risk-acceptance.json` in the project root, per finding:

- CVE/advisory id and package
- the reachability justification, using VEX-style justification codes where they fit (`vulnerable_code_not_present`, `vulnerable_code_not_in_execute_path`, `dev_dependency_not_shipped`, etc.)
- date accepted
- a re-check trigger — either an explicit expiry date, or a condition like "re-check when `<package>` publishes a new release"

If the user chose to persist the last-run marker in step 1, add this file to `.gitignore` too, same reasoning as the marker.

## 7. Update the marker

Skip this step entirely if step 1 ended in "standalone" (no marker file). Otherwise, write `.audited-last-run.json` with the current timestamp, the image tag just scanned, and whether the Node step ran — metadata only, never the findings themselves.
