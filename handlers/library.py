"""Library management handlers."""
from __future__ import annotations

from typing import Any, Dict

from utils import musickit
from utils.apple_script import run_applescript
from utils.auth import load_config
from utils.exceptions import ToolError


def _escape(text: str | None) -> str:
    return (text or "").replace("\"", "\\\"")


def _parse_arguments(arguments: Dict[str, Any]) -> str:
    if not isinstance(arguments, dict):
        raise ToolError("invalid_arguments", "Arguments must be provided as an object.")

    unexpected = set(arguments.keys()) - {"track_id"}
    if unexpected:
        raise ToolError(
            "invalid_arguments",
            "Unexpected parameters supplied.",
            f"Unsupported keys: {', '.join(sorted(unexpected))}.",
        )

    track_id = arguments.get("track_id")
    if not isinstance(track_id, str) or not track_id:
        raise ToolError(
            "invalid_arguments",
            "'track_id' is required and must be a string.",
        )

    return track_id


def handle_add_to_library(arguments: Dict[str, Any]) -> Dict[str, Any]:
    track_id = _parse_arguments(arguments)

    config = load_config()
    track = musickit.get_song(config=config, song_id=track_id)
    url = track.get("url")
    if not url:
        raise ToolError(
            "library_add_unavailable",
            "The track does not expose a playable URL for library import.",
            "Confirm the catalog item is available in the configured storefront.",
        )

    safe_url = _escape(url)
    script = f'''
set musicApp to application "Music"
if not running of musicApp then
    launch musicApp
end if
open location "{safe_url}"
delay 1.0
tell application "Music" to add current track to playlist "Library"
'''
    run_applescript(script)

    return {"status": "added", "track": track}


def handle_remove_from_library(arguments: Dict[str, Any]) -> Dict[str, Any]:
    track_id = _parse_arguments(arguments)

    config = load_config()
    track = musickit.get_song(config=config, song_id=track_id)
    name = _escape(track.get("name"))
    artist = _escape(track.get("artist"))
    album = _escape(track.get("album"))

    script = f'''
set musicApp to application "Music"
if not running of musicApp then
    launch musicApp
end if

tell application "Music"
    set libraryPlaylist to playlist "Library"
    set matchingTracks to (every track of libraryPlaylist whose name is "{name}" and artist is "{artist}")
    repeat with aTrack in matchingTracks
        if album of aTrack is "{album}" then
            delete aTrack
            exit repeat
        end if
    end repeat
end tell
'''
    run_applescript(script)

    return {"status": "removed", "track": track}
