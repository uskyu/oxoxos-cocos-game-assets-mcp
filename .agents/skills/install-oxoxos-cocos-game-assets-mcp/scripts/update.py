"""Safe, explicit updater for OXOXOS Cocos Game Assets MCP.

The updater never handles token values. Credentials live outside the repository
and remain untouched while source, dependencies, and client launch paths update.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]


class UpdateError(RuntimeError):
    """Actionable update failure."""


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()[:800]
        raise UpdateError(
            f"命令失败（exit {result.returncode}）：{command[0]} {' '.join(command[1:3])}"
            + (f"；{detail}" if detail else "")
        )
    return result


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], check=check)


def timestamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%d-%H%M%SZ")


def current_ref() -> str:
    result = git("rev-parse", "--abbrev-ref", "HEAD")
    return result.stdout.strip()


def current_commit() -> str:
    result = git("rev-parse", "HEAD")
    return result.stdout.strip()


def worktree_status() -> list[str]:
    result = git("status", "--porcelain")
    return [line for line in result.stdout.splitlines() if line.strip()]


def plan() -> dict[str, Any]:
    branch = current_ref()
    commit = current_commit()
    status = worktree_status()
    return {
        "ok": True,
        "mode": "plan",
        "repository": str(ROOT),
        "branch": branch,
        "commit": commit,
        "worktree_clean": not status,
        "changed_files": len(status),
        "actions_after_approval": [
            "fetch the configured remote",
            "create a local backup tag for the current commit",
            "fast-forward or update from the selected remote branch",
            "sync the locked Python environment",
            "run offline tests, lint, build, and MCP initialization checks",
            "leave the per-user OXOXOS credential file and client config backups untouched",
        ],
        "paid_api_calls": False,
        "rollback": "git reset --hard <backup-tag> only after reviewing the reported backup tag",
    }


def apply(remote: str, branch: str | None) -> dict[str, Any]:
    status = worktree_status()
    if status:
        raise UpdateError(
            "工作区有未提交改动，更新已停止。请先提交、暂存或备份这些改动；不会自动覆盖它们。"
        )
    active_branch = branch or current_ref()
    before = current_commit()
    backup_tag = f"oxoxos-pre-update-{timestamp()}"
    git("tag", backup_tag, before)
    try:
        git("fetch", remote)
        git("pull", "--ff-only", remote, active_branch)
        uv = "uv"
        run([uv, "sync"])
        report = {
            "ok": True,
            "mode": "apply",
            "before": before,
            "after": current_commit(),
            "branch": active_branch,
            "backup_tag": backup_tag,
            "remote": remote,
            "paid_api_calls": False,
            "next": "run verify.py and review the result",
        }
        return report
    except (UpdateError, OSError) as exc:
        return {
            "ok": False,
            "mode": "apply",
            "before": before,
            "backup_tag": backup_tag,
            "error": str(exc),
            "rollback": f"git reset --hard {backup_tag} (only after review)",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="")
    args = parser.parse_args()
    try:
        result = plan() if args.plan else apply(args.remote, args.branch or None)
    except (UpdateError, OSError) as exc:
        result = {"ok": False, "mode": "plan" if args.plan else "apply", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
