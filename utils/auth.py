"""Authentication helpers for MusicKit (placeholder)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from utils.exceptions import ToolError


@dataclass
class MusicKitConfig:
    """Configuration derived from environment variables."""

    team_id: str
    key_id: str
    private_key_path: str
    storefront: str


class MissingConfigurationError(ToolError):
    """Raised when required configuration is not present."""

    def __init__(self, hint: Optional[str] = None) -> None:
        super().__init__(
            code="missing_configuration",
            message="MusicKit credentials are not fully configured.",
            hint=hint,
        )


def load_config() -> MusicKitConfig:
    """Load MusicKit configuration from the environment."""

    team_id = os.getenv("TEAM_ID")
    key_id = os.getenv("KEY_ID")
    private_key_path = os.getenv("PRIVATE_KEY_PATH")
    storefront = os.getenv("STOREFRONT")

    missing = [
        name
        for name, value in (
            ("TEAM_ID", team_id),
            ("KEY_ID", key_id),
            ("PRIVATE_KEY_PATH", private_key_path),
            ("STOREFRONT", storefront),
        )
        if not value
    ]

    if missing:
        raise MissingConfigurationError(
            hint=f"Define {', '.join(missing)} in the environment or .env file."
        )

    return MusicKitConfig(
        team_id=team_id or "",
        key_id=key_id or "",
        private_key_path=private_key_path or "",
        storefront=storefront or "",
    )


def generate_developer_token(config: MusicKitConfig, ttl_seconds: int = 3600) -> str:
    """Generate a developer token placeholder."""

    raise ToolError(
        "token_generation_not_implemented",
        "Developer token minting has not been implemented yet.",
        "Use PyJWT to create an ES256 token signed with the MusicKit private key.",
    )
