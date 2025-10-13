"""Authentication helpers for MusicKit."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
from typing import Optional, Tuple

try:  # pragma: no cover - exercised in integration environments
    import jwt  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback path
    jwt = None  # type: ignore

from utils.exceptions import ToolError


MAX_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 180  # 6 months per Apple guidance


@dataclass(frozen=True)
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


def _read_private_key(path: str) -> str:
    try:
        return Path(path).expanduser().read_text(encoding="utf-8")
    except FileNotFoundError as exc:  # pragma: no cover - depends on local setup
        raise ToolError(
            "private_key_missing",
            "The MusicKit private key file could not be found.",
            f"Verify that '{path}' exists and is readable.",
        ) from exc
    except OSError as exc:  # pragma: no cover - depends on local setup
        raise ToolError(
            "private_key_unreadable",
            "Unable to read the MusicKit private key file.",
            str(exc),
        ) from exc


def _mint_developer_token(
    config: MusicKitConfig,
    ttl_seconds: int,
) -> Tuple[str, datetime]:
    if ttl_seconds <= 0:
        raise ToolError(
            "invalid_token_ttl",
            "Developer token TTL must be a positive integer.",
            "Provide a TTL value greater than zero seconds.",
        )

    if ttl_seconds > MAX_TOKEN_TTL_SECONDS:
        raise ToolError(
            "ttl_too_long",
            "Developer token TTL exceeds the 6 month maximum.",
            "Use a shorter TTL and rotate tokens regularly.",
        )

    private_key = _read_private_key(config.private_key_path)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=ttl_seconds)

    payload = {
        "iss": config.team_id,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "aud": "https://music.apple.com",
    }

    headers = {"alg": "ES256", "kid": config.key_id}

    try:
        token = _encode_jwt_es256(payload, headers, private_key)
    except ToolError:
        raise
    except Exception as exc:  # pragma: no cover - depends on key validity
        raise ToolError(
            "token_generation_failed",
            "Failed to generate a MusicKit developer token.",
            "Confirm the private key contents and permissions.",
        ) from exc

    return token, expires_at


_TOKEN_CACHE: dict[str, Tuple[str, datetime]] = {}
_CACHE_LOCK = threading.Lock()


def generate_developer_token(
    config: MusicKitConfig,
    ttl_seconds: int = 20 * 60,
    refresh_leeway: int = 60,
) -> str:
    """Generate or reuse a cached developer token for the provided config."""

    cache_key = f"{config.team_id}:{config.key_id}:{config.private_key_path}"
    now = datetime.now(timezone.utc)

    with _CACHE_LOCK:
        cached = _TOKEN_CACHE.get(cache_key)
        if cached:
            token, expires_at = cached
            if expires_at - timedelta(seconds=refresh_leeway) > now:
                return token

    token, expires_at = _mint_developer_token(config, ttl_seconds)

    with _CACHE_LOCK:
        _TOKEN_CACHE[cache_key] = (token, expires_at)

    return token


from typing import Any, Mapping


def _encode_jwt_es256(
    payload: Mapping[str, Any], headers: Mapping[str, Any], private_key: str
) -> str:
    if jwt is not None:  # pragma: no cover - relies on optional dependency
        return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

    signing_input = _build_signing_input(headers, payload)
    signature = _sign_with_openssl(signing_input, private_key)
    return f"{signing_input}.{signature}"


def _build_signing_input(headers: Mapping[str, Any], payload: Mapping[str, Any]) -> str:
    header_json = json.dumps(headers, separators=(",", ":"), sort_keys=True).encode()
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return ".".join((_b64url(header_json), _b64url(payload_json)))


def _sign_with_openssl(signing_input: str, private_key: str) -> str:
    key_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False) as key_file:
            key_file.write(private_key)
        key_path = key_file.name
        process = subprocess.run(  # noqa: S603, S607
            ["openssl", "dgst", "-sha256", "-sign", key_path],
            input=signing_input.encode(),
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise ToolError(
            "openssl_missing",
            "OpenSSL is required to sign developer tokens when PyJWT is unavailable.",
            "Install OpenSSL or add PyJWT to the environment.",
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise ToolError(
            "openssl_sign_failed",
            "OpenSSL failed to sign the developer token payload.",
            exc.stderr.decode() if exc.stderr else None,
        ) from exc
    finally:
        if key_path:
            try:
                os.unlink(key_path)
            except OSError:  # pragma: no cover - best effort cleanup
                pass

    der_signature = process.stdout
    raw_signature = _der_to_raw(der_signature)
    return _b64url(raw_signature)


def _der_to_raw(signature: bytes) -> bytes:
    if len(signature) < 8 or signature[0] != 0x30:
        raise ToolError(
            "invalid_signature",
            "Unexpected signature encoding returned by OpenSSL.",
        )
    length = signature[1]
    if length + 2 != len(signature):
        signature = signature[: length + 2]
    offset = 2
    if signature[offset] != 0x02:
        raise ToolError("invalid_signature", "Malformed DER sequence (missing R component).")
    r_len = signature[offset + 1]
    r = signature[offset + 2 : offset + 2 + r_len]
    offset += 2 + r_len
    if signature[offset] != 0x02:
        raise ToolError("invalid_signature", "Malformed DER sequence (missing S component).")
    s_len = signature[offset + 1]
    s = signature[offset + 2 : offset + 2 + s_len]
    r = r.lstrip(b"\x00").rjust(32, b"\x00")
    s = s.lstrip(b"\x00").rjust(32, b"\x00")
    return r + s


def _b64url(data: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
