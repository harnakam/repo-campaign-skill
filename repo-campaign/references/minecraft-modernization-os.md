# Minecraft Modernization OS

Use this reference when the target is Minecraft 1.8.9, MCP/deobfuscated-era
Java, Forge-era clients, mod compatibility, LWJGL2 to LWJGL3, Java 25, modern
Gradle, or long-running game-client modernization. Treat the work as a
multi-year campaign with dozens or hundreds of episodes, not as a one-shot
"upgrade Java" task.

## Strategic Rule

Minecraft 1.8.9 modernization is an ecosystem migration. The target is not only
the game client. The target can include Forge, mods, resource packs, launchers,
native libraries, rendering/audio/input backends, mappings, build tooling, and
runtime observability.

Do not report "Java 25 support" or "LWJGL3 migration" complete unless the
relevant runtime path is exercised and the verification result is recorded.

## Modernization Modes

Identify the mode before planning runtime or dependency changes:

- `vanilla-modernization`: modernize the client while preserving vanilla behavior.
- `forge-compatible-modernization`: preserve Forge/mod compatibility as a major
  public contract.
- `performance-modernization`: prioritize runtime performance while preserving
  observable behavior.
- `toolchain-modernization`: modernize Java, Gradle, CI, and dependency
  management before runtime architecture.
- `backend-modernization`: migrate native/window/input/audio/render backend such
  as LWJGL2 to LWJGL3.
- `full-platform-migration`: allow larger architectural changes across
  toolchain, backend, runtime, and compatibility layers.

Do not assume these modes have the same constraints. Forge-compatible
modernization must treat mod loading, transformers, mappings, public hooks, and
binary compatibility as contracts unless explicitly relaxed. Backend
modernization must map lifecycle, native handles, render context, input polling,
audio devices, and platform-specific behavior before replacement. Toolchain
modernization must check Gradle, compiler target, annotation processors, bytecode
tools, CI images, launch wrappers, and test runtime before source-level edits.

## Internal Specialist Units

### 1. Architecture Recovery

Recover lost design intent before editing. MCP-era names such as
`func_71407_l` and `field_71439_g` are historical artifacts, not architecture.

Map at least:

- Renderer
- Window and display
- Input
- Audio
- World
- Entity
- GUI
- Network
- Save
- Resource loading
- Mod/plugin integration

Record both evidence and uncertainty. Use call sites, lifecycle position,
field ownership, side effects, later Minecraft versions, and Forge patches as
signals.

### 2. Semantic Rename

Restore meaning before large migrations. A rename campaign should produce a
mapping table, not scattered guesses.

```json
{
  "symbol": "func_71407_l",
  "proposed_name": "runTick",
  "confidence": 0.91,
  "evidence": [
    "called once per client loop",
    "updates world, GUI, input, and network",
    "matches later mapped name"
  ],
  "status": "accepted"
}
```

Prefer high-confidence names for public campaign vocabulary. Leave low-confidence
symbols as unknown rather than inventing misleading names.

### 3. Fork Archaeology

Study descendants to discover how later code solved the same problem.

Useful comparison chain:

```text
Minecraft 1.8.9
-> 1.12
-> 1.16
-> 1.20+
-> Forge/Fabric/Quilt/modernized forks where relevant
```

Look for lifecycle splits, rendering backend changes, input abstraction, resource
loading changes, networking updates, logging changes, and build-system evolution.
Record the fork/version used and the exact behavior learned from it.

### 4. Migration Cookbook

Repo scanning can find dependencies. Migration work needs dependency-specific
knowledge. Maintain cookbook entries for:

- LWJGL2 to LWJGL3
- Log4j
- Guava
- ASM
- Gradle
- JDK
- Netty
- OpenAL
- OpenGL
- Forge/mod loader surfaces

Each cookbook entry should include current usage, target API, known traps,
mechanical rewrites, runtime checks, and rollback/fallback strategy.

### 5. Mechanical Rewrite

Use mechanical rewrites for repeated API changes after the target boundary is
known. Do not manually edit hundreds of equivalent call sites.

Example:

```text
Keyboard.isKeyDown(KEY_X)
-> inputBackend.isKeyDown(Key.X)
```

Use AST-aware tooling when regex can cross semantic boundaries. If only textual
rewrite is available, constrain it to reviewed patterns and run compile/error
cluster checks after each batch.

### 6. Runtime Observation

The dangerous failures are often delayed:

```text
compile passes
-> client launches
-> world opens
-> render/tick/network/save runs
-> delayed crash or corruption appears
```

Instrument and record:

- Startup lifecycle
- Tick loop
- Render loop
- Input events
- Network connect/disconnect
- World load/unload
- Save/write paths
- Resource reload
- Mod loading
- Native handle creation/destruction

Runtime checks must write artifacts: logs, traces, screenshots, crash reports,
saved-world diffs, or structured event output.

### 7. Mod Compatibility

If Forge or mods are in scope, preserve the ecosystem surface. Identify:

- Forge hooks and patches
- Mod loader lifecycle
- Reflection-dependent names
- Access transformers
- Coremods/ASM transformers
- Public fields/methods used by mods
- Config and resource pack behavior
- Network and save compatibility

Treat mod compatibility as a public contract unless the user explicitly narrows
scope to a non-Forge standalone client.

## Episode Defaults

Recommended early campaign:

```text
Episode 1: repo and build map
Episode 2: architecture recovery for client lifecycle
Episode 3: semantic rename map for top lifecycle/render/input symbols
Episode 4: dependency and native backend map
Episode 5: fork archaeology for lifecycle and LWJGL evolution
Episode 6: copy-and-diverge window/input backend
Episode 7: mechanical rewrite pilot on one API family
Episode 8: runtime observation harness
Episode 9: mod compatibility contract map
```

Do not jump to Java 25 or LWJGL3 default switching until architecture recovery,
state ownership, lifecycle, and compatibility contracts are mapped.

## Copy-And-Diverge Bias

For Minecraft modernization, copy-and-diverge is often safer than direct
refactoring. Preserve a runnable old path while building a new path behind a
feature flag or isolated backend. Track every duplicate with source, copy,
reason, allowed scope, cleanup condition, and cleanup episode.
