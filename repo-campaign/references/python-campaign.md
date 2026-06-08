# Python Campaign

Use this reference for Python version moves, packaging changes, type-checking
rollouts, API refactors, CLI changes, and mixed Python/native repositories.

## First Inspection Order

1. Packaging: `pyproject.toml`, `setup.cfg`, `setup.py`, `requirements*.txt`,
   lockfiles, `tox.ini`, `noxfile.py`, `uv.lock`, `poetry.lock`.
2. Runtime version: `requires-python`, CI images, Dockerfiles, `.python-version`,
   tox envs, type checker target versions.
3. Import and package layout: namespace packages, editable installs, implicit
   namespace packages, generated packages, vendored code.
4. Public contracts: CLIs, module imports, documented functions/classes, config,
   schemas, plugin entry points, serialized formats.
5. Native boundaries: C extensions, CFFI, ctypes, pybind11, wheels, platform tags.
6. Tests and quality gates: pytest/unittest, ruff/flake8, mypy/pyright/pytype,
   coverage, golden files.

## Useful Tools

- Required/recommended: `git`, `rg`, `python`, repo test runner.
- Python: `pytest`, `ruff`, `mypy`, `pyright`, `tox`, `nox`, `pip`, `uv`.
- Packaging/native: `build`, `twine`, `auditwheel`, `delocate`, `cibuildwheel`.

Ask before installing missing tools. Do not rewrite package management strategy
unless the episode requires it.

## Risk Zones

- Import path changes can break users even when tests pass locally.
- Top-level module side effects can make tools and tests order-dependent.
- Mutable global state complicates migration comparison and test isolation.
- Type annotations should stabilize public APIs and risky internals first; do
  not force whole-repo annotation churn in a migration episode.
- Native wheels and compiled extensions have platform-specific failures.

## Review Checklist

- Keep public modules importable.
- Preserve CLI behavior and exit codes unless migration says otherwise.
- Avoid hidden network or filesystem dependency in small tests.
- Prefer explicit errors with actionable messages.
- Do not add broad formatting churn to a semantic refactor.
