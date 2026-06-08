# Tooling

The scripts in this skill use only the Python standard library. Optional external
tools improve precision but must not be installed without user approval.

## Baseline Tools To Check

- Core: `git`, `rg`, `gh`.
- Java: `java`, `javac`, `jdeps`, `gradle`, `mvn`.
- Python: `python`, `pytest`, `ruff`, `mypy`, `pyright`.
- C/C++: `clang`, `clang-tidy`, `clangd`, `cmake`, `ninja`, `ctags`.
- Optional structure: `tree-sitter`.

## Missing Tool Policy

If a useful optional tool is missing:

1. Continue with degraded precision when possible.
2. Report the missing tool and why it matters.
3. Ask the user before installing it.
4. Prefer project-local tool wrappers or devcontainer instructions over global
   machine installs.
5. Do not install compiler toolchains, package managers, language servers, or
   tree-sitter grammars silently.

## Installation Prompt Pattern

Use a direct, specific approval request:

```text
`clang-tidy` is missing. It would let me classify C++ modernization warnings
without hand-inspecting every file. May I install or enable it using the repo's
documented toolchain instructions?
```

## Tool Confidence Levels

```json
{
  "tool": "rg",
  "status": "found",
  "confidence": "high",
  "reason": "available on PATH and version command succeeded"
}
```

```json
{
  "tool": "tree-sitter",
  "status": "missing",
  "confidence": "medium",
  "reason": "not found on PATH; script can continue with textual scan"
}
```

## Do Not Confuse Tool Presence With Runtime Health

For build wrappers, servers, CLIs, and native runtimes, version output only proves
the command launches. When the episode depends on real behavior, run a focused
runtime check.
