# C++ Campaign

Use this reference for C++ migrations, library/API changes, native rendering or
runtime backends, template-heavy refactors, and ABI-sensitive work.

## First Inspection Order

1. Build graph: CMake, Bazel, Meson, Make, package managers, generated headers,
   compiler standard flags, sanitizer flags.
2. Public API/ABI: exported headers, namespaces, inline functions, templates,
   symbol visibility, shared library boundaries, plugin interfaces.
3. Ownership: RAII objects, raw pointer ownership, smart pointers, reference
   lifetimes, thread ownership, callbacks.
4. Lifecycle and global state: static initialization, singleton registries,
   thread locals, native handles, GPU resources, shutdown ordering.
5. Dependencies: Abseil, Boost, protobuf, fmt, spdlog, platform SDKs, graphics
   and audio libraries.
6. Tests and tooling: gtest/gmock, golden tests, sanitizers, clang-tidy,
   clang-format, ABI checkers, fuzzers.

## Useful Tools

- Required/recommended: `git`, `rg`, repo build tool.
- C++: `clang`, `clang++`, `clang-tidy`, `clangd`, `cmake`, `ninja`, `ctags`.
- Optional: include-what-you-use, sanitizers, libabigail, abi-compliance-checker,
  clang-query, tree-sitter.

Ask before installing missing tools. Prefer the compiler and standard library
already used by CI unless the episode is a toolchain migration.

## Risk Zones

- Header-only and template changes can create enormous hidden blast radius.
- Static initialization order and shutdown order are common runtime traps.
- ABI is not the same as API. Recompilation requirements must be explicit.
- Exception/RTTI policies, ownership conventions, and style rules differ by repo.
- Namespaces or files containing `internal`, `detail`, `impl`, `test`, or
  `benchmark` are usually not public unless documented otherwise.

## Review Checklist

- Optimize for the reader and for automation-friendly consistency.
- Avoid surprising ownership transfer; make ownership visible at call sites.
- Do not introduce new global state unless the repo already has a clear owner.
- Use mechanical rewrites only after compile errors are clustered.
- Keep temporary old/new implementations separated until their real differences
  are visible.
