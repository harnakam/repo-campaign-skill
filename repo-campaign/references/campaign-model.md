# Campaign Model

Use these records as the stable vocabulary for a repo campaign. Store repo-local
campaign state under `.codex/repo-campaign/`.

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
  "risk_zones": ["native backend", "serialization", "render loop"]
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
  "generated": false
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
  "migration_relevance": "high"
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
  "migration_risk": "critical"
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
  "risk": "high"
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
  ]
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
  "migration_policy": "do not change without explicit migration"
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
  "not_allowed": ["save format changes", "network protocol changes"]
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
  "carryover": ["Separate window/input lifecycle before backend switch"]
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
