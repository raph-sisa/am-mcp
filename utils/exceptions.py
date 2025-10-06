"""Shared exception types for MCP handlers."""
from __future__ import annotations

from typing import Any, Dict, Optional


class ToolError(Exception):
    """Raised when a tool invocation fails with a known error."""

    def __init__(self, code: str, message: str, hint: Optional[str] = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.hint:
            payload["hint"] = self.hint
        return payload


__all__ = ["ToolError"]
