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
JSON_ARTIFACTS = (
    "repo-map.json",
    "components.json",
    "connections.json",
    "dependencies.json",
    "lifecycle.json",
    "contracts.json",
)
JSONL_ARTIFACTS = (
    "episodes.jsonl",
    "debt.jsonl",
    "failures.jsonl",
    "experience.jsonl",
    "verification-results.jsonl",
    "copy-diverge.jsonl",
)
EVIDENCE_LEVELS = ("observed", "inferred", "assumed", "unknown")
FAILURE_TYPES = (
    "mechanical",
    "architectural",
    "lifecycle",
    "state-ownership",
    "contract-break",
    "dependency-toolchain",
    "platform-specific",
    "test-only",
    "performance",
    "unknown",
    "render-context",
    "input-polling",
    "audio-device",
    "native-loading",
    "resource-path",
    "mapping-obfuscation",
    "mixin-transformer",
    "forge-mod-compatibility",
    "save-world-compatibility",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_root(repo: Path) -> Path:
    return repo.resolve() / STATE_DIR


def read_json_arg(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise argparse.ArgumentTypeError("additional JSON must be an object")
    return data


def empty_artifact(name: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "artifact": name,
        "updated_at": now(),
        "records": [],
        "evidence_level": "unknown",
    }


def write_json(path: Path, data: dict[str, Any], overwrite: bool = True) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_campaign(repo: Path, root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "created_at": now(),
        "repo_root": str(repo.resolve()),
        "state_dir": str(root),
        "goal": None,
        "mode": None,
        "constraints": [],
        "global_non_negotiables": [],
        "current_episode": None,
        "policy": {
            "artifact_schema": "fixed",
            "experience_path": ".codex/repo-campaign/experience.jsonl",
            "no_silent_tool_install": True,
            "record_verification_results": True,
            "track_cleanup_debt": True,
            "track_copy_and_diverge": True,
            "record_failure_clusters": True,
        },
    }


def ensure_state(repo: Path) -> Path:
    root = state_root(repo)
    root.mkdir(parents=True, exist_ok=True)

    campaign_path = root / "campaign.json"
    if not campaign_path.exists():
        write_json(campaign_path, default_campaign(repo, root))

    for filename in JSON_ARTIFACTS:
        path = root / filename
        if not path.exists():
            write_json(path, empty_artifact(filename))

    for filename in JSONL_ARTIFACTS:
        path = root / filename
        if not path.exists():
            path.write_text("", encoding="utf-8")

    context_pack = root / "context-pack.md"
    if not context_pack.exists():
        context_pack.write_text("# Repo Campaign Context Pack\n\nNo context pack has been generated yet.\n", encoding="utf-8")

    return root


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def next_episode_number(root: Path) -> int:
    numbers = [record.get("episode") for record in read_jsonl(root / "episodes.jsonl")]
    numeric = [number for number in numbers if isinstance(number, int)]
    return (max(numeric) + 1) if numeric else 1


def update_episode(root: Path, episode_number: int | None, mutator: Any) -> None:
    if episode_number is None:
        return
    path = root / "episodes.jsonl"
    records = read_jsonl(path)
    changed = False
    for record in records:
        if record.get("episode") == episode_number:
            mutator(record)
            record["updated_at"] = now()
            changed = True
            break
    if changed:
        write_jsonl(path, records)


def command_init(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    if not repo.exists():
        raise SystemExit(f"repo does not exist: {repo}")
    root = ensure_state(repo)
    meta_path = root / "campaign.json"
    if args.force:
        campaign = default_campaign(repo, root)
    else:
        campaign = json.loads(meta_path.read_text(encoding="utf-8"))
    if args.goal is not None:
        campaign["goal"] = args.goal
    if args.mode is not None:
        campaign["mode"] = args.mode
    if args.constraint:
        campaign["constraints"] = args.constraint
    if args.non_negotiable:
        campaign["global_non_negotiables"] = args.non_negotiable
    campaign["updated_at"] = now()
    write_json(meta_path, campaign)
    return 0


def command_save_repo_map(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    root = ensure_state(repo)
    if args.input == "-":
        data = json.loads(sys.stdin.read())
    else:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    data.setdefault("schema_version", 1)
    data.setdefault("evidence_level", "observed")
    data["saved_at"] = now()
    write_json(root / "repo-map.json", data)
    return 0


def command_save_artifact(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    root = ensure_state(repo)
    filename = f"{args.artifact}.json"
    if filename not in JSON_ARTIFACTS:
        raise SystemExit(f"unsupported artifact: {args.artifact}")
    if args.input == "-":
        data = json.loads(sys.stdin.read())
    else:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    data.setdefault("schema_version", 1)
    data.setdefault("artifact", filename)
    data.setdefault("evidence_level", args.evidence_level)
    data["updated_at"] = now()
    write_json(root / filename, data)
    return 0


def command_new_episode(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    root = ensure_state(repo)
    episode_number = args.episode or next_episode_number(root)
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
        "risk_budget": args.risk_budget,
        "checkpoint": args.checkpoint,
        "expected_failures": args.expected_failures,
        "verification": args.verification,
        "verification_results": [],
        "failure_clusters": [],
        "plan_changes_for_next_episode": [],
        "status": "planned",
        "result": None,
    }
    records = read_jsonl(root / "episodes.jsonl")
    if any(item.get("episode") == episode_number for item in records) and not args.overwrite:
        raise SystemExit(f"episode already exists: {episode_number}")
    records = [item for item in records if item.get("episode") != episode_number]
    records.append(record)
    records.sort(key=lambda item: item.get("episode", 0))
    write_jsonl(root / "episodes.jsonl", records)

    meta_path = root / "campaign.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["current_episode"] = episode_number
    meta["updated_at"] = now()
    write_json(meta_path, meta)
    return 0


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
        "evidence_level": "observed",
        "data": read_json_arg(args.data),
    }
    append_jsonl(root / "verification-results.jsonl", record)

    def mutate(episode: dict[str, Any]) -> None:
        episode.setdefault("verification_results", []).append(record)

    update_episode(root, args.episode, mutate)
    return 0


def command_append_failure(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    root = ensure_state(repo)
    record = {
        "schema_version": 1,
        "recorded_at": now(),
        "episode": args.episode,
        "failure_type": args.failure_type,
        "count": args.count,
        "examples": args.example,
        "affected_components": args.affected_component,
        "suspected_cause": args.suspected_cause,
        "evidence_level": args.evidence_level,
        "proposed_action": args.proposed_action,
        "fix_kind": args.fix_kind,
        "data": read_json_arg(args.data),
    }
    append_jsonl(root / "failures.jsonl", record)

    def mutate(episode: dict[str, Any]) -> None:
        episode.setdefault("failure_clusters", []).append(record)

    update_episode(root, args.episode, mutate)
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
        "what_to_inspect_first_next_time": args.inspect_first,
        "plan_changes_for_next_episode": args.plan_change,
        "episode": args.episode,
        "data": read_json_arg(args.data),
    }
    append_jsonl(root / "experience.jsonl", record)

    def mutate(episode: dict[str, Any]) -> None:
        episode.setdefault("plan_changes_for_next_episode", []).extend(args.plan_change)

    update_episode(root, args.episode, mutate)
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
        "json_artifacts": {},
        "jsonl_records": {},
        "has_context_pack": (root / "context-pack.md").exists(),
    }
    if root.exists():
        for filename in ("campaign.json", *JSON_ARTIFACTS):
            status["json_artifacts"][filename] = (root / filename).exists()
        for filename in JSONL_ARTIFACTS:
            path = root / filename
            status["jsonl_records"][filename] = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()) if path.exists() else 0
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


def add_list_arg(parser: argparse.ArgumentParser, name: str, help_text: str, required: bool = False) -> None:
    parser.add_argument(f"--{name.replace('_', '-')}", dest=name, action="append", default=[], required=required, help=help_text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create campaign state artifacts.")
    init.add_argument("repo")
    init.add_argument("--goal")
    init.add_argument("--mode")
    add_list_arg(init, "constraint", "Campaign constraint.")
    add_list_arg(init, "non_negotiable", "Global non-negotiable.")
    init.add_argument("--force", action="store_true", help="Rewrite campaign metadata.")
    init.set_defaults(func=command_init)

    save_map = subparsers.add_parser("save-repo-map", help="Save a repo_scan JSON result.")
    save_map.add_argument("repo")
    save_map.add_argument("--input", required=True, help="Path to repo_scan JSON, or '-' for stdin.")
    save_map.set_defaults(func=command_save_repo_map)

    save_artifact = subparsers.add_parser("save-artifact", help="Save one campaign artifact JSON.")
    save_artifact.add_argument("repo")
    save_artifact.add_argument("--artifact", required=True, choices=["components", "connections", "dependencies", "lifecycle", "contracts"])
    save_artifact.add_argument("--input", required=True, help="Path to JSON, or '-' for stdin.")
    save_artifact.add_argument("--evidence-level", default="observed", choices=EVIDENCE_LEVELS)
    save_artifact.set_defaults(func=command_save_artifact)

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
    add_list_arg(episode, "risk_budget", "Risk budget item.")
    episode.add_argument("--checkpoint", help="Rollback checkpoint or branch.")
    add_list_arg(episode, "expected_failures", "Expected failure mode.")
    add_list_arg(episode, "verification", "Verification command or scenario.")
    episode.add_argument("--overwrite", action="store_true", help="Overwrite an existing episode record.")
    episode.set_defaults(func=command_new_episode)

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

    failure = subparsers.add_parser("append-failure", help="Append a clustered failure record.")
    failure.add_argument("repo")
    failure.add_argument("--episode", type=int)
    failure.add_argument("--failure-type", required=True, choices=FAILURE_TYPES)
    failure.add_argument("--count", type=int, required=True)
    add_list_arg(failure, "example", "Example failure text.", required=True)
    add_list_arg(failure, "affected_component", "Affected component.")
    failure.add_argument("--suspected-cause", required=True)
    failure.add_argument("--evidence-level", required=True, choices=EVIDENCE_LEVELS)
    failure.add_argument("--proposed-action", required=True)
    failure.add_argument("--fix-kind", required=True, choices=["mechanical", "architectural", "mixed", "unknown"])
    failure.add_argument("--data", help="Additional JSON object.")
    failure.set_defaults(func=command_append_failure)

    experience = subparsers.add_parser("append-experience", help="Append an experience record.")
    experience.add_argument("repo")
    experience.add_argument("--event", required=True)
    experience.add_argument("--task", required=True)
    experience.add_argument("--lesson", required=True)
    add_list_arg(experience, "inspect_first", "What to inspect first next time.")
    add_list_arg(experience, "plan_change", "Plan change for the next episode.")
    experience.add_argument("--episode", type=int)
    experience.add_argument("--data", help="Additional JSON object.")
    experience.set_defaults(func=command_append_experience)

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
    add_list_arg(copy_diverge, "allowed_scope", "Allowed scope for intentional duplication.", required=True)
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
