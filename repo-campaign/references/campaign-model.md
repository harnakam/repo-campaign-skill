# Campaign Model

Use these records as the stable vocabulary for a repo campaign. Store repo-local
campaign state under `.codex/repo-campaign/`.

## Evidence And Source Of Truth

Do not treat inferred architecture as fact. Every map entry should carry an
evidence level:

- `observed`: directly found in code, build files, tests, CI, runtime logs, or
  generated scan output.
- `inferred`: strongly suggested by naming, call paths, package structure, or
  repeated usage.
- `assumed`: a working assumption used to proceed, not yet verified.
- `unknown`: explicitly not known yet.

When sources disagree, prefer this order:

1. runtime behavior and traces
2. test and verification results
3. build, CI, and toolchain configuration
4. current implementation
5. recent commit history
6. documentation
7. comments
8. naming conventions

Old comments and stale documentation must not override observed behavior.

## Campaign Artifacts

Maintain campaign state under:

```text
.codex/repo-campaign/
  campaign.json
  repo-map.json
  components.json
  connections.json
  dependencies.json
  lifecycle.json
  contracts.json
  episodes.jsonl
  debt.jsonl
  failures.jsonl
  experience.jsonl
  context-pack.md
```

Use these artifacts as the campaign's working memory. `campaign.json` records the
goal, mode, constraints, current episode, and global non-negotiables.
`repo-map.json` records structure, languages, build systems, tests, CI, generated
code, vendored/third-party code, entry points, and tools. `components.json`
records components, declared or inferred owners, responsibilities, evidence
levels, and risks. `connections.json` records adapters, registries, callbacks,
service locators, event paths, protocols, file formats, config keys, resource
identifiers, and boundaries. `dependencies.json` records internal/external
dependencies, build plugins, annotation processors, native libraries, runtime
dependencies, and test dependencies. `lifecycle.json` records startup,
initialization, load, tick, render, save, shutdown, test setup, and deploy order.
`contracts.json` records public APIs, save formats, protocols, plugin/mod APIs,
CLI behavior, config formats, serialization formats, and compatibility
constraints. `episodes.jsonl` records each episode plan, result, carryover, and
plan changes. `debt.jsonl` records temporary duplication, migration scaffolding,
feature flags, adapters, compatibility layers, TODOs, fallback paths, and cleanup
episodes. `failures.jsonl` records clustered compile, test, lint, runtime,
performance, platform, compatibility, and verification failures. `experience.jsonl`
records reusable lessons, failed assumptions, successful strategies, repo-specific
conventions, landmines, and next inspection priorities. `context-pack.md` is the
compact context for the next run.

The scripts may also maintain supporting indexes such as
`verification-results.jsonl` and `copy-diverge.jsonl` so checks and intentional
duplication can be queried across episodes. These are derived campaign memory,
not a substitute for recording episode results and cleanup debt.

## Repo Map

```json
{
  "repo_root": "/repo",
  "repo_kind": "mixed-java-python-cpp",
  "build_systems": ["gradle", "cmake"],
  "languages": {"java": {"files": 1200}, "cpp": {"files": 320}},
  "major_components": ["client", "renderer", "network"],
  "declared_owner_files": ["CODEOWNERS"],
  "inferred_owners": [{"path": "renderer", "owner": "alice@example.com"}],
  "modules": [{"name": "client", "path": "client", "kind": "gradle"}],
  "risk_zones": ["native backend", "serialization", "render loop"],
  "evidence_level": "observed"
}
```

Repo maps are reconnaissance, not truth. Refresh them when build files,
entrypoints, public APIs, or generated code layout changes.

## Component

```json
{
  "component": "Rendering",
  "owns": ["GameRenderer", "ShaderManager"],
  "declared_or_inferred_owners": ["alice@example.com", "graphics-team"],
  "depends_on": ["Window", "ResourceManager", "OpenGL"],
  "used_by": ["ClientRuntime"],
  "boundary": "client-runtime",
  "generated": false,
  "evidence_level": "inferred"
}
```

Map components by responsibility before listing files. A directory can contain
multiple components; a component can span directories. Owners can be declared in
files such as `CODEOWNERS`, inferred from commit history, or inferred from
module/package boundaries. Mark inference confidence instead of pretending the
repo has a formal ownership model.

## Connection

```json
{
  "from": "Input",
  "to": "PlayerController",
  "connection": "InputEvent",
  "contract": "pressed/released state is consumed during tick",
  "risk": "medium",
  "migration_relevance": "high",
  "evidence_level": "observed"
}
```

Prioritize interfaces, adapters, callbacks, registries, service locators, file
formats, config keys, resource identifiers, serialization, protocols, and public
methods. These fail more often than isolated implementation details.

## Dependency

```json
{
  "dependency": "org.lwjgl:lwjgl",
  "current_version": "2.x",
  "used_by": ["Window", "Input", "Audio"],
  "scope": "runtime",
  "migration_risk": "critical",
  "evidence_level": "observed"
}
```

Include build plugins, annotation processors, runtime/native libraries, CI images,
test dependencies, language versions, package managers, and generated-code tools.

## State Ownership

```json
{
  "state": "windowHandle",
  "owned_by": "WindowBackend",
  "created_during": "startup",
  "used_by": ["Renderer", "Input"],
  "destroyed_during": "shutdown",
  "risk": "high",
  "evidence_level": "inferred"
}
```

Find singletons, globals, caches, registries, thread locals, handles, sockets,
file locks, GPU resources, and persistent state before changing lifecycle.

## Lifecycle

```json
{
  "lifecycle": [
    "Main.main",
    "Client.create",
    "Window.create",
    "Renderer.init",
    "GameLoop.run",
    "tick",
    "render",
    "shutdown"
  ],
  "evidence_level": "observed"
}
```

Compile success is not lifecycle success. Confirm initialization order, ownership
transfer, cleanup order, test setup, and shutdown.

## Contract

```json
{
  "contract": "save_format",
  "owner": "SaveSystem",
  "compatibility_requirement": "must remain backward compatible",
  "migration_policy": "do not change without explicit migration",
  "evidence_level": "observed"
}
```

Contracts include public APIs, headers, CLI flags, config keys, save formats,
network protocols, database schemas, plugin/mod APIs, generated schema files, and
observable behavior relied on by users.

## Episode

```json
{
  "episode": 3,
  "title": "Create WindowBackend boundary",
  "goal": "Contain direct LWJGL access inside WindowBackend",
  "entry_condition": ["LWJGL access sites are classified"],
  "exit_condition": [
    "WindowBackend interface exists",
    "Old implementation compiles through the interface",
    "No public API change",
    "Verification results are recorded"
  ],
  "allowed_mess": ["temporary adapter", "backend-internal duplication"],
  "not_allowed": ["save format changes", "network protocol changes"],
  "risk_budget": [
    "compile may be red only inside the migration branch",
    "old backend must remain runnable"
  ],
  "checkpoint": "branch before backend extraction"
}
```

Episodes are allowed to end incomplete. If reality invalidates the plan, revise
the next episode instead of pretending the original plan still fits.

## Episode Result

```json
{
  "episode": 3,
  "completed": false,
  "done": ["WindowBackend interface exists"],
  "not_done": ["Input lifecycle still reaches old Display directly"],
  "verification_results": [
    {
      "command": "./gradlew :client:compileJava",
      "status": "failed",
      "exit_code": 1,
      "summary": "184 Display API errors remain",
      "artifact": ".codex/repo-campaign/error-clusters/display-api.json"
    }
  ],
  "surprises": ["Input initialization owns more window state than expected"],
  "carryover": ["Separate window/input lifecycle before backend switch"],
  "plan_changes_for_next_episode": [
    "Replace planned input migration with window/input lifecycle separation"
  ]
}
```

An attempted check that is not recorded does not count as campaign knowledge.
Record failures, skipped checks, timeouts, and environment blockers with the same
care as passing checks.

## Copy And Diverge

```json
{
  "copy_group": "window-backend-migration",
  "source": "Lwjgl2WindowBackend",
  "copy": "Lwjgl3WindowBackend",
  "reason": "Preserve the working LWJGL2 path while developing GLFW lifecycle",
  "allowed_scope": ["backend internals", "adapter glue"],
  "cleanup_condition": "LWJGL3 backend is default and fallback removal is approved",
  "cleanup_episode": 9
}
```

Do not treat duplication as failure during migrations. Temporary duplication is
allowed when it preserves a working old path, creates a safer new path, or
reveals real differences before abstraction. Every intentional duplicate must
have source, copy, reason, allowed scope, cleanup condition, and cleanup episode.

## Failure Cluster

```json
{
  "failure_type": "lifecycle",
  "count": 184,
  "examples": ["Display access before GLFW initialization"],
  "affected_components": ["Window", "Input"],
  "suspected_cause": "Input still depends on old Display lifecycle",
  "evidence_level": "observed",
  "proposed_action": "Split window/input lifecycle before backend replacement",
  "fix_kind": "architectural"
}
```

Classify failures using:

- `mechanical`
- `architectural`
- `lifecycle`
- `state-ownership`
- `contract-break`
- `dependency-toolchain`
- `platform-specific`
- `test-only`
- `performance`
- `unknown`

For Minecraft-like clients, also recognize `render-context`, `input-polling`,
`audio-device`, `native-loading`, `resource-path`, `mapping-obfuscation`,
`mixin-transformer`, `forge-mod-compatibility`, and
`save-world-compatibility`.

Each cluster should include count, examples, affected components, suspected
cause, evidence level, proposed action, and whether the fix is mechanical or
architectural.

## Risk Budget And Checkpoints

Each episode must state what may break and what may not. Useful examples:

- compile may be red only inside the migration branch.
- runtime launch must remain possible through the old path.
- old backend must remain runnable.
- save format, network protocol, and public mod/plugin API must not change.
- feature flags may be introduced.
- temporary duplication is allowed only inside the migration package.
- generated, vendored, and third-party code must not be edited.
- performance regressions may be measured but not accepted silently.

Before risky changes, create or identify a rollback checkpoint. After an episode
satisfies its exit conditions, record the checkpoint and verification result. If
verification regresses outside the episode's risk budget, do not keep stacking
changes. Revert, split the episode, or create a new investigation episode.

## Cleanup Debt

```json
{
  "debt": "temporary duplicate backend",
  "reason": "migration parallel run",
  "cleanup_after": "new backend becomes default",
  "owner_episode": 9,
  "files": ["Lwjgl2WindowBackend.java", "Lwjgl3WindowBackend.java"]
}
```

Temporary mess is permitted only when tracked with a cleanup condition.

## Experience

```json
{
  "event": "migration_failure",
  "task": "LWJGL2 to LWJGL3",
  "failure": {
    "type": "runtime_order_bug",
    "symptom": "window handle accessed before GLFW initialization"
  },
  "lesson": {
    "rule": "Map window/input/render lifecycle before moving input",
    "confidence": 0.82
  },
  "next_time": {
    "recommended_first_step": "Build lifecycle map for window/input/render"
  }
}
```

Experience records should change future exploration order. Do not store generic
status logs unless they preserve a reusable decision.

## Episode Completion

An episode is complete only when:

- exit conditions were checked.
- verification was attempted.
- verification results were recorded.
- failures were clustered or explicitly deferred.
- risk budget was not exceeded or plan revision was recorded.
- temporary duplication or scaffolding was recorded as cleanup debt.
- experience records were updated.
- `context-pack.md` was updated.
