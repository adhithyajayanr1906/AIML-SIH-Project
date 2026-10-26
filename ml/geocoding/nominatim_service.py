"""
ml/geocoding/nominatim_service.py
==================================
Reusable geocoding service backed by OpenStreetMap Nominatim.

Policy compliance:
  - User-Agent must identify the application (required by Nominatim ToS).
  - A maximum of 1 request per second is enforced via a module-level rate guard.
  - No aggressive autocomplete traffic; the endpoint applies a minimum query length.
  - Results are cached in a simple LRU cache to avoid redundant requests.
  - No place names or coordinates are fabricated.

Usage:
    from ml.geocoding.nominatim_service import search_locations, GeocodingError
"""

import time
import urllib.request
import urllib.parse
import urllib.error
import json
import threading
import functools
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Identify the application as required by the Nominatim usage policy.
# https://operations.osmfoundation.org/policies/nominatim/
USER_AGENT = "NER-Smart-Logistics/1.0 (academic project; NE India logistics research)"

# Request defaults
REQUEST_TIMEOUT_S  = 8      # seconds before aborting a Nominatim call
MAX_RESULTS        = 7      # maximum suggestions returned per query
MIN_QUERY_LENGTH   = 2      # refuse to geocode trivially short strings

# NER region "viewbox" to bias results toward North-East India (not exclusive).
# Bounds: roughly 22°N–29.5°N, 89.5°E–97.5°E
NER_VIEWBOX      = "89.5,22.0,97.5,29.5"
NER_BOUNDED      = 0   # 0 = viewbox is a bias, not a hard boundary

# ---------------------------------------------------------------------------
# Rate limiter — max 1 Nominatim request per second (per ToS)
# ---------------------------------------------------------------------------

_rate_lock       = threading.Lock()
_last_request_ts = 0.0       # Unix timestamp of the most recent outgoing call

def _rate_wait() -> None:
    """Block the calling thread until the 1 req/s rate limit is satisfied."""
    global _last_request_ts
    with _rate_lock:
        now   = time.monotonic()
        delta = now - _last_request_ts
        if delta < 1.0:
            time.sleep(1.0 - delta)
        _last_request_ts = time.monotonic()

# ---------------------------------------------------------------------------
# Simple LRU result cache (128 unique queries)
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=128)
def _cached_geocode(query_lower: str) -> str:
    """
    Execute a Nominatim search and return the raw JSON string.
    Cached by normalised query string.  Raises GeocodingError on failure.
    """
    _rate_wait()

    params = {
        "q":              query_lower,
        "format":         "jsonv2",
        "limit":          MAX_RESULTS,
        "addressdetails": 1,
        "viewbox":        NER_VIEWBOX,
        "bounded":        NER_BOUNDED,
    }
    url = f"{NOMINATIM_URL}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
            if resp.status != 200:
                raise GeocodingError(
                    f"Nominatim returned HTTP {resp.status}."
                )
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise GeocodingError(
            f"Nominatim HTTP error {exc.code}: {exc.reason}."
        ) from exc
    except urllib.error.URLError as exc:
        raise GeocodingError(
            f"Nominatim network error: {exc.reason}."
        ) from exc
    except TimeoutError as exc:
        raise GeocodingError("Nominatim request timed out.") from exc

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class GeocodingError(RuntimeError):
    """Raised when the geocoding provider cannot be reached or returns an error."""


def search_locations(query: str) -> list[dict]:
    """
    Search for real geographic places matching *query*.

    Returns a list of result dicts, each containing:
        display_name  – human-readable place label
        latitude      – float
        longitude     – float
        place_type    – OSM place category string
        source        – always "openstreetmap_nominatim"

    Raises:
        ValueError      – if the query is too short or empty
        GeocodingError  – if the provider is unavailable or returns an error
    """
    if not query or not query.strip():
        raise ValueError("Query must not be empty.")
    q = query.strip()
    if len(q) < MIN_QUERY_LENGTH:
        raise ValueError(
            f"Query must be at least {MIN_QUERY_LENGTH} characters long."
        )

    raw_json = _cached_geocode(q.lower())        # may raise GeocodingError

    try:
        raw_results: list[dict] = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise GeocodingError("Nominatim returned unparseable JSON.") from exc

    results = []
    for item in raw_results:
        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
        except (KeyError, TypeError, ValueError):
            # Skip any result with invalid or missing coordinates
            continue

        # Sanity-check coordinates are geographically valid
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            continue

        display_name = item.get("display_name", "").strip() or item.get("name", "Unknown")
        place_type   = item.get("type") or item.get("category") or "place"

        results.append({
            "display_name": display_name,
            "latitude":     round(lat, 6),
            "longitude":    round(lon, 6),
            "place_type":   place_type,
            "source":       "openstreetmap_nominatim",
        })

    return results
