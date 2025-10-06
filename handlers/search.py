"""Search handler placeholder for the Apple Music MCP."""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Extra, Field, ValidationError

from utils.exceptions import ToolError


class SearchArguments(BaseModel):
    """Arguments accepted by the search tool."""

    term: str = Field(..., description="Search term to query the Apple Music catalog")
    types: List[str] = Field(default_factory=lambda: ["songs"], description="Resource types")
    limit: int = Field(10, ge=1, le=25)
    offset: int = Field(0, ge=0)

    class Config:
        extra = Extra.forbid


def handle_search(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Validate input and return a placeholder response."""

    try:
        args = SearchArguments(**arguments)
    except ValidationError as exc:
        raise ToolError("invalid_arguments", "Invalid parameters for search_music.", str(exc))

    return {
        "status": "pending",
        "message": "MusicKit search integration is not implemented yet.",
        "request": args.model_dump(),
    }
