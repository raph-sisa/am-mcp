"""Health check handler for the MCP."""
from __future__ import annotations

from typing import Any, Dict

from utils import musickit
from utils.apple_script import run_applescript
from utils.auth import load_config
from utils.exceptions import ToolError


def handle_health_check(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Return diagnostics for AppleScript and MusicKit connectivity."""

    if arguments:
        raise ToolError(
            "invalid_arguments",
            "mcp.health_check does not accept any arguments.",
            "Remove unexpected parameters from the request.",
        )

    checks: Dict[str, Any] = {}

    try:
        run_applescript('tell application "Music" to playpause')
    except ToolError as exc:
        checks["applescript"] = {
            "status": "error",
            "code": exc.code,
            "message": exc.message,
            "hint": exc.hint,
        }
    else:
        checks["applescript"] = {"status": "ok"}

    try:
        config = load_config()
        response = musickit.search_catalog(
            config=config,
            term="health check",
            types=["songs"],
            limit=1,
            offset=0,
        )
        hit_count = 0
        results = response.get("results", {}) if isinstance(response, dict) else {}
        for bucket in results.values():
            if isinstance(bucket, dict):
                hit_count += len(bucket.get("data", []))
        checks["musickit"] = {"status": "ok", "hits": hit_count}
    except ToolError as exc:
        checks["musickit"] = {
            "status": "error",
            "code": exc.code,
            "message": exc.message,
            "hint": exc.hint,
        }

    status = "ok" if all(check.get("status") == "ok" for check in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
