---
name: repo-campaign
description: Coordinate production-grade work in very large repositories. Use when Codex needs to understand a huge codebase, plan or continue an episode-based migration, move Java/Python/C/C++ code to a new platform or language version, copy an old implementation into a new one before diverging, map components/connections/dependencies/state/lifecycle/contracts, classify compile or test failures into a worklist, or revise a multi-session refactoring plan from prior results.
---

# Repo Campaign

Use this skill to treat a repository as a running system: components, boundaries,
dependencies, state, contracts, history, and staged plans. Do not start with
function-level edits. Build a map first, then move one episode at a time.

## Operating Loop

1. Recall prior experience from `.codex/repo-campaign/experience.jsonl` when it exists.
2. Scan the repository before editing: structure, languages, build systems, tests, CI,
   generated code, third party code, entry points, public-contract candidates, and tools.
3. Map components before files. Identify owners, connections, dependencies, state,
   lifecycle, public contracts, internal boundaries, and risk zones.
4. Choose the current episode. State the goal, scope, exit conditions, allowed mess,
   forbidden breakage, expected failures, and verification.
5. Execute only the current episode. Prefer a vertical slice over disconnected cleanup.
6. Treat copy-and-diverge as a valid migration tactic when the old implementation is a
   safer seed than a premature abstraction.
7. Convert compile, test, lint, and runtime failures into clustered worklists.
8. Verify with the narrowest meaningful checks first, then broader checks when risk
   warrants it.
9. Record what happened, including surprises and revised next steps, in
   `.codex/repo-campaign/`.
10. Build a compact context pack for the next run.

## First Commands

Run these scripts from this skill directory as needed. They use only the Python
standard library and should not install external tools automatically.

```bash
python scripts/tool_check.py /path/to/repo
python scripts/repo_scan.py /path/to/repo
python scripts/dep_scan.py /path/to/repo
python scripts/campaign_state.py init /path/to/repo
python scripts/context_pack.py /path/to/repo --write
```

If a useful optional tool is missing, ask the user before installing it. Do not
silently install `tree-sitter`, compiler toolchains, package managers, or language
servers.

## What To Load

- Load `references/campaign-model.md` when creating or updating repo maps,
  episodes, debt records, experience records, or context packs.
- Load `references/google-engineering-flow.md` when making review, testing,
  compatibility, or "Google-scale" engineering tradeoffs.
- Load exactly one or more language references when relevant:
  `references/java-campaign.md`, `references/python-campaign.md`,
  `references/c-campaign.md`, `references/cpp-campaign.md`.
- Load `references/tooling.md` before requesting installation of optional tools.
- Load `references/templates.md` when producing the campaign status format.

## Campaign Rules

- Preserve public contracts unless the episode explicitly includes a migration plan.
- Distinguish generated, third-party, vendored, and handwritten code before editing.
- Locate state owners before changing lifecycle or threading behavior.
- Locate adapters, registries, callbacks, service locators, protocols, file formats,
  config keys, and resource identifiers before changing component boundaries.
- Avoid broad rewrites until error clusters show which mechanical change is safe.
- Do not abstract until old and new implementations have revealed their real
  differences.
- Keep temporary duplication tracked as cleanup debt with a cleanup episode.
- Never report an episode complete until the exit conditions and verification are
  attempted.

## Required Output Shape

When using the skill, report:

```text
Current understanding:
- Major components
- Components touched this episode
- Important connections
- Dangerous dependencies
- Contracts that must not break

Current episode:
Episode N: title

Exit conditions:
- ...

This episode will do:
- ...

This episode will not do:
- ...

Allowed temporary mess:
- ...

Result:
- Completed
- Not completed
- Surprises
- Carryover

Experience:
- Lessons learned
- What to inspect first next time
```
