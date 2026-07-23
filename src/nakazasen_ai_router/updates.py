"""Safe, opt-in release awareness for Nakazasen AI Router."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any, Callable

from .http import UrllibHTTPClient

DISTRIBUTION_NAME = "nakazasen-ai-router"
DEFAULT_TAGS_URL = "https://api.github.com/repos/Nakazasen/nakazasen-ai-router/tags?per_page=30"
_VERSION_RE = re.compile(
    r"^v?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_CACHE: dict[tuple[str, str, bool], tuple[float, "UpdateInfo"]] = {}


@dataclass(frozen=True)
class UpdateInfo:
    """Non-sensitive result of a release check."""

    current_version: str
    latest_version: str = ""
    status: str = "unknown"
    release_url: str = ""
    error_type: str = ""
    checked_at: float = 0.0

    @property
    def update_available(self) -> bool:
        return self.status == "update_available"

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "status": self.status,
            "release_url": self.release_url,
            "error_type": self.error_type,
            "checked_at": self.checked_at,
        }


def installed_version(distribution_name: str = DISTRIBUTION_NAME) -> str:
    """Return the installed distribution version, with a source-tree fallback."""

    source_pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if source_pyproject.is_file():
        try:
            match = re.search(
                r'^version\s*=\s*"([^"]+)"',
                source_pyproject.read_text(encoding="utf-8-sig"),
                re.MULTILINE,
            )
        except OSError:
            match = None
        if match:
            return match.group(1)

    try:
        return metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
        return "0.0.0+source"


def check_for_updates(
    *,
    enable_network: bool = False,
    current_version: str | None = None,
    http_client: Any | None = None,
    tags_url: str = DEFAULT_TAGS_URL,
    include_prerelease: bool = False,
    timeout: float = 3.0,
    cache_ttl_seconds: float = 3600.0,
    clock: Callable[[], float] = time.time,
) -> UpdateInfo:
    """Check GitHub tags only when network access is explicitly enabled.

    Failures are represented as data and never prevent imports or router startup.
    No prompts, provider keys, router metadata, or telemetry are sent.
    """

    current = current_version or installed_version()
    checked_at = float(clock())
    if not enable_network:
        return UpdateInfo(current, status="network_disabled", checked_at=checked_at)

    cache_key = (tags_url, current, include_prerelease)
    cached = _CACHE.get(cache_key)
    if cached and cache_ttl_seconds > 0 and checked_at - cached[0] < cache_ttl_seconds:
        return cached[1]

    client = http_client or UrllibHTTPClient()
    try:
        response = client.get(
            tags_url,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "nakazasen-ai-router-version-check"},
            timeout=max(0.1, float(timeout)),
        )
        if int(getattr(response, "status_code", 0)) != 200:
            result = UpdateInfo(current, status="check_failed", error_type="http_error", checked_at=checked_at)
        else:
            payload = response.json()
            tags = [str(item.get("name", "")) for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []
            latest = _latest_version(tags, include_prerelease=include_prerelease)
            if not latest:
                result = UpdateInfo(current, status="check_failed", error_type="no_valid_release", checked_at=checked_at)
            else:
                current_key = _version_key(current)
                latest_key = _version_key(latest)
                status = "update_available" if current_key is not None and latest_key is not None and latest_key > current_key else "up_to_date"
                result = UpdateInfo(
                    current,
                    latest,
                    status,
                    f"https://github.com/Nakazasen/nakazasen-ai-router/tree/v{latest}",
                    checked_at=checked_at,
                )
    except Exception as exc:
        result = UpdateInfo(current, status="check_failed", error_type=_safe_error_type(exc), checked_at=checked_at)

    _CACHE[cache_key] = (checked_at, result)
    return result


def clear_update_cache() -> None:
    """Clear the process-local release-check cache (primarily for tests)."""

    _CACHE.clear()


def _latest_version(tags: list[str], *, include_prerelease: bool) -> str:
    candidates: list[tuple[tuple[int, int, int, tuple[tuple[int, int | str], ...]], str]] = []
    for tag in tags:
        key = _version_key(tag)
        normalized = _normalized_tag(tag)
        if key is not None and normalized is not None:
            if not include_prerelease and "-" in normalized:
                continue
            candidates.append((key, normalized))
    return max(candidates, default=((0, 0, 0), ""))[1]


def _version_key(value: str) -> tuple[int, int, int, tuple[tuple[int, int | str], ...]] | None:
    match = _VERSION_RE.fullmatch(str(value).strip())
    if not match:
        return None
    prerelease = match.group("prerelease")
    if prerelease is None:
        prerelease_key: tuple[tuple[int, int | str], ...] = ((2, ""),)
    else:
        prerelease_key = tuple(
            (0, int(identifier)) if identifier.isdigit() else (1, identifier)
            for identifier in prerelease.split(".")
        )
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        prerelease_key,
    )


def _normalized_tag(value: str) -> str | None:
    match = _VERSION_RE.fullmatch(str(value).strip())
    if not match:
        return None
    normalized = f"{match.group('major')}.{match.group('minor')}.{match.group('patch')}"
    prerelease = match.group("prerelease")
    return f"{normalized}-{prerelease}" if prerelease else normalized


def _safe_error_type(exc: Exception) -> str:
    name = type(exc).__name__.lower()
    if "timeout" in name:
        return "timeout"
    if "json" in name or isinstance(exc, (TypeError, ValueError)):
        return "invalid_response"
    return "network_error"