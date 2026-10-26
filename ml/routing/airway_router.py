"""
airway_router.py
================
Haversine great-circle distance calculator for airway mode.

Current capability:
  - Validates origin and destination coordinates.
  - Computes the shortest great-circle distance between two geographic points.
  - Returns a structured result dict with a clear disclaimer.

Future integration points (not implemented; no synthetic data):
  - Airport lookup by nearest verified ICAO airport to each coordinate.
  - Verified scheduled-service route availability.
  - Actual flight-path geometry (not a straight line).

Do NOT pass road-network risk scores into airway calculations.
"""

import math
from typing import Tuple

# Approximate bounding box for North-East India + reasonable buffer.
# Used only as a sanity-check guard; not a hard constraint on all valid inputs.
_LAT_MIN, _LAT_MAX = 20.0, 32.0
_LON_MIN, _LON_MAX = 85.0, 98.0
_EARTH_RADIUS_KM = 6371.0088  # mean radius per IUGG


class AirwayValidationError(ValueError):
    """Raised when coordinate validation fails before distance calculation."""


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Return the great-circle distance in kilometres between two geographic points
    using the Haversine formula.

    Parameters
    ----------
    lat1, lon1 : float
        Origin latitude and longitude in decimal degrees.
    lat2, lon2 : float
        Destination latitude and longitude in decimal degrees.

    Returns
    -------
    float
        Great-circle distance in kilometres (>= 0.0).

    Notes
    -----
    This function does NOT validate its inputs. Call :func:`calculate_air_route`
    for validated, end-to-end usage.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return _EARTH_RADIUS_KM * c


def _validate_coordinate(lat: float, lon: float, label: str) -> None:
    """Raise AirwayValidationError if lat/lon are unusable."""
    if lat is None or lon is None:
        raise AirwayValidationError(f"{label}: coordinates must not be None.")
    if not math.isfinite(lat) or not math.isfinite(lon):
        raise AirwayValidationError(f"{label}: coordinates must be finite numbers (got lat={lat}, lon={lon}).")
    if not (-90.0 <= lat <= 90.0):
        raise AirwayValidationError(f"{label}: latitude {lat} is outside valid range [-90, 90].")
    if not (-180.0 <= lon <= 180.0):
        raise AirwayValidationError(f"{label}: longitude {lon} is outside valid range [-180, 180].")


def calculate_air_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
) -> dict:
    """
    Validate coordinates and compute a direct air-distance estimate.

    Parameters
    ----------
    origin_lat, origin_lon : float
        Origin coordinates in decimal degrees.
    dest_lat, dest_lon : float
        Destination coordinates in decimal degrees.

    Returns
    -------
    dict with keys:
        transport_mode  : "AIRWAY"
        route_type      : "DIRECT_AIR_DISTANCE"
        distance_km     : float — Haversine great-circle distance.
        coords          : list of [[lat, lon], [lat, lon]] — straight line
                          for map rendering only.
        disclaimer      : str — must be displayed to the user.
        eta_available   : False — never fabricated.

    Raises
    ------
    AirwayValidationError
        If coordinates are invalid or if origin and destination are identical.
    """
    _validate_coordinate(origin_lat, origin_lon, "Origin")
    _validate_coordinate(dest_lat, dest_lon, "Destination")

    # Reject identical endpoints — a zero-distance flight is nonsensical.
    if origin_lat == dest_lat and origin_lon == dest_lon:
        raise AirwayValidationError(
            "Origin and destination coordinates are identical. "
            "A separate airway route cannot be calculated."
        )

    distance = haversine_km(origin_lat, origin_lon, dest_lat, dest_lon)

    return {
        "transport_mode": "AIRWAY",
        "route_type": "DIRECT_AIR_DISTANCE",
        "distance_km": round(distance, 3),
        # Two-point straight line for the Leaflet map — NOT a verified flight path.
        "coords": [[origin_lat, origin_lon], [dest_lat, dest_lon]],
        "disclaimer": (
            "Direct air distance estimate — not a verified flight route. "
            "No airport, airline, schedule, or flight-time data has been used. "
            "The straight line shown is a great-circle approximation only."
        ),
        "eta_available": False,
    }
