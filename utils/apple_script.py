"""AppleScript utility helpers (placeholder)."""
from __future__ import annotations

from utils.exceptions import ToolError


def run_applescript(script: str) -> str:
    """Execute an AppleScript command via osascript (placeholder implementation)."""

    raise ToolError(
        "applescript_not_configured",
        "AppleScript execution is not available in the current environment.",
        "Implement run_applescript to call osascript on macOS and capture stdout/stderr.",
    )
