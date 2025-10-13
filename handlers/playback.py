"""Playback control handler."""
from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from utils.apple_script import run_applescript
from utils.exceptions import ToolError


PlaybackAction = Literal["play", "pause", "next", "previous", "toggle_shuffle", "toggle_repeat"]


def _with_music_app(script_body: str) -> str:
    return f'''
set musicApp to application "Music"
if not running of musicApp then
    launch musicApp
end if

tell application "Music"
{script_body}
end tell
'''


def _shuffle_script(mode: Optional[str]) -> str:
    if mode is None:
        return _with_music_app(
            """set shuffle enabled to not shuffle enabled
if shuffle enabled then set shuffle mode to songs
"""
        )

    if mode == "off":
        return _with_music_app("set shuffle enabled to false")

    return _with_music_app(
        f"""set shuffle enabled to true
set shuffle mode to {mode}
"""
    )


def _repeat_script(mode: Optional[str]) -> str:
    if mode is None:
        return _with_music_app(
            """if song repeat is off then
    set song repeat to one
else if song repeat is one then
    set song repeat to all
else
    set song repeat to off
end if
"""
        )

    return _with_music_app(f"set song repeat to {mode}")


def _script_for_action(action: str, shuffle_mode: Optional[str], repeat_mode: Optional[str]) -> str:
    if action == "play":
        return _with_music_app("play")
    if action == "pause":
        return _with_music_app("pause")
    if action == "next":
        return _with_music_app("next track")
    if action == "previous":
        return _with_music_app("previous track")
    if action == "toggle_shuffle":
        return _shuffle_script(shuffle_mode)
    if action == "toggle_repeat":
        return _repeat_script(repeat_mode)
    raise ToolError("unsupported_action", "Unsupported playback action.")


def _parse_arguments(arguments: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(arguments, dict):
        raise ToolError("invalid_arguments", "Arguments for control_playback must be an object.")

    unexpected = set(arguments.keys()) - {"action", "shuffle_mode", "repeat_mode"}
    if unexpected:
        raise ToolError(
            "invalid_arguments",
            "Unexpected parameters provided to control_playback.",
            f"Unsupported keys: {', '.join(sorted(unexpected))}.",
        )

    action = arguments.get("action")
    if action not in {"play", "pause", "next", "previous", "toggle_shuffle", "toggle_repeat"}:
        raise ToolError(
            "invalid_arguments",
            "'action' must be one of play, pause, next, previous, toggle_shuffle, toggle_repeat.",
        )

    shuffle_mode = arguments.get("shuffle_mode")
    if shuffle_mode is not None and shuffle_mode not in {"off", "songs", "albums"}:
        raise ToolError(
            "invalid_arguments",
            "'shuffle_mode' must be one of off, songs, albums.",
        )

    repeat_mode = arguments.get("repeat_mode")
    if repeat_mode is not None and repeat_mode not in {"off", "one", "all"}:
        raise ToolError(
            "invalid_arguments",
            "'repeat_mode' must be one of off, one, all.",
        )

    return {"action": action, "shuffle_mode": shuffle_mode, "repeat_mode": repeat_mode}


def handle_playback_control(arguments: Dict[str, Any]) -> Dict[str, Any]:
    args = _parse_arguments(arguments)

    script = _script_for_action(args["action"], args["shuffle_mode"], args["repeat_mode"])
    run_applescript(script)

    response: Dict[str, Any] = {"action": args["action"], "status": "ok"}
    if args["shuffle_mode"] is not None:
        response["shuffle_mode"] = args["shuffle_mode"]
    if args["repeat_mode"] is not None:
        response["repeat_mode"] = args["repeat_mode"]

    return response
