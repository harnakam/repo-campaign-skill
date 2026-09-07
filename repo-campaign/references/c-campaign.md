# C Campaign

Use this reference for C APIs, native backends, ABI-sensitive code, platform
ports, memory safety work, and C/C++ mixed boundaries.

## First Inspection Order

1. Build and platform matrix: Make, CMake, Meson, Bazel, configure scripts,
   toolchain files, target triples, compiler flags.
2. Public headers and ABI: exported headers, symbol visibility, calling
   conventions, struct layout, enum values, macros, version scripts.
3. Ownership and lifecycle: allocation/free pairs, handle ownership, callbacks,
   global state, thread lifecycle, signal handlers.
4. Platform layers: `win32`, `posix`, `linux`, `darwin`, `android`, embedded
   targets, architecture-specific code.
5. Generated and vendored code: protobuf, flex/bison, generated tables,
   third-party libraries.
6. Tests and analyzers: unit tests, integration tests, sanitizers, fuzzers,
   static analysis, ABI checks.

## Useful Tools

- Required/recommended: `git`, `rg`, compiler used by the repo.
- Build: `cmake`, `ninja`, `make`, `meson`, `bazel`.
- Analysis: `clang`, `clang-tidy`, `clangd`, `cppcheck`, sanitizers,
  `nm`, `objdump`, `readelf`, `dumpbin`, `ctags`.
- Security reference: SEI CERT C.

Ask before installing missing tools. Native toolchains can affect the whole
machine and must not be installed silently.

## Risk Zones

- Header changes can break source compatibility, binary compatibility, or both.
- Struct layout, enum values, macro behavior, and allocation ownership are
  contracts when exposed.
- C APIs often serve other languages. Keep C99-compatible public headers when
  the API is meant to cross language boundaries.
- Undefined behavior, integer overflow, lifetime bugs, and data races may not
  show up in ordinary tests.

## Review Checklist

- Track who allocates, owns, mutates, and frees every resource touched.
- Preserve public header order and macro contracts unless explicitly migrated.
- Use sanitizers or static analysis when memory/thread behavior changes.
- Keep platform-specific changes isolated behind the existing platform boundary.
- Prefer adapters over broad call-site rewrites until error clusters are known.
