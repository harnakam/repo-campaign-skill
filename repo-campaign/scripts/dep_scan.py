#!/usr/bin/env python3
"""Scan dependency and toolchain declarations in a repository."""

from __future__ import annotations

import argparse
import configparser
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback.
    tomllib = None  # type: ignore[assignment]


DEPENDENCY_LINE = re.compile(
    r"(?P<scope>api|implementation|compileOnly|runtimeOnly|testImplementation|"
    r"annotationProcessor|kapt|ksp|compile|testCompile)\s*(?:\(|\s)\s*"
    r"['\"](?P<coord>[^'\"]+)['\"]"
)
PLUGIN_LINE = re.compile(r"id\s*(?:\(|\s)\s*['\"](?P<id>[^'\"]+)['\"].*?version\s*['\"](?P<version>[^'\"]+)['\"]")
JAVA_VERSION_LINE = re.compile(r"(sourceCompatibility|targetCompatibility|languageVersion)\s*[= ]\s*([^;\n]+)")
CMAKE_FIND_PACKAGE = re.compile(r"find_package\s*\(\s*([A-Za-z0-9_:+.-]+)([^)]*)\)", re.IGNORECASE)
CMAKE_FETCH_CONTENT = re.compile(r"FetchContent_Declare\s*\(\s*([A-Za-z0-9_:+.-]+)", re.IGNORECASE)
CMAKE_STANDARD = re.compile(r"CMAKE_(C|CXX)_STANDARD\s+([0-9]+)", re.IGNORECASE)
BAZEL_DEP = re.compile(r"bazel_dep\s*\(\s*name\s*=\s*['\"]([^'\"]+)['\"].*?version\s*=\s*['\"]([^'\"]+)['\"]", re.DOTALL)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def text_or_none(elem: ElementTree.Element | None) -> str | None:
    if elem is None or elem.text is None:
        return None
    value = elem.text.strip()
    return value or None


def child_text(parent: ElementTree.Element, local_name: str) -> str | None:
    for child in parent:
        if child.tag.endswith(local_name):
            return text_or_none(child)
    return None


def scan_gradle(root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.gradle")) + sorted(root.rglob("*.gradle.kts")):
        if ".git" in path.parts or "build" in path.parts:
            continue
        text = read_text(path)
        for match in DEPENDENCY_LINE.finditer(text):
            coord = match.group("coord")
            parts = coord.split(":")
            results.append(
                {
                    "manager": "gradle",
                    "file": rel(path, root),
                    "scope": match.group("scope"),
                    "dependency": coord,
                    "group": parts[0] if len(parts) > 0 else None,
                    "name": parts[1] if len(parts) > 1 else None,
                    "version": parts[2] if len(parts) > 2 else None,
                }
            )
        for match in PLUGIN_LINE.finditer(text):
            results.append(
                {
                    "manager": "gradle-plugin",
                    "file": rel(path, root),
                    "scope": "plugin",
                    "dependency": match.group("id"),
                    "version": match.group("version"),
                }
            )
        for match in JAVA_VERSION_LINE.finditer(text):
            results.append(
                {
                    "manager": "gradle-toolchain",
                    "file": rel(path, root),
                    "scope": match.group(1),
                    "dependency": "java",
                    "version": match.group(2).strip().strip('"'),
                }
            )
    return results


def scan_maven(root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for pom in sorted(root.rglob("pom.xml")):
        if ".git" in pom.parts or "target" in pom.parts:
            continue
        try:
            tree = ElementTree.parse(pom)
        except ElementTree.ParseError:
            continue
        for dep in tree.iter():
            if not dep.tag.endswith("dependency") and not dep.tag.endswith("plugin"):
                continue
            group = child_text(dep, "groupId")
            artifact = child_text(dep, "artifactId")
            version = child_text(dep, "version")
            scope = child_text(dep, "scope") or ("plugin" if dep.tag.endswith("plugin") else "compile")
            if artifact:
                coord = ":".join(part for part in (group, artifact, version) if part)
                results.append(
                    {
                        "manager": "maven",
                        "file": rel(pom, root),
                        "scope": scope,
                        "dependency": coord,
                        "group": group,
                        "name": artifact,
                        "version": version,
                    }
                )
        for prop in tree.iter():
            if prop.tag.endswith("maven.compiler.source") or prop.tag.endswith("maven.compiler.target") or prop.tag.endswith("maven.compiler.release"):
                value = text_or_none(prop)
                if value:
                    results.append(
                        {
                            "manager": "maven-toolchain",
                            "file": rel(pom, root),
                            "scope": prop.tag.split("}")[-1],
                            "dependency": "java",
                            "version": value,
                        }
                    )
    return results


def scan_requirements(root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in sorted(root.glob("requirements*.txt")):
        for line in read_text(path).splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("-"):
                continue
            package = re.split(r"[<>=!~\[]", stripped, maxsplit=1)[0].strip()
            results.append(
                {
                    "manager": "pip-requirements",
                    "file": rel(path, root),
                    "scope": "runtime",
                    "dependency": stripped,
                    "name": package,
                    "version": None,
                }
            )
    return results


def scan_pyproject(root: Path) -> list[dict[str, Any]]:
    path = root / "pyproject.toml"
    if not path.exists() or tomllib is None:
        return []
    try:
        data = tomllib.loads(read_text(path))
    except Exception:
        return []
    results: list[dict[str, Any]] = []
    project = data.get("project", {})
    for dependency in project.get("dependencies", []) or []:
        results.append({"manager": "pyproject", "file": rel(path, root), "scope": "runtime", "dependency": dependency, "name": str(dependency).split()[0]})
    for group, dependencies in (project.get("optional-dependencies", {}) or {}).items():
        for dependency in dependencies or []:
            results.append({"manager": "pyproject", "file": rel(path, root), "scope": f"optional:{group}", "dependency": dependency, "name": str(dependency).split()[0]})
    for dependency in (data.get("build-system", {}) or {}).get("requires", []) or []:
        results.append({"manager": "pyproject", "file": rel(path, root), "scope": "build-system", "dependency": dependency, "name": str(dependency).split()[0]})
    poetry = (((data.get("tool", {}) or {}).get("poetry", {}) or {}).get("dependencies", {}) or {})
    for name, version in poetry.items():
        results.append({"manager": "poetry", "file": rel(path, root), "scope": "runtime", "dependency": name, "name": name, "version": version})
    requires_python = project.get("requires-python")
    if requires_python:
        results.append({"manager": "pyproject-toolchain", "file": rel(path, root), "scope": "requires-python", "dependency": "python", "version": requires_python})
    return results


def scan_setup_cfg(root: Path) -> list[dict[str, Any]]:
    path = root / "setup.cfg"
    if not path.exists():
        return []
    parser = configparser.ConfigParser()
    try:
        parser.read(path, encoding="utf-8")
    except configparser.Error:
        return []
    results: list[dict[str, Any]] = []
    if parser.has_option("options", "install_requires"):
        for line in parser.get("options", "install_requires").splitlines():
            dependency = line.strip()
            if dependency:
                results.append({"manager": "setup.cfg", "file": rel(path, root), "scope": "runtime", "dependency": dependency})
    return results


def scan_cmake(root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in sorted(root.rglob("CMakeLists.txt")):
        if ".git" in path.parts or "build" in path.parts:
            continue
        text = read_text(path)
        for match in CMAKE_FIND_PACKAGE.finditer(text):
            results.append({"manager": "cmake", "file": rel(path, root), "scope": "find_package", "dependency": match.group(1), "details": match.group(2).strip()})
        for match in CMAKE_FETCH_CONTENT.finditer(text):
            results.append({"manager": "cmake", "file": rel(path, root), "scope": "FetchContent", "dependency": match.group(1)})
        for match in CMAKE_STANDARD.finditer(text):
            results.append({"manager": "cmake-toolchain", "file": rel(path, root), "scope": f"{match.group(1).lower()}-standard", "dependency": match.group(1).lower(), "version": match.group(2)})
    return results


def scan_vcpkg(root: Path) -> list[dict[str, Any]]:
    path = root / "vcpkg.json"
    if not path.exists():
        return []
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError:
        return []
    results: list[dict[str, Any]] = []
    for dependency in data.get("dependencies", []) or []:
        if isinstance(dependency, str):
            name = dependency
            details: Any = None
        elif isinstance(dependency, dict):
            name = dependency.get("name")
            details = dependency
        else:
            continue
        if name:
            results.append({"manager": "vcpkg", "file": rel(path, root), "scope": "runtime", "dependency": name, "details": details})
    return results


def scan_conan(root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    conan_txt = root / "conanfile.txt"
    if conan_txt.exists():
        in_requires = False
        for line in read_text(conan_txt).splitlines():
            stripped = line.strip()
            if stripped.startswith("["):
                in_requires = stripped.lower() == "[requires]"
                continue
            if in_requires and stripped and not stripped.startswith("#"):
                results.append({"manager": "conan", "file": rel(conan_txt, root), "scope": "requires", "dependency": stripped})
    conan_py = root / "conanfile.py"
    if conan_py.exists():
        for match in re.finditer(r"requires\s*=\s*['\"]([^'\"]+)['\"]", read_text(conan_py)):
            results.append({"manager": "conan", "file": rel(conan_py, root), "scope": "requires", "dependency": match.group(1)})
    return results


def scan_bazel(root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    module = root / "MODULE.bazel"
    if module.exists():
        text = read_text(module)
        for match in BAZEL_DEP.finditer(text):
            results.append({"manager": "bazel-module", "file": rel(module, root), "scope": "bazel_dep", "dependency": match.group(1), "version": match.group(2)})
    return results


def scan_repo(root: Path) -> dict[str, Any]:
    root = root.resolve()
    dependencies: list[dict[str, Any]] = []
    for scanner in (
        scan_gradle,
        scan_maven,
        scan_pyproject,
        scan_requirements,
        scan_setup_cfg,
        scan_cmake,
        scan_vcpkg,
        scan_conan,
        scan_bazel,
    ):
        dependencies.extend(scanner(root))

    manager_counts: dict[str, int] = {}
    scope_counts: dict[str, int] = {}
    for item in dependencies:
        manager_counts[item["manager"]] = manager_counts.get(item["manager"], 0) + 1
        scope_counts[item["scope"]] = scope_counts.get(item["scope"], 0) + 1

    return {
        "schema_version": 1,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "dependency_count": len(dependencies),
        "manager_counts": dict(sorted(manager_counts.items())),
        "scope_counts": dict(sorted(scope_counts.items())),
        "dependencies": dependencies,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".", help="Repository root to scan.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    root = Path(args.repo)
    if not root.exists():
        parser.error(f"repo does not exist: {root}")
    print(json.dumps(scan_repo(root), indent=2 if args.pretty else None, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
