"""MusicKit API helpers with graceful fallbacks."""
from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional

try:  # pragma: no cover - optional dependency
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback to urllib
    requests = None  # type: ignore

from utils.auth import MusicKitConfig, generate_developer_token
from utils.exceptions import ToolError


_API_BASE_URL = "https://api.music.apple.com"
_DEFAULT_TIMEOUT = 10
_MAX_RETRIES = 3


@dataclass
class _HttpResponse:
    status_code: int
    text: str

    def json(self) -> Any:
        return json.loads(self.text)


def _perform_request(
    method: str,
    url: str,
    *,
    headers: Mapping[str, str],
    params: Optional[Mapping[str, Any]] = None,
    timeout: int = _DEFAULT_TIMEOUT,
) -> _HttpResponse:
    if requests is not None:  # pragma: no cover - exercised when requests is installed
        session = requests.Session()
        try:
            response = session.request(
                method,
                url,
                headers=headers,
                params=params,
                timeout=timeout,
            )
        except Exception as exc:  # pragma: no cover - network errors covered in fallback
            raise ToolError(
                "network_error",
                "Unable to reach the MusicKit API.",
                "Check network connectivity and Apple Music service status.",
            ) from exc
        return _HttpResponse(status_code=response.status_code, text=response.text)

    from urllib import error as urllib_error
    from urllib import parse, request

    full_url = url
    if params:
        query = parse.urlencode({k: str(v) for k, v in params.items()})
        full_url = f"{url}?{query}"

    req = request.Request(full_url, method=method, headers=dict(headers))
    try:
        with request.urlopen(req, timeout=timeout) as resp:  # type: ignore[arg-type]
            status = resp.status
            text = resp.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        status = exc.code
        text = exc.read().decode("utf-8")
    except urllib_error.URLError as exc:
        raise ToolError(
            "network_error",
            "Unable to reach the MusicKit API.",
            str(exc.reason),
        ) from exc

    return _HttpResponse(status_code=status, text=text)


def _request(
    method: str,
    path: str,
    *,
    config: MusicKitConfig,
    params: Optional[Mapping[str, Any]] = None,
    timeout: int = _DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    token = generate_developer_token(config)
    url = f"{_API_BASE_URL}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    last_error: Optional[ToolError] = None
    for attempt in range(1, _MAX_RETRIES + 1):
        response = _perform_request(method, url, headers=headers, params=params, timeout=timeout)

        if 500 <= response.status_code < 600:
            if attempt == _MAX_RETRIES:
                last_error = ToolError(
                    "musickit_unavailable",
                    "MusicKit returned repeated server errors.",
                    f"Last status: {response.status_code}",
                )
                break
            sleep_seconds = min(1.5, 0.2 * attempt + random.uniform(0, 0.3))
            time.sleep(sleep_seconds)
            continue

        if response.status_code != 200:
            _raise_for_status(response)

        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise ToolError(
                "invalid_response",
                "MusicKit response was not valid JSON.",
                str(exc),
            ) from exc

    if last_error is None:
        last_error = ToolError(
            "musickit_unavailable",
            "MusicKit API request failed after retries.",
            None,
        )
    raise last_error


def _raise_for_status(response: _HttpResponse) -> None:
    hint = None
    try:
        payload = response.json()
        errors = payload.get("errors") if isinstance(payload, dict) else None
        if errors and isinstance(errors, Iterable):
            first = next(iter(errors), None)
            if isinstance(first, dict):
                hint = first.get("detail") or first.get("message")
    except json.JSONDecodeError:
        hint = response.text

    raise ToolError(
        "musickit_error",
        f"MusicKit API returned status {response.status_code}.",
        hint,
    )


def search_catalog(
    *,
    config: MusicKitConfig,
    term: str,
    types: Iterable[str],
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    params = {
        "term": term,
        "types": ",".join(types),
        "limit": str(limit),
        "offset": str(offset),
    }
    return _request("GET", f"/v1/catalog/{config.storefront}/search", config=config, params=params)


def get_catalog_resource(
    *,
    config: MusicKitConfig,
    resource_type: str,
    resource_id: str,
) -> Dict[str, Any]:
    return _request(
        "GET",
        f"/v1/catalog/{config.storefront}/{resource_type}/{resource_id}",
        config=config,
    )


def normalize_song(resource: Dict[str, Any]) -> Dict[str, Any]:
    attributes = resource.get("attributes", {})
    return {
        "id": resource.get("id"),
        "type": resource.get("type"),
        "name": attributes.get("name"),
        "artist": attributes.get("artistName"),
        "album": attributes.get("albumName"),
        "genre_names": attributes.get("genreNames"),
        "url": attributes.get("url"),
        "artwork": attributes.get("artwork"),
        "duration_in_millis": attributes.get("durationInMillis"),
        "release_date": attributes.get("releaseDate"),
        "play_params": attributes.get("playParams"),
    }


def get_song(*, config: MusicKitConfig, song_id: str) -> Dict[str, Any]:
    response = get_catalog_resource(
        config=config,
        resource_type="songs",
        resource_id=song_id,
    )

    data = response.get("data") if isinstance(response, dict) else None
    if not data:
        raise ToolError(
            "track_not_found",
            "The requested track was not found in the Apple Music catalog.",
            "Verify the identifier and storefront settings.",
        )

    return normalize_song(data[0])
