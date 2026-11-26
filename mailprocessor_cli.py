"""Headless CLI for MailProcessor (dual-use human & LLM entrypoint)."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import config as cfg_module
import snapshot_export
import store_readiness
import tool_manager as tm_module
from tool_manager import TOOL_DEFINITIONS, ToolManager

_CLI_SUBCOMMANDS = frozenset(
    {"status", "scan", "snapshot", "register", "unregister", "launch", "store-readiness"}
)
_CLI_FLAGS = frozenset({"-h", "--help", "-V", "--version", "--json"})


def should_dispatch_cli(argv: Sequence[str] | None = None) -> bool:
    """Return True if argv targets the headless CLI rather than GUI or --self-test."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args == ["--self-test"]:
        return False
    first = args[0]
    return first in _CLI_SUBCOMMANDS or first in _CLI_FLAGS


def _emit(payload: dict, as_json: bool, text_lines: list[str]) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("\n".join(text_lines))


def _tool_status_payload(tm: ToolManager, tool_id: str) -> dict:
    meta = TOOL_DEFINITIONS[tool_id]
    tool_cfg = tm.cfg.tools.get(tool_id)
    enabled = bool(tool_cfg.enabled) if tool_cfg else False
    valid = tm.is_path_valid(tool_id)
    if not enabled or not tool_cfg or not tool_cfg.path or not tool_cfg.main_script:
        state = "not_configured"
    elif valid:
        state = "available"
    else:
        state = "missing"
    return {
        "id": tool_id,
        "display_name": meta["display_name"],
        "enabled": enabled,
        "valid": valid,
        "status": state,
        "version": tm.tool_version(tool_id),
        "installed_by": tool_cfg.installed_by if tool_cfg and tool_cfg.installed_by else None,
        "main_script": tool_cfg.main_script if tool_cfg and tool_cfg.main_script else None,
        "path_hint": snapshot_export._redact_path_hint(tool_cfg.path if tool_cfg else None),
    }


def _cmd_status(args: argparse.Namespace) -> int:
    cfg = cfg_module.load()
    tm = ToolManager(cfg)
    tools = [_tool_status_payload(tm, tid) for tid in TOOL_DEFINITIONS]
    payload = {
        "ok": True,
        "app": "MailProcessor",
        "version": snapshot_export._read_app_version(),
        "config_exists": cfg_module.CONFIG_FILE.is_file(),
        "config_file": snapshot_export._redact_path_hint(str(cfg_module.CONFIG_FILE)),
        "language": cfg.language,
        "first_run": cfg.first_run,
        "start_with_windows": cfg.start_with_windows,
        "tools": tools,
    }
    lines = [
        f"MailProcessor {payload['version'] or '0.1.0'} (language={cfg.language}, "
        f"first_run={cfg.first_run}, start_with_windows={cfg.start_with_windows})",
    ]
    for item in tools:
        ver = f" {item['version']}" if item["version"] else ""
        hint = f" [{item['path_hint']}]" if item["path_hint"] else ""
        lines.append(f"- {item['id']}: {item['status']}{ver}{hint}")
    _emit(payload, args.json, lines)
    return 0


def _cmd_scan(args: argparse.Namespace) -> int:
    cfg = cfg_module.load()
    tm = ToolManager(cfg)
    results = tm.scan()
    added: list[str] = []
    if args.apply:
        added = tm.apply_scan_results(results)
        if added:
            cfg_module.save(cfg)

    detected = {
        tid: {
            "found": found is not None,
            "path_hint": snapshot_export._redact_path_hint(found[0]) if found else None,
            "main_script": found[1] if found else None,
        }
        for tid, found in results.items()
    }
    payload = {
        "ok": True,
        "dry_run": not args.apply,
        "applied": bool(args.apply),
        "updated_tools": added,
        "detected": detected,
    }
    lines = [
        f"Scan complete ({'applied' if args.apply else 'dry-run'}; updated={len(added)}):"
    ]
    for tid, info in detected.items():
        if info["found"]:
            lines.append(f"- {tid}: found ({info['main_script']}) [{info['path_hint']}]")
        else:
            lines.append(f"- {tid}: not found")
    _emit(payload, args.json, lines)
    return 0


def _cmd_snapshot(args: argparse.Namespace) -> int:
    cfg = cfg_module.load()
    if args.out:
        try:
            written = snapshot_export.write_snapshot(args.out, cfg)
        except Exception as exc:
            payload = {"ok": False, "error": str(exc)}
            _emit(payload, args.json, [f"Snapshot error: {exc}"])
            return 2
        payload = {
            "ok": True,
            "schema": snapshot_export.SNAPSHOT_SCHEMA,
            "output_path": str(written),
        }
        _emit(payload, args.json, [f"Snapshot written: {written}"])
        return 0

    payload = snapshot_export.build_snapshot_payload(cfg)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def _cmd_register(args: argparse.Namespace) -> int:
    if args.tool_id not in TOOL_DEFINITIONS:
        payload = {
            "ok": False,
            "error": f"Unknown tool_id: {args.tool_id}",
            "valid_tool_ids": sorted(TOOL_DEFINITIONS),
        }
        _emit(payload, args.json, [payload["error"]])
        return 2

    cfg = cfg_module.load()
    tm = ToolManager(cfg)
    ok = tm.register_from_script_path(args.tool_id, args.path, installed_by=args.installed_by)
    if not ok:
        payload = {
            "ok": False,
            "tool_id": args.tool_id,
            "error": f"No valid launch script found for {args.tool_id} at {args.path}",
        }
        _emit(payload, args.json, [payload["error"]])
        return 2

    cfg_module.save(cfg)
    payload = {
        "ok": True,
        "tool": _tool_status_payload(tm, args.tool_id),
    }
    _emit(
        payload,
        args.json,
        [f"Registered {args.tool_id}: {payload['tool']['main_script']} [{payload['tool']['path_hint']}]"],
    )
    return 0


def _cmd_unregister(args: argparse.Namespace) -> int:
    if args.tool_id not in TOOL_DEFINITIONS:
        payload = {
            "ok": False,
            "error": f"Unknown tool_id: {args.tool_id}",
            "valid_tool_ids": sorted(TOOL_DEFINITIONS),
        }
        _emit(payload, args.json, [payload["error"]])
        return 2

    if not args.yes and not args.dry_run:
        payload = {
            "ok": False,
            "tool_id": args.tool_id,
            "error": "Refusing to unregister without --yes (pass --dry-run to preview)",
        }
        _emit(payload, args.json, [payload["error"]])
        return 2

    cfg = cfg_module.load()
    tm = ToolManager(cfg)
    had_entry = bool(cfg.tools.get(args.tool_id) and cfg.tools[args.tool_id].enabled)
    if args.yes and not args.dry_run:
        tm.unregister(args.tool_id)
        cfg_module.save(cfg)

    payload = {
        "ok": True,
        "tool_id": args.tool_id,
        "dry_run": bool(args.dry_run or not args.yes),
        "was_enabled": had_entry,
    }
    mode = "dry-run" if payload["dry_run"] else "unregistered"
    _emit(payload, args.json, [f"{args.tool_id}: {mode} (was_enabled={had_entry})"])
    return 0


def _cmd_launch(args: argparse.Namespace) -> int:
    if args.tool_id not in TOOL_DEFINITIONS:
        payload = {
            "ok": False,
            "error": f"Unknown tool_id: {args.tool_id}",
            "valid_tool_ids": sorted(TOOL_DEFINITIONS),
        }
        _emit(payload, args.json, [payload["error"]])
        return 2

    cfg = cfg_module.load()
    tm = ToolManager(cfg)
    if args.dry_run:
        valid = tm.is_path_valid(args.tool_id)
        interpreter = tm_module._python_interpreter()
        ok = bool(valid and interpreter)
        tool_cfg = cfg.tools.get(args.tool_id)
        payload = {
            "ok": ok,
            "dry_run": True,
            "tool_id": args.tool_id,
            "valid": valid,
            "interpreter_found": bool(interpreter),
            "main_script": tool_cfg.main_script if tool_cfg else None,
            "path_hint": snapshot_export._redact_path_hint(tool_cfg.path if tool_cfg else None),
        }
        if not valid:
            payload["error"] = "Tool not configured or launch script missing"
        elif not interpreter:
            payload["error"] = "Python interpreter not found"
        _emit(
            payload,
            args.json,
            [
                f"Dry-run launch {args.tool_id}: ok={ok}, valid={valid}, "
                f"interpreter_found={bool(interpreter)}"
            ],
        )
        return 0 if ok else 2

    err = tm.launch(args.tool_id)
    if err:
        payload = {"ok": False, "tool_id": args.tool_id, "error": err}
        _emit(payload, args.json, [f"Launch failed ({args.tool_id}): {err}"])
        return 1
    payload = {"ok": True, "tool_id": args.tool_id, "launched": True}
    _emit(payload, args.json, [f"Launched {args.tool_id}"])
    return 0


def _cmd_store_readiness(args: argparse.Namespace) -> int:
    sr_args: list[str] = []
    if args.project_root is not None:
        sr_args.extend(["--project-root", str(args.project_root)])
    if args.release_dir is not None:
        sr_args.extend(["--release-dir", str(args.release_dir)])
    if args.json:
        sr_args.append("--json")
    return store_readiness.main(sr_args)


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="Emit JSON output")

    parser = argparse.ArgumentParser(
        prog="mailprocessor",
        description="MailProcessor headless CLI & desktop tray hub for doc-bricks Universal Mail Tools",
        parents=[common],
    )
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Show application version and exit",
    )
    parser.set_defaults(json=False)

    sub = parser.add_subparsers(dest="command")

    p_status = sub.add_parser("status", parents=[common], help="Show launcher and tool configuration status")
    p_status.set_defaults(func=_cmd_status)

    p_scan = sub.add_parser("scan", parents=[common], help="Scan sibling and download folders for mail tools")
    p_scan.add_argument("--apply", action="store_true", help="Persist detected tools to config.json")
    p_scan.set_defaults(func=_cmd_scan)

    p_snap = sub.add_parser("snapshot", parents=[common], help="Export redacted mailprocessor-suite-v1 snapshot")
    p_snap.add_argument("--out", help="Write snapshot atomically to file path instead of stdout")
    p_snap.set_defaults(func=_cmd_snapshot)

    p_reg = sub.add_parser("register", parents=[common], help="Register a mail tool from script or folder path")
    p_reg.add_argument("tool_id", help=f"Tool ID ({', '.join(sorted(TOOL_DEFINITIONS))})")
    p_reg.add_argument("path", help="Path to main script or tool directory")
    p_reg.add_argument("--installed-by", default="manual", choices=("manual", "scan"), help="Origin label")
    p_reg.set_defaults(func=_cmd_register)

    p_unreg = sub.add_parser("unregister", parents=[common], help="Unregister a configured tool (without deleting files)")
    p_unreg.add_argument("tool_id", help=f"Tool ID ({', '.join(sorted(TOOL_DEFINITIONS))})")
    p_unreg.add_argument("--yes", action="store_true", help="Confirm removing tool registration")
    p_unreg.add_argument("--dry-run", action="store_true", help="Preview unregister without modifying config")
    p_unreg.set_defaults(func=_cmd_unregister)

    p_launch = sub.add_parser("launch", parents=[common], help="Launch a configured mail tool subprocess")
    p_launch.add_argument("tool_id", help=f"Tool ID ({', '.join(sorted(TOOL_DEFINITIONS))})")
    p_launch.add_argument("--dry-run", action="store_true", help="Validate tool path and interpreter without spawning")
    p_launch.set_defaults(func=_cmd_launch)

    p_sr = sub.add_parser("store-readiness", parents=[common], help="Run read-only Microsoft Store readiness audit")
    p_sr.add_argument("--project-root", type=Path, default=None, help="Project root directory")
    p_sr.add_argument("--release-dir", type=Path, default=None, help="Existing vX.Y.Z release directory")
    p_sr.set_defaults(func=_cmd_store_readiness)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.version:
        version = snapshot_export._read_app_version() or "0.1.0"
        payload = {"app": "MailProcessor", "version": version}
        _emit(payload, args.json, [f"MailProcessor {version}"])
        return 0

    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
