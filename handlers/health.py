"""Health check handler for the MCP."""
from __future__ import annotations

from typing import Any, Dict

from utils.exceptions import ToolError


def handle_health_check(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Return placeholder diagnostics for AppleScript and MusicKit connectivity."""

    if arguments:
        raise ToolError(
            "invalid_arguments",
            "mcp.health_check does not accept any arguments.",
            "Remove unexpected parameters from the request.",
        )

    return {
        "status": "pending",
        "checks": {
            "applescript": {
                "status": "not_implemented",
                "hint": "Execute a playpause probe via osascript once AppleScript bridge is ready.",
            },
            "musickit": {
                "status": "not_implemented",
                "hint": "Perform a lightweight catalog search using the developer token once auth is wired.",
            },
        },
    }
