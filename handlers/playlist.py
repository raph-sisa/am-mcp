"""Playlist creation handler."""
from __future__ import annotations

from typing import Any, Dict, List

from utils import musickit
from utils.apple_script import run_applescript
from utils.auth import load_config
from utils.exceptions import ToolError


def _escape(text: str | None) -> str:
    return (text or "").replace("\"", "\\\"")


def _ensure_playlist(name: str, description: str | None) -> None:
    safe_name = _escape(name)
    safe_description = _escape(description)
    script = f'''
set musicApp to application "Music"
if not running of musicApp then
    launch musicApp
end if

tell application "Music"
    if exists playlist "{safe_name}" then
        set targetPlaylist to playlist "{safe_name}"
        delete every track of targetPlaylist
    else
        set targetPlaylist to make new playlist with properties {{name:"{safe_name}"}}
    end if
    if "{safe_description}" is not "" then
        set description of targetPlaylist to "{safe_description}"
    end if
end tell
'''
    run_applescript(script)


def _add_track_to_playlist(name: str, url: str) -> None:
    safe_name = _escape(name)
    safe_url = _escape(url)
    script = f'''
set musicApp to application "Music"
if not running of musicApp then
    launch musicApp
end if
open location "{safe_url}"
delay 1.0

tell application "Music"
    add current track to playlist "{safe_name}"
end tell
'''
    run_applescript(script)


def _parse_arguments(arguments: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(arguments, dict):
        raise ToolError("invalid_arguments", "Arguments for create_playlist must be an object.")

    unexpected = set(arguments.keys()) - {"name", "description", "track_ids"}
    if unexpected:
        raise ToolError(
            "invalid_arguments",
            "Unexpected parameters provided to create_playlist.",
            f"Unsupported keys: {', '.join(sorted(unexpected))}.",
        )

    name = arguments.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ToolError(
            "invalid_arguments",
            "'name' is required and must be a non-empty string.",
        )

    description = arguments.get("description")
    if description is not None and not isinstance(description, str):
        raise ToolError(
            "invalid_arguments",
            "'description' must be a string when provided.",
        )

    track_ids = arguments.get("track_ids", [])
    if not isinstance(track_ids, list) or not all(isinstance(item, str) and item for item in track_ids):
        raise ToolError(
            "invalid_arguments",
            "'track_ids' must be an array of non-empty strings.",
        )

    return {"name": name, "description": description, "track_ids": track_ids}


def handle_create_playlist(arguments: Dict[str, Any]) -> Dict[str, Any]:
    args = _parse_arguments(arguments)

    config = load_config()
    tracks = [musickit.get_song(config=config, song_id=track_id) for track_id in args["track_ids"]]

    _ensure_playlist(args["name"], args["description"])
    for track in tracks:
        url = track.get("url")
        if not url:
            raise ToolError(
                "playlist_track_unavailable",
                "One of the tracks is missing a playable URL.",
                f"Track '{track.get('name')}' may be unavailable in this storefront.",
            )
        _add_track_to_playlist(args["name"], url)

    return {
        "status": "created",
        "name": args["name"],
        "description": args["description"],
        "tracks": tracks,
    }
