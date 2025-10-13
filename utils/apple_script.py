"""AppleScript utility helpers."""
from __future__ import annotations

import platform
import subprocess

from utils.exceptions import ToolError


def run_applescript(script: str, *, timeout: float = 10.0) -> str:
    """Execute an AppleScript command via osascript on macOS."""

    if platform.system() != "Darwin":
        raise ToolError(
            "applescript_unavailable",
            "AppleScript execution is only supported on macOS.",
            "Run the MCP on a macOS host with the Music app installed.",
        )

    if not script.strip():
        raise ToolError(
            "empty_script",
            "No AppleScript content was provided.",
            "Pass a non-empty script string to run_applescript.",
        )

    try:
        process = subprocess.run(  # noqa: S603, S607
            ["osascript", "-"],
            input=script,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:  # pragma: no cover - depends on host
        raise ToolError(
            "osascript_not_found",
            "osascript is not available on this system.",
            "Ensure the AppleScript runtime is installed and accessible in PATH.",
        ) from exc
    except subprocess.TimeoutExpired as exc:  # pragma: no cover - depends on host
        raise ToolError(
            "applescript_timeout",
            "AppleScript execution timed out.",
            "Review the script for long-running operations or increase the timeout.",
        ) from exc

    if process.returncode != 0:
        stderr = process.stderr.strip()
        raise ToolError(
            "applescript_error",
            "AppleScript command failed.",
            stderr or "Check Automation permissions in macOS settings.",
        )

    return (process.stdout or "").strip()
