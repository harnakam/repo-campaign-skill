#!/usr/bin/env python3
"""Check repo-campaign tool availability without installing anything."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOOLS = [
    {"name": "git", "category": "core", "version_args": ["--version"], "importance": "required"},
    {"name": "rg", "category": "core", "version_args": ["--version"], "importance": "strongly-recommended"},
    {"name": "gh", "category": "core", "version_args": ["--version"], "importance": "optional"},
    {"name": "java", "category": "java", "version_args": ["--version"], "importance": "optional"},
    {"name": "javac", "category": "java", "version_args": ["--version"], "importance": "optional"},
    {"name": "jdeps", "category": "java", "version_args": ["--version"], "importance": "optional"},
    {"name": "gradle", "category": "java", "version_args": ["--version"], "importance": "optional"},
    {"name": "mvn", "category": "java", "version_args": ["--version"], "importance": "optional"},
    {"name": "python", "category": "python", "version_args": ["--version"], "importance": "required"},
    {"name": "pytest", "category": "python", "version_args": ["--version"], "importance": "optional"},
    {"name": "ruff", "category": "python", "version_args": ["--version"], "importance": "optional"},
    {"name": "mypy", "category": "python", "version_args": ["--version"], "importance": "optional"},
    {"name": "pyright", "category": "python", "version_args": ["--version"], "importance": "optional"},
    {"name": "clang", "category": "c-cpp", "version_args": ["--version"], "importance": "optional"},
    {"name": "clang-tidy", "category": "c-cpp", "version_args": ["--version"], "importance": "optional"},
    {"name": "clangd", "category": "c-cpp", "version_args": ["--version"], "importance": "optional"},
    {"name": "cmake", "category": "c-cpp", "version_args": ["--version"], "importance": "optional"},
    {"name": "ninja", "category": "c-cpp", "version_args": ["--version"], "importance": "optional"},
    {"name": "ctags", "category": "c-cpp", "version_args": ["--version"], "importance": "optional"},
    {"name": "tree-sitter", "category": "structure", "version_args": ["--version"], "importance": "optional"},
]


def version_for(executable: str, version_args: list[str]) -> tuple[str | None, str | None]:
    try:
        completed = subprocess.run(
            [executable, *version_args],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, str(exc)
    output = (completed.stdout or completed.stderr).strip().splitlines()
    if completed.returncode != 0 and not output:
        return None, f"version command exited {completed.returncode}"
    return (output[0] if output else None), None


def check_tools() -> dict[str, Any]:
    tools: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    for spec in TOOLS:
        path = shutil.which(spec["name"])
        if path:
            version, error = version_for(path, spec["version_args"])
            status = "found" if error is None else "found-version-error"
            item = {
                "tool": spec["name"],
                "category": spec["category"],
                "importance": spec["importance"],
                "status": status,
                "path": path,
                "version": version,
                "error": error,
            }
        else:
            item = {
                "tool": spec["name"],
                "category": spec["category"],
                "importance": spec["importance"],
                "status": "missing",
                "path": None,
                "version": None,
                "error": None,
            }
            missing.append(
                {
                    "tool": spec["name"],
                    "category": spec["category"],
                    "importance": spec["importance"],
                    "install_policy": "ask-user-before-install",
                }
            )
        tools.append(item)

    return {
        "schema_version": 1,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "tools": tools,
        "missing_tools": missing,
        "install_policy": "Report missing tools and ask before installing. Continue with degraded precision when possible.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".", help="Repository root, included for command symmetry.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    _ = Path(args.repo).resolve()
    print(json.dumps(check_tools(), indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
