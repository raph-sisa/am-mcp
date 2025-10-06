"""Entry point and dispatcher for the Apple Music MCP."""
from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict

from dotenv import load_dotenv
from pydantic import BaseModel, Extra, Field, ValidationError

from handlers import health as health_handler
from handlers import library as library_handler
from handlers import play as play_handler
from handlers import playback as playback_handler
from handlers import playlist as playlist_handler
from handlers import queue as queue_handler
from handlers import search as search_handler

load_dotenv()

from utils.exceptions import ToolError

RequestHandler = Callable[[Dict[str, Any]], Dict[str, Any]]


class ToolRequest(BaseModel):
    """Incoming request payload."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = Extra.forbid


class ToolResponse(BaseModel):
    """Standard tool response payload."""

    request_id: str
    status: str
    result: Dict[str, Any]

    class Config:
        extra = Extra.forbid


@dataclass
class RegisteredHandler:
    handler: RequestHandler
    description: str


class Dispatcher:
    """Route validated requests to the appropriate tool handler."""

    def __init__(self) -> None:
        self._handlers: Dict[str, RegisteredHandler] = {}
        self._logger = self._create_logger()

    @staticmethod
    def _create_logger() -> logging.Logger:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

        class RequestIdFilter(logging.Filter):
            def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
                if not hasattr(record, "request_id"):
                    record.request_id = "-"
                return True

        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s request_id=%(request_id)s message=%(message)s",
            stream=sys.stdout,
        )
        logger = logging.getLogger("apple_music_mcp")
        logger.addFilter(RequestIdFilter())
        return logger

    def register(self, name: str, handler: RequestHandler, description: str) -> None:
        self._handlers[name] = RegisteredHandler(handler=handler, description=description)

    def dispatch(self, payload: Dict[str, Any]) -> ToolResponse:
        try:
            request = ToolRequest(**payload)
        except ValidationError as exc:
            raise ToolError(
                code="invalid_request",
                message="Request validation failed.",
                hint=str(exc),
            ) from exc

        request_id = request.id
        logger = logging.LoggerAdapter(self._logger, extra={"request_id": request_id})
        logger.info("Received request for tool '%s'", request.name)

        if request.name not in self._handlers:
            raise ToolError(
                code="unknown_tool",
                message=f"Tool '{request.name}' is not registered.",
                hint="Check the manifest.json definitions.",
            )

        handler = self._handlers[request.name].handler

        try:
            result = handler(request.arguments)
        except ToolError:
            raise
        except Exception as exc:  # pragma: no cover - defensive catch
            logger.exception("Unexpected error from handler")
            raise ToolError(
                code="internal_error",
                message="An unexpected error occurred.",
                hint="Check server logs for details.",
            ) from exc

        logger.info("Request completed successfully")
        return ToolResponse(request_id=request_id, status="success", result=result)


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.register(
        "search_music",
        search_handler.handle_search,
        "Search the Apple Music catalog using MusicKit.",
    )
    dispatcher.register(
        "play_song",
        play_handler.handle_play_song,
        "Start playback for a song using AppleScript and MusicKit metadata.",
    )
    dispatcher.register(
        "control_playback",
        playback_handler.handle_playback_control,
        "Control playback state such as play, pause, next, previous, shuffle, repeat.",
    )
    dispatcher.register(
        "manage_queue",
        queue_handler.handle_queue,
        "Manage the Apple Music play queue (add/view/clear).",
    )
    dispatcher.register(
        "add_to_library",
        library_handler.handle_add_to_library,
        "Add a catalog item to the local Apple Music library.",
    )
    dispatcher.register(
        "remove_from_library",
        library_handler.handle_remove_from_library,
        "Remove a catalog item from the local Apple Music library.",
    )
    dispatcher.register(
        "create_playlist",
        playlist_handler.handle_create_playlist,
        "Create a new playlist in the local library from catalog metadata.",
    )
    dispatcher.register(
        "mcp.health_check",
        health_handler.handle_health_check,
        "Validate AppleScript and MusicKit connectivity.",
    )
    return dispatcher


def handle_cli() -> int:
    dispatcher = create_dispatcher()
    raw_input = sys.stdin.read()
    try:
        payload = json.loads(raw_input) if raw_input.strip() else {}
    except json.JSONDecodeError as exc:
        error = ToolError("invalid_json", "Failed to parse JSON input.", str(exc))
        print(json.dumps({"status": "error", **error.to_dict()}))
        return 1

    try:
        response = dispatcher.dispatch(payload)
    except ToolError as exc:
        print(json.dumps({"status": "error", **exc.to_dict()}))
        return 2

    print(response.model_dump())
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(handle_cli())
