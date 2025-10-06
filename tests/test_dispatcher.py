"""Basic dispatcher tests for scaffolding."""
from __future__ import annotations

import pytest

from main import create_dispatcher
from utils.exceptions import ToolError


def test_unknown_tool() -> None:
    dispatcher = create_dispatcher()
    with pytest.raises(ToolError) as exc:
        dispatcher.dispatch({"name": "unknown_tool"})

    assert exc.value.code == "unknown_tool"


def test_argument_validation_error() -> None:
    dispatcher = create_dispatcher()

    with pytest.raises(ToolError) as exc:
        dispatcher.dispatch(
            {
                "name": "search_music",
                "arguments": {"term": "hello", "types": ["songs"], "limit": 5, "extra": True},
            }
        )

    assert exc.value.code == "invalid_arguments"


def test_health_check_rejects_arguments() -> None:
    dispatcher = create_dispatcher()

    with pytest.raises(ToolError) as exc:
        dispatcher.dispatch({"name": "mcp.health_check", "arguments": {"unexpected": True}})

    assert exc.value.code == "invalid_arguments"
