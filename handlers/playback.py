"""Playback control handler placeholder."""
from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Extra, ValidationError

from utils.exceptions import ToolError


PlaybackAction = Literal["play", "pause", "next", "previous", "toggle_shuffle", "toggle_repeat"]


class PlaybackArguments(BaseModel):
    """Arguments for the control_playback tool."""

    action: PlaybackAction
    shuffle_mode: Optional[Literal["off", "songs", "albums"]] = None
    repeat_mode: Optional[Literal["off", "one", "all"]] = None

    class Config:
        extra = Extra.forbid


def handle_playback_control(arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        args = PlaybackArguments(**arguments)
    except ValidationError as exc:
        raise ToolError(
            "invalid_arguments",
            "Invalid parameters for control_playback.",
            str(exc),
        )

    return {
        "status": "pending",
        "message": "AppleScript playback controls not wired yet.",
        "request": args.model_dump(),
    }
