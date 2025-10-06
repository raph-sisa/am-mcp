"""Library management handlers."""
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Extra, Field, ValidationError

from utils.exceptions import ToolError


class LibraryArguments(BaseModel):
    """Arguments for add/remove library operations."""

    track_id: str = Field(..., description="Identifier of the catalog item")

    class Config:
        extra = Extra.forbid


def handle_add_to_library(arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        args = LibraryArguments(**arguments)
    except ValidationError as exc:
        raise ToolError(
            "invalid_arguments",
            "Invalid parameters for add_to_library.",
            str(exc),
        )

    return {
        "status": "pending",
        "message": "Library add functionality not implemented yet.",
        "request": args.model_dump(),
    }


def handle_remove_from_library(arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        args = LibraryArguments(**arguments)
    except ValidationError as exc:
        raise ToolError(
            "invalid_arguments",
            "Invalid parameters for remove_from_library.",
            str(exc),
        )

    return {
        "status": "pending",
        "message": "Library removal functionality not implemented yet.",
        "request": args.model_dump(),
    }
