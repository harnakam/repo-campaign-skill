# Templates

Use these templates when reporting a campaign state or creating repo-local
records. Keep them concise and update them when reality changes.

## Campaign Status

```text
Current understanding:
- Major components:
- Components touched this episode:
- Important connections:
- Dangerous dependencies:
- Contracts that must not break:

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
- Completed:
- Not completed:
- Surprises:
- Carryover:

Experience:
- Lessons learned:
- What to inspect first next time:
```

## Episode Plan

```json
{
  "episode": 1,
  "title": "Map repository structure",
  "goal": "Create a usable map before code changes",
  "scope": ["build graph", "major components", "contracts"],
  "out_of_scope": ["semantic refactors", "dependency upgrades"],
  "entry_condition": ["repo is readable"],
  "exit_condition": [
    "repo-map.json exists",
    "risk zones are listed",
    "next episode is named"
  ],
  "allowed_mess": ["incomplete component ownership labels"],
  "not_allowed": ["repo-tracked production code edits"],
  "expected_failures": ["optional tools missing"],
  "verification": ["repo_scan.py", "dep_scan.py", "tool_check.py"]
}
```

## Result Record

```json
{
  "episode": 1,
  "completed": true,
  "done": ["repo map created", "dependency scan created"],
  "not_done": [],
  "surprises": ["Gradle build logic is in buildSrc"],
  "carryover": ["Map annotation processors in episode 2"],
  "verification": [
    {"command": "python scripts/repo_scan.py .", "result": "passed"}
  ]
}
```

## Compile Error Cluster

```json
{
  "error_cluster": "old Display API",
  "count": 184,
  "example": "cannot find symbol Display",
  "meaning": "old window dependency remains outside the backend boundary",
  "recommended_action": "move Display access behind WindowBackend"
}
```

## Context Pack

```text
# Repo Campaign Context Pack

Purpose:
- ...

Current episode:
- ...

Repo map:
- Build systems:
- Languages:
- Major components:
- Risk zones:

Relevant files:
- ...

Connections and contracts:
- ...

Known landmines:
- ...

Allowed mess:
- ...

Not allowed:
- ...

Next verification:
- ...
```
