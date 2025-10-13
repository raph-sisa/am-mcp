"""Search handler for the Apple Music MCP."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Tuple

from utils import musickit
from utils.auth import MusicKitConfig, load_config
from utils.exceptions import ToolError


_CACHE_TTL_SECONDS = 300
_SEARCH_CACHE: Dict[Tuple[str, Tuple[str, ...], int, int], Tuple[float, Dict[str, Any]]] = {}


def _parse_arguments(arguments: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(arguments, dict):
        raise ToolError(
            "invalid_arguments",
            "Arguments for search_music must be an object.",
        )

    unexpected = set(arguments.keys()) - {"term", "types", "limit", "offset"}
    if unexpected:
        raise ToolError(
            "invalid_arguments",
            "Unexpected parameters provided to search_music.",
            f"Unsupported keys: {', '.join(sorted(unexpected))}.",
        )

    term = arguments.get("term")
    if not isinstance(term, str) or not term.strip():
        raise ToolError(
            "invalid_arguments",
            "'term' is required and must be a non-empty string.",
        )

    types = arguments.get("types", ["songs"])
    if not isinstance(types, list) or not all(isinstance(item, str) and item for item in types):
        raise ToolError(
            "invalid_arguments",
            "'types' must be an array of non-empty strings.",
        )

    limit = arguments.get("limit", 10)
    if not isinstance(limit, int) or not 1 <= limit <= 25:
        raise ToolError(
            "invalid_arguments",
            "'limit' must be an integer between 1 and 25.",
        )

    offset = arguments.get("offset", 0)
    if not isinstance(offset, int) or offset < 0:
        raise ToolError(
            "invalid_arguments",
            "'offset' must be a non-negative integer.",
        )

    return {"term": term, "types": types, "limit": limit, "offset": offset}


def _normalize_result(resource: Dict[str, Any]) -> Dict[str, Any]:
    normalized = musickit.normalize_song(resource)
    artwork = normalized.get("artwork") or {}
    normalized["artwork"] = {
        "url": artwork.get("url"),
        "width": artwork.get("width"),
        "height": artwork.get("height"),
    }
    return normalized


def _load_config() -> MusicKitConfig:
    try:
        return load_config()
    except ToolError as exc:
        raise ToolError(
            exc.code,
            exc.message,
            exc.hint or "Ensure TEAM_ID, KEY_ID, PRIVATE_KEY_PATH, and STOREFRONT are configured.",
        ) from exc


def handle_search(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Validate input, query MusicKit, and return normalized results."""

    args = _parse_arguments(arguments)

    cache_key = (
        args["term"].lower(),
        tuple(sorted(args["types"])),
        args["limit"],
        args["offset"],
    )
    cached = _SEARCH_CACHE.get(cache_key)
    now = time.time()
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return {"source": "cache", **cached[1]}

    config = _load_config()
    response = musickit.search_catalog(
        config=config,
        term=args["term"],
        types=args["types"],
        limit=args["limit"],
        offset=args["offset"],
    )

    normalized_results: List[Dict[str, Any]] = []
    results = response.get("results", {}) if isinstance(response, dict) else {}
    for type_bucket in results.values():
        items = type_bucket.get("data", []) if isinstance(type_bucket, dict) else []
        for resource in items:
            normalized_results.append(_normalize_result(resource))

    payload = {
        "term": args["term"],
        "types": args["types"],
        "limit": args["limit"],
        "offset": args["offset"],
        "storefront": config.storefront,
        "results": normalized_results,
        "raw": response,
    }

    _SEARCH_CACHE[cache_key] = (now, payload)
    return {"source": "live", **payload}
