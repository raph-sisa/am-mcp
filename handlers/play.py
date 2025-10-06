"""Play handler placeholder."""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Extra, Field, ValidationError

from utils.exceptions import ToolError


class PlaySongArguments(BaseModel):
    """Arguments for initiating playback."""

    track_id: str = Field(..., description="Apple Music catalog identifier")
    play_location_url: Optional[str] = Field(
        default=None,
        description="If provided, open this URL via AppleScript",
    )

    class Config:
        extra = Extra.forbid


def handle_play_song(arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        args = PlaySongArguments(**arguments)
    except ValidationError as exc:
        raise ToolError("invalid_arguments", "Invalid parameters for play_song.", str(exc))

    return {
        "status": "pending",
        "message": "Playback bridge not yet implemented.",
        "request": args.model_dump(),
    }
