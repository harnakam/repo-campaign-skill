#!/usr/bin/env python3
"""Build a compact Repo Campaign context pack from saved state."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_DIR = Path(".codex") / "repo-campaign"


def now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def state_root(repo: Path) -> Path:
    return repo.resolve() / STATE_DIR


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def latest_episode(root: Path) -> dict[str, Any] | None:
    episodes = sorted((root / "episodes").glob("episode-*.json"))
    if not episodes:
        return None
    return read_json(episodes[-1])


def read_jsonl_tail(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records[-limit:]


def bullet_list(values: list[Any], empty: str = "none recorded") -> str:
    if not values:
        return f"- {empty}"
    lines: list[str] = []
    for value in values:
        if isinstance(value, dict):
            label = value.get("path") or value.get("name") or value.get("title") or json.dumps(value, sort_keys=True)
            lines.append(f"- {label}")
        else:
            lines.append(f"- {value}")
    return "\n".join(lines)


def build_pack(repo: Path, purpose: str | None = None, tail: int = 5) -> str:
    root = state_root(repo)
    repo_map = read_json(root / "repo-map.json") or {}
    episode = latest_episode(root) or {}
    experience = read_jsonl_tail(root / "experience.jsonl", tail)
    debt = read_jsonl_tail(root / "debt.jsonl", tail)

    lines = [
        "# Repo Campaign Context Pack",
        "",
        "Purpose:",
        f"- {purpose or episode.get('goal') or 'Continue the current repo campaign safely.'}",
        "",
        "Current episode:",
        f"- Episode {episode.get('episode', 'unknown')}: {episode.get('title', 'not planned')}",
        f"- Goal: {episode.get('goal', 'not recorded')}",
        "",
        "Repo map:",
        f"- Repo kind: {repo_map.get('repo_kind', 'unknown')}",
        f"- Build systems: {', '.join(repo_map.get('build_systems', [])) or 'unknown'}",
        f"- Languages: {', '.join(key for key in repo_map.get('languages', {}).keys() if key != 'extensions') or 'unknown'}",
        "",
        "Major components:",
        bullet_list(repo_map.get("major_components", [])),
        "",
        "Risk zones:",
        bullet_list(repo_map.get("risk_zones", [])),
        "",
        "Important contracts and entrypoints:",
        bullet_list((repo_map.get("contract_candidates", [])[:20]) + [item.get("path") for item in repo_map.get("entrypoint_candidates", [])[:20] if isinstance(item, dict)]),
        "",
        "Allowed mess:",
        bullet_list(episode.get("allowed_mess", [])),
        "",
        "Not allowed:",
        bullet_list(episode.get("not_allowed", [])),
        "",
        "Exit conditions:",
        bullet_list(episode.get("exit_condition", [])),
        "",
        "Recent experience:",
        bullet_list([record.get("lesson") or record.get("event") for record in experience]),
        "",
        "Cleanup debt:",
        bullet_list([record.get("debt") for record in debt]),
        "",
        "Next verification:",
        bullet_list(episode.get("verification", [])),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--purpose", help="Override the purpose section.")
    parser.add_argument("--tail", type=int, default=5, help="Experience/debt records to include.")
    parser.add_argument("--write", action="store_true", help="Write into .codex/repo-campaign/context-packs.")
    args = parser.parse_args()

    repo = Path(args.repo)
    pack = build_pack(repo, purpose=args.purpose, tail=args.tail)
    if args.write:
        root = state_root(repo)
        out_dir = root / "context-packs"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"context-pack-{now_slug()}.md"
        out_path.write_text(pack, encoding="utf-8")
        print(str(out_path))
    else:
        print(pack)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
