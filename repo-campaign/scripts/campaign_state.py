#!/usr/bin/env python3
"""Create and update `.codex/repo-campaign` state in a target repository."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_DIR = Path(".codex") / "repo-campaign"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_root(repo: Path) -> Path:
    return repo.resolve() / STATE_DIR


def read_json_arg(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON: {exc}") from exc


def ensure_state(repo: Path) -> Path:
    root = state_root(repo)
    (root / "episodes").mkdir(parents=True, exist_ok=True)
    (root / "context-packs").mkdir(parents=True, exist_ok=True)
    for filename in ("experience.jsonl", "debt.jsonl", "verification-results.jsonl", "copy-diverge.jsonl"):
        path = root / filename
        if not path.exists():
            path.write_text("", encoding="utf-8")
    return root


def write_json(path: Path, data: dict[str, Any], overwrite: bool = True) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_init(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    if not repo.exists():
        raise SystemExit(f"repo does not exist: {repo}")
    root = ensure_state(repo)
    meta_path = root / "campaign.json"
    if not meta_path.exists() or args.force:
        write_json(
            meta_path,
            {
                "schema_version": 1,
                "created_at": now(),
                "repo_root": str(repo.resolve()),
                "state_dir": str(root),
                "current_episode": None,
                "policy": {
                    "experience_path": ".codex/repo-campaign/experience.jsonl",
                    "no_silent_tool_install": True,
                    "record_verification_results": True,
                    "track_cleanup_debt": True,
                    "track_copy_and_diverge": True,
                },
            },
        )
    return 0


def command_save_repo_map(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    root = ensure_state(repo)
    if args.input == "-":
        data = json.loads(sys.stdin.read())
    else:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    data.setdefault("schema_version", 1)
    data["saved_at"] = now()
    write_json(root / "repo-map.json", data)
    return 0


def next_episode_number(episodes_dir: Path) -> int:
    numbers: list[int] = []
    for path in episodes_dir.glob("episode-*.json"):
        try:
            numbers.append(int(path.stem.split("-")[1]))
        except (IndexError, ValueError):
            continue
    return (max(numbers) + 1) if numbers else 1


def command_new_episode(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    root = ensure_state(repo)
    episodes_dir = root / "episodes"
    episode_number = args.episode or next_episode_number(episodes_dir)
    record = {
        "schema_version": 1,
        "episode": episode_number,
        "title": args.title,
        "goal": args.goal,
        "created_at": now(),
        "scope": args.scope,
        "out_of_scope": args.out_of_scope,
        "entry_condition": args.entry_condition,
        "exit_condition": args.exit_condition,
        "allowed_mess": args.allowed_mess,
        "not_allowed": args.not_allowed,
        "expected_failures": args.expected_failures,
        "verification": args.verification,
        "status": "planned",
        "result": None,
    }
    path = episodes_dir / f"episode-{episode_number:03d}.json"
    write_json(path, record, overwrite=args.overwrite)
    meta_path = root / "campaign.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["current_episode"] = episode_number
        meta["updated_at"] = now()
        write_json(meta_path, meta)
    return 0


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def episode_path(root: Path, episode: int | None) -> Path | None:
    if episode is None:
        return None
    path = root / "episodes" / f"episode-{episode:03d}.json"
    return path if path.exists() else None


def command_record_verification(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    root = ensure_state(repo)
    record = {
        "schema_version": 1,
        "recorded_at": now(),
        "episode": args.episode,
        "command": args.command,
        "status": args.status,
        "exit_code": args.exit_code,
        "summary": args.summary,
        "artifact": args.artifact,
        "data": read_json_arg(args.data),
    }
    append_jsonl(root / "verification-results.jsonl", record)

    path = episode_path(root, args.episode)
    if path:
        episode = json.loads(path.read_text(encoding="utf-8"))
        episode.setdefault("verification_results", [])
        episode["verification_results"].append(record)
        episode["updated_at"] = now()
        write_json(path, episode)
    return 0


def command_append_experience(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    root = ensure_state(repo)
    record = {
        "schema_version": 1,
        "recorded_at": now(),
        "event": args.event,
        "task": args.task,
        "lesson": args.lesson,
        "episode": args.episode,
        "data": read_json_arg(args.data),
    }
    append_jsonl(root / "experience.jsonl", record)
    return 0


def command_append_debt(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    root = ensure_state(repo)
    record = {
        "schema_version": 1,
        "recorded_at": now(),
        "debt": args.debt,
        "reason": args.reason,
        "cleanup_after": args.cleanup_after,
        "owner_episode": args.owner_episode,
        "files": args.files,
        "data": read_json_arg(args.data),
    }
    append_jsonl(root / "debt.jsonl", record)
    return 0


def command_append_copy_diverge(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    root = ensure_state(repo)
    record = {
        "schema_version": 1,
        "recorded_at": now(),
        "copy_group": args.copy_group,
        "source": args.source,
        "copy": args.copy,
        "reason": args.reason,
        "allowed_scope": args.allowed_scope,
        "cleanup_condition": args.cleanup_condition,
        "cleanup_episode": args.cleanup_episode,
        "data": read_json_arg(args.data),
    }
    append_jsonl(root / "copy-diverge.jsonl", record)
    return 0


def command_status(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    root = state_root(repo)
    status = {
        "state_dir": str(root),
        "exists": root.exists(),
        "has_repo_map": (root / "repo-map.json").exists(),
        "episodes": [],
        "experience_records": 0,
        "debt_records": 0,
        "verification_result_records": 0,
        "copy_diverge_records": 0,
    }
    if root.exists():
        status["episodes"] = [path.name for path in sorted((root / "episodes").glob("episode-*.json"))]
        for key, filename in (
            ("experience_records", "experience.jsonl"),
            ("debt_records", "debt.jsonl"),
            ("verification_result_records", "verification-results.jsonl"),
            ("copy_diverge_records", "copy-diverge.jsonl"),
        ):
            path = root / filename
            if path.exists():
                status[key] = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


def add_list_arg(parser: argparse.ArgumentParser, name: str, help_text: str) -> None:
    parser.add_argument(f"--{name.replace('_', '-')}", dest=name, action="append", default=[], help=help_text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create campaign state directories.")
    init.add_argument("repo")
    init.add_argument("--force", action="store_true", help="Rewrite campaign metadata.")
    init.set_defaults(func=command_init)

    save_map = subparsers.add_parser("save-repo-map", help="Save a repo_scan JSON result.")
    save_map.add_argument("repo")
    save_map.add_argument("--input", required=True, help="Path to repo_scan JSON, or '-' for stdin.")
    save_map.set_defaults(func=command_save_repo_map)

    episode = subparsers.add_parser("new-episode", help="Create an episode plan record.")
    episode.add_argument("repo")
    episode.add_argument("--episode", type=int)
    episode.add_argument("--title", required=True)
    episode.add_argument("--goal", required=True)
    add_list_arg(episode, "scope", "In-scope item.")
    add_list_arg(episode, "out_of_scope", "Out-of-scope item.")
    add_list_arg(episode, "entry_condition", "Entry condition.")
    add_list_arg(episode, "exit_condition", "Exit condition.")
    add_list_arg(episode, "allowed_mess", "Allowed temporary mess.")
    add_list_arg(episode, "not_allowed", "Forbidden breakage.")
    add_list_arg(episode, "expected_failures", "Expected failure mode.")
    add_list_arg(episode, "verification", "Verification command or scenario.")
    episode.add_argument("--overwrite", action="store_true", help="Overwrite an existing episode file.")
    episode.set_defaults(func=command_new_episode)

    experience = subparsers.add_parser("append-experience", help="Append an experience record.")
    experience.add_argument("repo")
    experience.add_argument("--event", required=True)
    experience.add_argument("--task", required=True)
    experience.add_argument("--lesson", required=True)
    experience.add_argument("--episode", type=int)
    experience.add_argument("--data", help="Additional JSON object.")
    experience.set_defaults(func=command_append_experience)

    verification = subparsers.add_parser("record-verification", help="Record a verification result.")
    verification.add_argument("repo")
    verification.add_argument("--episode", type=int)
    verification.add_argument("--command", required=True)
    verification.add_argument("--status", required=True, choices=["passed", "failed", "skipped", "blocked", "timeout"])
    verification.add_argument("--exit-code", type=int)
    verification.add_argument("--summary", required=True)
    verification.add_argument("--artifact")
    verification.add_argument("--data", help="Additional JSON object.")
    verification.set_defaults(func=command_record_verification)

    debt = subparsers.add_parser("append-debt", help="Append a cleanup-debt record.")
    debt.add_argument("repo")
    debt.add_argument("--debt", required=True)
    debt.add_argument("--reason", required=True)
    debt.add_argument("--cleanup-after", required=True)
    debt.add_argument("--owner-episode", type=int)
    debt.add_argument("--files", action="append", default=[])
    debt.add_argument("--data", help="Additional JSON object.")
    debt.set_defaults(func=command_append_debt)

    copy_diverge = subparsers.add_parser("append-copy-diverge", help="Append a copy-and-diverge record.")
    copy_diverge.add_argument("repo")
    copy_diverge.add_argument("--copy-group", required=True)
    copy_diverge.add_argument("--source", required=True)
    copy_diverge.add_argument("--copy", required=True)
    copy_diverge.add_argument("--reason", required=True)
    copy_diverge.add_argument("--allowed-scope", action="append", default=[], required=True)
    copy_diverge.add_argument("--cleanup-condition", required=True)
    copy_diverge.add_argument("--cleanup-episode", type=int, required=True)
    copy_diverge.add_argument("--data", help="Additional JSON object.")
    copy_diverge.set_defaults(func=command_append_copy_diverge)

    status = subparsers.add_parser("status", help="Print campaign state status.")
    status.add_argument("repo")
    status.set_defaults(func=command_status)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
