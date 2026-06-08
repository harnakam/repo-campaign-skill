#!/usr/bin/env python3
"""Scan a repository into a coarse Repo Campaign map."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".gradle",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "cmake-build-debug",
    "cmake-build-release",
    "dist",
    "node_modules",
    "out",
    "target",
    "venv",
}

THIRD_PARTY_DIR_NAMES = {
    "3rdparty",
    "deps",
    "external",
    "third_party",
    "third-party",
    "vendor",
    "vendored",
}

GENERATED_DIR_HINTS = {
    "generated",
    "generated-sources",
    "autogen",
    "build/generated",
    "target/generated-sources",
}

LANGUAGE_EXTENSIONS = {
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".py": "python",
    ".pyi": "python",
    ".c": "c",
    ".h": "c/c++ header",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp header",
    ".hh": "cpp header",
    ".hxx": "cpp header",
    ".m": "objective-c",
    ".mm": "objective-c++",
    ".rs": "rust",
    ".go": "go",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".cs": "csharp",
    ".swift": "swift",
    ".scala": "scala",
}

BUILD_FILE_TO_SYSTEM = {
    "settings.gradle": "gradle",
    "settings.gradle.kts": "gradle",
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "gradlew": "gradle-wrapper",
    "gradlew.bat": "gradle-wrapper",
    "pom.xml": "maven",
    "pyproject.toml": "python-packaging",
    "setup.py": "python-packaging",
    "setup.cfg": "python-packaging",
    "requirements.txt": "python-requirements",
    "tox.ini": "tox",
    "noxfile.py": "nox",
    "CMakeLists.txt": "cmake",
    "Makefile": "make",
    "makefile": "make",
    "meson.build": "meson",
    "WORKSPACE": "bazel",
    "WORKSPACE.bazel": "bazel",
    "MODULE.bazel": "bazel",
    "BUILD": "bazel",
    "BUILD.bazel": "bazel",
    "conanfile.txt": "conan",
    "conanfile.py": "conan",
    "vcpkg.json": "vcpkg",
    "package.json": "node",
    "Cargo.toml": "cargo",
}

CI_PATH_HINTS = {
    ".github/workflows",
    ".gitlab-ci.yml",
    "azure-pipelines.yml",
    "Jenkinsfile",
    ".circleci/config.yml",
    "buildkite",
    ".buildkite",
}

CONTRACT_PATTERNS = [
    re.compile(r".*openapi.*\.(yaml|yml|json)$", re.IGNORECASE),
    re.compile(r".*swagger.*\.(yaml|yml|json)$", re.IGNORECASE),
    re.compile(r".*\.proto$", re.IGNORECASE),
    re.compile(r".*\.thrift$", re.IGNORECASE),
    re.compile(r".*\.graphqls?$", re.IGNORECASE),
    re.compile(r".*schema.*\.(json|yaml|yml|sql)$", re.IGNORECASE),
    re.compile(r".*migration.*\.(sql|py|java)$", re.IGNORECASE),
    re.compile(r".*api.*\.(h|hpp|java|py)$", re.IGNORECASE),
]

ENTRYPOINT_EXTENSIONS = {".java", ".py", ".c", ".cc", ".cpp", ".cxx", ".m", ".mm"}
MAX_TEXT_READ_BYTES = 80_000


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_third_party(path: Path) -> bool:
    return any(part.lower() in THIRD_PARTY_DIR_NAMES for part in path.parts)


def is_generated(path: Path) -> bool:
    lowered = path.as_posix().lower()
    parts = {part.lower() for part in path.parts}
    if parts.intersection({"generated", "generated-sources", "gen", "autogen"}):
        return True
    return any(hint in lowered for hint in {"build/generated", "target/generated-sources"})


def iter_repo_files(root: Path) -> tuple[list[Path], list[str], list[str]]:
    files: list[Path] = []
    third_party_dirs: list[str] = []
    generated_dirs: list[str] = []

    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        kept_dirs: list[str] = []
        for dirname in dirnames:
            child = current_path / dirname
            name = dirname.lower()
            child_rel = rel(child, root)
            if name in EXCLUDED_DIRS:
                continue
            if name in THIRD_PARTY_DIR_NAMES:
                third_party_dirs.append(child_rel)
                continue
            if is_generated(child):
                generated_dirs.append(child_rel)
                continue
            kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            path = current_path / filename
            if is_third_party(path):
                continue
            files.append(path)

    return files, sorted(set(third_party_dirs)), sorted(set(generated_dirs))


def detect_build_systems(root: Path, files: list[Path]) -> tuple[list[str], list[dict[str, str]]]:
    systems: set[str] = set()
    build_files: list[dict[str, str]] = []
    for path in files:
        system = BUILD_FILE_TO_SYSTEM.get(path.name)
        if not system:
            continue
        systems.add(system)
        build_files.append({"path": rel(path, root), "system": system})

    for requirements in root.glob("requirements*.txt"):
        if requirements.is_file():
            systems.add("python-requirements")
            build_files.append({"path": rel(requirements, root), "system": "python-requirements"})

    return sorted(systems), sorted(build_files, key=lambda item: item["path"])


def parse_gradle_modules(root: Path) -> list[dict[str, str]]:
    modules: list[dict[str, str]] = []
    for settings_name in ("settings.gradle", "settings.gradle.kts"):
        settings = root / settings_name
        if not settings.exists():
            continue
        text = read_text(settings)
        for match in re.finditer(r"include\s*(?:\(|\s)([^)\n]+)", text):
            include_blob = match.group(1)
            for raw in re.findall(r"['\"]([^'\"]+)['\"]", include_blob):
                module_path = raw.strip(":").replace(":", "/")
                if module_path:
                    modules.append({"name": raw, "path": module_path, "kind": "gradle"})
    return modules


def parse_maven_modules(root: Path) -> list[dict[str, str]]:
    pom = root / "pom.xml"
    if not pom.exists():
        return []
    modules: list[dict[str, str]] = []
    try:
        tree = ElementTree.parse(pom)
    except ElementTree.ParseError:
        return modules
    for elem in tree.iter():
        if elem.tag.endswith("module") and elem.text:
            value = elem.text.strip()
            if value:
                modules.append({"name": value, "path": value, "kind": "maven"})
    return modules


def detect_modules(root: Path, files: list[Path]) -> list[dict[str, str]]:
    modules = parse_gradle_modules(root) + parse_maven_modules(root)
    seen = {(item["kind"], item["path"]) for item in modules}
    for path in files:
        if path.name not in BUILD_FILE_TO_SYSTEM:
            continue
        parent = path.parent
        if parent == root:
            continue
        kind = BUILD_FILE_TO_SYSTEM[path.name]
        key = (kind, rel(parent, root))
        if key in seen:
            continue
        modules.append({"name": parent.name, "path": rel(parent, root), "kind": kind})
        seen.add(key)
    return sorted(modules, key=lambda item: (item["kind"], item["path"]))


def detect_languages(files: list[Path]) -> dict[str, dict[str, Any]]:
    counts: Counter[str] = Counter()
    extensions: Counter[str] = Counter()
    for path in files:
        suffix = path.suffix.lower()
        language = LANGUAGE_EXTENSIONS.get(suffix)
        if language:
            counts[language] += 1
            extensions[suffix] += 1
    return {
        language: {"files": count}
        for language, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    } | {"extensions": dict(sorted(extensions.items()))}


def detect_tests(root: Path, files: list[Path]) -> dict[str, Any]:
    test_files: list[str] = []
    test_dirs: set[str] = set()
    for path in files:
        parts = [part.lower() for part in path.relative_to(root).parts]
        name = path.name.lower()
        if any(part in {"test", "tests", "__tests__", "src/test"} for part in parts):
            test_dirs.add(parts[0])
        if (
            name.startswith("test_")
            or name.endswith("_test.py")
            or name.endswith("test.java")
            or name.endswith("tests.java")
            or name.endswith("_test.cc")
            or name.endswith("_test.cpp")
            or name.endswith("test.cpp")
            or name.endswith("test.c")
        ):
            test_files.append(rel(path, root))
    config_files = [
        rel(path, root)
        for path in files
        if path.name in {"pytest.ini", "tox.ini", "noxfile.py", "junit-platform.properties"}
    ]
    return {
        "test_dirs": sorted(test_dirs),
        "test_file_count": len(test_files),
        "test_file_examples": sorted(test_files)[:30],
        "config_files": sorted(config_files),
    }


def detect_ci(root: Path) -> list[str]:
    results: list[str] = []
    for hint in CI_PATH_HINTS:
        path = root / hint
        if path.is_dir():
            for child in sorted(path.glob("*")):
                if child.is_file():
                    results.append(rel(child, root))
        elif path.exists():
            results.append(rel(path, root))
    return sorted(set(results))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:MAX_TEXT_READ_BYTES]
    except OSError:
        return ""


def detect_entrypoints(root: Path, files: list[Path]) -> list[dict[str, str]]:
    entrypoints: list[dict[str, str]] = []
    for path in files:
        if path.suffix.lower() not in ENTRYPOINT_EXTENSIONS:
            continue
        text = read_text(path)
        if not text:
            continue
        kind = None
        if path.suffix.lower() == ".java" and "public static void main" in text:
            kind = "java-main"
        elif path.suffix.lower() == ".py" and "__main__" in text:
            kind = "python-main"
        elif path.suffix.lower() in {".c", ".cc", ".cpp", ".cxx", ".m", ".mm"}:
            if re.search(r"\b(int|void)\s+main\s*\(", text):
                kind = "native-main"
        if kind:
            entrypoints.append({"path": rel(path, root), "kind": kind})
    return sorted(entrypoints, key=lambda item: item["path"])[:100]


def detect_contracts(root: Path, files: list[Path]) -> list[str]:
    contracts: list[str] = []
    for path in files:
        relative = rel(path, root)
        if any(pattern.match(relative) for pattern in CONTRACT_PATTERNS):
            contracts.append(relative)
    return sorted(contracts)[:200]


def detect_platform_specific(root: Path, files: list[Path]) -> list[str]:
    platform_terms = {
        "win",
        "win32",
        "windows",
        "linux",
        "darwin",
        "mac",
        "macos",
        "posix",
        "unix",
        "android",
        "ios",
        "x86",
        "x64",
        "arm",
        "aarch64",
    }
    results: set[str] = set()
    for path in files:
        parts = [part.lower() for part in path.relative_to(root).parts]
        if any(part in platform_terms for part in parts):
            results.add(rel(path.parent, root) if path.parent != root else rel(path, root))
    return sorted(results)[:200]


def detect_major_components(root: Path, files: list[Path]) -> list[str]:
    counts: Counter[str] = Counter()
    for path in files:
        parts = path.relative_to(root).parts
        if not parts:
            continue
        if len(parts) == 1:
            continue
        top = parts[0]
        if top.lower() in EXCLUDED_DIRS or top.startswith("."):
            continue
        counts[top] += 1
    return [name for name, _ in counts.most_common(30)]


def infer_risk_zones(scan: dict[str, Any]) -> list[str]:
    risks: set[str] = set()
    languages = scan.get("languages", {})
    if any(language in languages for language in ("c", "cpp", "c/c++ header", "cpp header")):
        risks.add("native code")
    if scan.get("contract_candidates"):
        risks.add("public contracts")
    if scan.get("generated_code"):
        risks.add("generated code")
    if scan.get("third_party"):
        risks.add("third party or vendored code")
    build_systems = set(scan.get("build_systems", []))
    if "gradle" in build_systems or "maven" in build_systems:
        risks.add("Java build and toolchain")
    if "cmake" in build_systems or "make" in build_systems or "meson" in build_systems:
        risks.add("native build toolchain")
    for component in scan.get("major_components", []):
        lowered = component.lower()
        if lowered in {"network", "protocol", "serialization", "save", "storage", "db", "database"}:
            risks.add(lowered)
        if lowered in {"render", "renderer", "graphics", "window", "input", "audio"}:
            risks.add("runtime lifecycle")
    return sorted(risks)


def infer_repo_kind(languages: dict[str, Any], build_systems: list[str]) -> str:
    language_names = [key for key in languages.keys() if key != "extensions"]
    if not language_names and not build_systems:
        return "empty-or-unclassified"
    dominant = "-".join(language_names[:4]) if language_names else "unknown-language"
    build = "-".join(build_systems[:3]) if build_systems else "no-build-system-detected"
    return f"{dominant}-{build}"


def scan_repo(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files, third_party_dirs, generated_dirs = iter_repo_files(root)
    build_systems, build_files = detect_build_systems(root, files)
    languages = detect_languages(files)
    scan: dict[str, Any] = {
        "schema_version": 1,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "repo_kind": infer_repo_kind(languages, build_systems),
        "file_count_scanned": len(files),
        "build_systems": build_systems,
        "build_files": build_files,
        "languages": languages,
        "major_components": detect_major_components(root, files),
        "modules": detect_modules(root, files),
        "test_structure": detect_tests(root, files),
        "ci": detect_ci(root),
        "generated_code": generated_dirs,
        "third_party": third_party_dirs,
        "entrypoint_candidates": detect_entrypoints(root, files),
        "platform_specific_code": detect_platform_specific(root, files),
        "contract_candidates": detect_contracts(root, files),
    }
    scan["risk_zones"] = infer_risk_zones(scan)
    return scan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".", help="Repository root to scan.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    root = Path(args.repo)
    if not root.exists():
        parser.error(f"repo does not exist: {root}")
    scan = scan_repo(root)
    print(json.dumps(scan, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
