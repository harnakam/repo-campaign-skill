# Large-Scale Engineering Tradeoffs

This reference distills public Google engineering material into campaign rules.
Use it as a decision aid, not as a claim that this skill reproduces internal
Google tooling.

## Core Sources

- Google Engineering Practices: https://google.github.io/eng-practices/
- Google Code Review Guide: https://google.github.io/eng-practices/review/
- Software Engineering at Google: https://abseil.io/resources/swe-book
- Google Style Guides: https://google.github.io/styleguide/
- Google Java Style Guide: https://google.github.io/styleguide/javaguide.html
- Google Python Style Guide: https://google.github.io/styleguide/pyguide.html
- Google C++ Style Guide: https://google.github.io/styleguide/cppguide.html
- Starboard C/C++ Style Guide: https://developers.google.com/youtube/cobalt/docs/gen/starboard/doc/style
- Google Testing Blog, Test Sizes: https://testing.googleblog.com/2010/12/test-sizes.html
- Abseil Compatibility Guidelines: https://abseil.io/about/compatibility
- SEI CERT C/C++ Coding Standards: https://www.sei.cmu.edu/library/sei-cert-c-and-c-coding-standards/

## Campaign-Level Rules

- Optimize for long-term readers and maintainers. Prefer code that another
  engineer can find, understand, test, and safely change later.
- Review design, functionality, complexity, tests, naming, comments, style, and
  documentation as separate dimensions.
- Consistency is useful, especially for automation, but do not preserve a harmful
  legacy pattern merely because it exists nearby.
- Treat every public interface as a possible compatibility surface. At scale,
  users can depend on behavior that was not intentionally documented.
- Prefer live-at-head compatible migration paths: small reversible changes,
  feature flags when appropriate, and temporary fallback only with cleanup debt.
- Use data from builds, tests, logs, and error clusters. Do not rely on a clean
  mental model after the repo contradicts it.

## Test Sizing

Classify verification by blast radius:

```text
Small: one unit or narrow module; no network; no real external services.
Medium: integration boundary; localhost or filesystem/database allowed.
Large: end-to-end or system behavior; external systems or full runtime allowed.
```

Start with small checks for mechanical edits. Use medium checks for component
boundary changes. Use large checks when lifecycle, native resources, protocols,
or user-visible workflows are touched.

## Review Heuristics

- Ask whether the change improves overall code health, not only whether it works.
- Prefer smaller reviewable changes, but keep each episode vertically meaningful.
- Insist on tests for behavior and contract changes.
- Look for hidden global state, ownership transfer, cleanup order, error handling,
  and migration rollback.
- Comments should explain surprising intent, constraints, and contracts. Avoid
  comments that restate obvious code.

## Compatibility Heuristics

- Public headers, exported classes, CLI options, config keys, schemas, protocols,
  file formats, package names, and build targets can all be API.
- Anything named `internal`, `impl`, `detail`, `test`, `benchmark`, `sample`, or
  `example` is normally not public unless the repo documents otherwise.
- Do not change public behavior without an explicit migration plan, compatibility
  window, or user-approved breaking change.

## Style Heuristics

- Use repo-local formatters and linters before external taste.
- Names should carry intent across team boundaries. Short names are acceptable
  only in narrow scopes or established notation.
- Local consistency is a tie-breaker, not an excuse to copy dangerous patterns.
- Generated code should usually not be hand-edited.
