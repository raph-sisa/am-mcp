"""Queue management handler."""
from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from utils import musickit
from utils.apple_script import run_applescript
from utils.auth import load_config
from utils.exceptions import ToolError

QueueAction = Literal["add", "view", "clear"]


def _escape(text: str | None) -> str:
    return (text or "").replace("\"", "\\\"")


def _queue_add_script(url: str, play_next: bool) -> str:
    safe_url = _escape(url)
    move_logic = ""
    if play_next:
        move_logic = """set queuePlaylist to playlist \"Up Next\"
        set insertedTrack to last track of queuePlaylist
        move insertedTrack to beginning of queuePlaylist
"""

    return f'''
set musicApp to application "Music"
if not running of musicApp then
    launch musicApp
end if

tell application "Music"
    set targetUrl to "{safe_url}"
    open location targetUrl
    delay 0.5
    pause
    set theTrack to current track
    add theTrack to playlist "Up Next"
    {move_logic}
end tell
'''


def _queue_view_script() -> str:
    return '''
set musicApp to application "Music"
if not running of musicApp then
    launch musicApp
end if

tell application "Music"
    set summaries to {}
    repeat with aTrack in tracks of playlist "Up Next"
        set end of summaries to (name of aTrack & " — " & artist of aTrack)
    end repeat
    return summaries as string
end tell
'''


def _queue_clear_script() -> str:
    return '''
set musicApp to application "Music"
if not running of musicApp then
    launch musicApp
end if

tell application "Music"
    delete every track of playlist "Up Next"
end tell
'''


def _parse_arguments(arguments: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(arguments, dict):
        raise ToolError("invalid_arguments", "Arguments for manage_queue must be an object.")

    unexpected = set(arguments.keys()) - {"action", "track_id", "play_next"}
    if unexpected:
        raise ToolError(
            "invalid_arguments",
            "Unexpected parameters provided to manage_queue.",
            f"Unsupported keys: {', '.join(sorted(unexpected))}.",
        )

    action = arguments.get("action")
    if action not in {"add", "view", "clear"}:
        raise ToolError("invalid_arguments", "'action' must be add, view, or clear.")

    track_id = arguments.get("track_id")
    if track_id is not None and not isinstance(track_id, str):
        raise ToolError("invalid_arguments", "'track_id' must be a string when provided.")

    play_next = arguments.get("play_next", False)
    if not isinstance(play_next, bool):
        raise ToolError("invalid_arguments", "'play_next' must be a boolean.")

    return {"action": action, "track_id": track_id, "play_next": play_next}


def handle_queue(arguments: Dict[str, Any]) -> Dict[str, Any]:
    args = _parse_arguments(arguments)

    if args["action"] == "add":
        if not args["track_id"]:
            raise ToolError(
                "missing_track_id",
                "track_id is required when action=add.",
            )
        config = load_config()
        track = musickit.get_song(config=config, song_id=args["track_id"])
        url = track.get("url")
        if not url:
            raise ToolError(
                "queue_add_unavailable",
                "The track does not expose an Apple Music URL for queuing.",
                "Verify the song is available in the configured storefront.",
            )
        run_applescript(_queue_add_script(url, args["play_next"]))
        return {"status": "queued", "track": track, "play_next": args["play_next"]}

    if args["action"] == "view":
        output = run_applescript(_queue_view_script())
        items = [item.strip() for item in output.split(",") if item.strip()]
        return {"status": "ok", "queue": items}

    if args["action"] == "clear":
        run_applescript(_queue_clear_script())
        return {"status": "cleared"}

    raise ToolError("invalid_action", f"Unknown queue action: {args['action']}")
