"""Automated installer for OXOXOS Cocos Game Assets MCP.

This script is standard-library-only so an agent can run it before project
packages exist. It stores credentials outside the repository, installs the
runtime, backs up client configuration, migrates old server names, and keeps
client-specific failures isolated.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
SERVER = ROOT / "mcp" / "server.py"
SERVER_NAME = "oxoxos-cocos-game-assets"
LEGACY_SERVER_NAMES = ("cocos-game-assets", "qweapi-image-gen")


class InstallError(RuntimeError):
    """Actionable installation failure without secret values."""


def oxoxos_config_dir() -> Path:
    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "OXOXOS"


def credential_file() -> Path:
    override = os.getenv("OXOXOS_CREDENTIAL_FILE", "").strip()
    if override:
        return Path(override).expanduser()
    return oxoxos_config_dir() / "oxoxos-cocos-game-assets-mcp.env"


def legacy_credential_files() -> tuple[Path, ...]:
    return (oxoxos_config_dir() / "cocos-game-assets-mcp.env",)


def venv_python() -> Path:
    return ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def timestamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%d-%H%M%SZ")


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    destination = path.with_name(f"{path.name}.bak-{timestamp()}")
    shutil.copy2(path, destination)
    return destination


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.chmod(temporary, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(temporary, path)
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
    finally:
        temporary_path = Path(temporary)
        if temporary_path.exists():
            temporary_path.unlink()


def store_token(token: str) -> Path:
    value = token.strip()
    if not value:
        raise InstallError("令牌为空")
    if any(character in value for character in ("\n", "\r", "\x00")):
        raise InstallError("令牌包含非法换行或空字符")
    path = credential_file()
    backup(path)
    atomic_write(
        path,
        "# Managed by OXOXOS Cocos Game Assets MCP. Do not commit or share.\n"
        "OXOXOS_BASE_URL=https://api.oxoxos.com/v1\n"
        f"OXOXOS_API_KEY={value}\n"
        "OXOXOS_IMAGE_MODEL=\n"
        "OXOXOS_VISION_MODEL=\n"
        "OXOXOS_PROXY=\n",
    )
    return path


def migrate_existing_credential() -> tuple[Path, Path | None]:
    target = credential_file()
    if target.exists():
        return target, None
    for legacy in legacy_credential_files():
        if not legacy.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        legacy.replace(target)
        try:
            os.chmod(target, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        return target, legacy
    raise InstallError("未发现已保存的令牌；首次安装请使用 --token-stdin")


def read_token_from_stdin() -> str:
    if sys.stdin.isatty():
        import getpass

        return getpass.getpass("OXOXOS API token: ")
    return sys.stdin.readline().rstrip("\r\n")


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
        raise InstallError(
            f"命令失败（exit {result.returncode}）：{command[0]} {' '.join(command[1:3])}"
            + (f"；{detail}" if detail else "")
        )
    return result


def install_dependencies() -> dict[str, Any]:
    uv = shutil.which("uv")
    if uv:
        run([uv, "sync"])
        return {"method": "uv sync", "ok": True}

    if not venv_python().exists():
        run([sys.executable, "-m", "venv", str(ROOT / ".venv")])
    run([str(venv_python()), "-m", "pip", "install", "-e", str(ROOT)])
    return {"method": "venv + pip editable", "ok": True}


def server_definition() -> dict[str, Any]:
    return {
        "type": "stdio",
        "command": str(venv_python()),
        "args": [str(SERVER)],
        "enabled": True,
        "timeoutMs": 60000,
    }


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallError(f"无法读取 JSON 配置 {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InstallError(f"配置根节点不是对象: {path}")
    return value


def configure_zcode() -> dict[str, Any]:
    config_path = Path.home() / ".zcode" / "cli" / "config.json"
    config = load_json_object(config_path)
    backup_path = backup(config_path)
    mcp = config.setdefault("mcp", {})
    if not isinstance(mcp, dict):
        raise InstallError(f"ZCode mcp 配置不是对象: {config_path}")
    servers = mcp.setdefault("servers", {})
    if not isinstance(servers, dict):
        raise InstallError(f"ZCode mcp.servers 配置不是对象: {config_path}")
    removed = [name for name in LEGACY_SERVER_NAMES if servers.pop(name, None) is not None]
    servers[SERVER_NAME] = server_definition()
    atomic_write(config_path, json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    return {
        "client": "zcode",
        "configured": True,
        "config": str(config_path),
        "backup": str(backup_path) if backup_path else None,
        "removed_legacy_entries": removed,
    }


def remove_cli_entry(executable: str, name: str) -> bool:
    removed = False
    for _ in range(3):
        if run([executable, "mcp", "get", name], check=False).returncode != 0:
            break
        result = run([executable, "mcp", "remove", name], check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()[:500]
            raise InstallError(f"无法移除旧 MCP 条目 {name}: {detail}")
        removed = True
    return removed


def configure_cli(client: str, executable: str) -> dict[str, Any]:
    if client == "claude":
        config_path = Path.home() / ".claude.json"
        add_scope = ["--scope", "user"]
    else:
        config_path = Path.home() / ".codex" / "config.toml"
        add_scope = []
    backup_path = backup(config_path)
    removed = []
    try:
        for name in (SERVER_NAME, *LEGACY_SERVER_NAMES):
            if remove_cli_entry(executable, name):
                removed.append(name)
        run(
            [
                executable,
                "mcp",
                "add",
                *add_scope,
                SERVER_NAME,
                "--",
                str(venv_python()),
                str(SERVER),
            ]
        )
        if run([executable, "mcp", "get", SERVER_NAME], check=False).returncode != 0:
            raise InstallError(f"{client} 未能读取刚添加的 {SERVER_NAME} 条目")
    except InstallError:
        if backup_path:
            shutil.copy2(backup_path, config_path)
        raise
    return {
        "client": client,
        "configured": True,
        "config": str(config_path),
        "backup": str(backup_path) if backup_path else None,
        "removed_entries": removed,
    }


def detect_clients(requested: list[str]) -> list[tuple[str, str | None]]:
    if requested and "auto" not in requested:
        names = requested
    else:
        names = []
        if shutil.which("claude"):
            names.append("claude")
        if shutil.which("codex"):
            names.append("codex")
        if (Path.home() / ".zcode").exists():
            names.append("zcode")
    return [(name, shutil.which(name) if name != "zcode" else None) for name in dict.fromkeys(names)]


def plan(requested: list[str]) -> dict[str, Any]:
    clients = detect_clients(requested)
    return {
        "ok": True,
        "mode": "plan",
        "product": "OXOXOS Cocos Game Assets MCP",
        "repository": str(ROOT),
        "credential_file": str(credential_file()),
        "credential_will_be_private": True,
        "dependency_method": "uv sync" if shutil.which("uv") else "venv + pip editable",
        "server_name": SERVER_NAME,
        "server": server_definition(),
        "clients": [name for name, _ in clients],
        "legacy_server_names_to_remove": list(LEGACY_SERVER_NAMES),
        "persistent_changes": [
            "create or migrate the per-user OXOXOS credential file",
            "create or update one MCP entry per detected client",
            "back up existing client configuration before replacement",
        ],
        "paid_api_calls": False,
    }


def configure_token_only() -> dict[str, Any]:
    stored = store_token(read_token_from_stdin())
    return {
        "ok": True,
        "mode": "token-only",
        "credential_file": str(stored),
        "credential_updated": True,
        "next": (
            "restart the bundled MCP or start a fresh client session, then call "
            "list_models(force_refresh=true)"
        ),
    }


def apply(
    requested: list[str],
    token_stdin: bool,
    use_existing_token: bool,
    defer_token: bool,
) -> dict[str, Any]:
    report: dict[str, Any] = {"ok": False, "mode": "apply", "clients": []}
    if token_stdin:
        stored = store_token(read_token_from_stdin())
        report.update(credential_file=str(stored), credential_updated=True, token_configured=True)
    elif use_existing_token:
        stored, migrated_from = migrate_existing_credential()
        report.update(
            credential_file=str(stored),
            credential_updated=False,
            credential_migrated_from=str(migrated_from) if migrated_from else None,
            token_configured=True,
        )
    elif defer_token:
        report.update(
            credential_file=str(credential_file()),
            credential_updated=False,
            token_configured=False,
            token_setup_required=True,
        )
    else:
        raise InstallError(
            "自动安装需要 --defer-token、--token-stdin 或 --use-existing-token"
        )

    report["dependencies"] = install_dependencies()
    clients = detect_clients(requested)
    if not clients:
        raise InstallError("未检测到支持的客户端；请通过 --client 指定")
    for name, executable in clients:
        try:
            if name == "zcode":
                item = configure_zcode()
            elif executable:
                item = configure_cli(name, executable)
            else:
                raise InstallError("CLI executable not found")
        except (InstallError, OSError) as exc:
            item = {"client": name, "configured": False, "error": str(exc)}
        report["clients"].append(item)
    report["ok"] = all(item.get("configured") for item in report["clients"])
    report["next"] = (
        "ask the user to initialize OXOXOS API configuration, then run "
        "install.py --apply --token-stdin --client auto and verify.py --live-models"
        if defer_token
        else "run verify.py --live-models"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--token-only", action="store_true")
    parser.add_argument(
        "--client",
        action="append",
        choices=("auto", "claude", "codex", "zcode"),
        default=[],
    )
    token = parser.add_mutually_exclusive_group()
    token.add_argument("--defer-token", action="store_true")
    token.add_argument("--token-stdin", action="store_true")
    token.add_argument("--use-existing-token", action="store_true")
    args = parser.parse_args()

    try:
        if args.plan:
            result = plan(args.client)
        elif args.token_only:
            if not args.token_stdin:
                raise InstallError("--token-only 必须与 --token-stdin 一起使用")
            result = configure_token_only()
        else:
            result = apply(
                args.client,
                args.token_stdin,
                args.use_existing_token,
                args.defer_token,
            )
    except (InstallError, OSError, ValueError) as exc:
        result = {"ok": False, "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
