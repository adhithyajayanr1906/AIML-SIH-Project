"""
tests/test_routing.py
=====================
Pure unit tests for the airway_router module (Haversine + validation).

These tests do NOT require a running server and do NOT touch the road graph,
geospatial datasets, or any network connection. They validate the mathematical
correctness of the Haversine implementation and the input-validation logic of
calculate_air_route().

Run with:
    python -m pytest tests/test_routing.py -v
"""

import math
import sys
import os

# Ensure the routing module is importable without installing as a package.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ml', 'routing')))

import pytest
from airway_router import haversine_km, calculate_air_route, AirwayValidationError


# ============================================================================
# Haversine distance tests
# ============================================================================

class TestHaversine:
    """Mathematical correctness of haversine_km()."""

    def test_known_distance_guwahati_to_shillong(self):
        """
        Guwahati (26.1445, 91.7362) to Shillong (25.5788, 91.8933).
        Verified reference value: approximately 68 km great-circle distance.
        Tolerance: ±2 km.
        """
        origin_lat, origin_lon = 26.1445, 91.7362
        dest_lat,   dest_lon   = 25.5788, 91.8933

        dist = haversine_km(origin_lat, origin_lon, dest_lat, dest_lon)

        # Verified true great-circle distance between Guwahati (26.1445, 91.7362)
        # and Shillong (25.5788, 91.8933) is ~64.84 km.
        assert 63.0 <= dist <= 67.0, (
            f"Expected ~64.8 km Guwahati→Shillong, got {dist:.3f} km"
        )

    def test_identical_coordinates_returns_zero(self):
        """haversine_km with identical start and end must return exactly 0."""
        dist = haversine_km(25.5788, 91.8933, 25.5788, 91.8933)
        assert dist == pytest.approx(0.0, abs=1e-9)

    def test_antipodal_distance(self):
        """
        Antipodal points (North Pole → South Pole) must return approximately
        half the Earth's circumference: ~20 015 km.
        Tolerance: ±5 km.
        """
        dist = haversine_km(90.0, 0.0, -90.0, 0.0)
        assert 20010.0 <= dist <= 20020.0, (
            f"Expected ~20 015 km for antipodal points, got {dist:.3f} km"
        )

    def test_symmetry(self):
        """Distance A→B must equal distance B→A."""
        a_lat, a_lon = 26.1445, 91.7362
        b_lat, b_lon = 25.5788, 91.8933

        assert haversine_km(a_lat, a_lon, b_lat, b_lon) == pytest.approx(
            haversine_km(b_lat, b_lon, a_lat, a_lon), rel=1e-9
        )

    def test_short_intra_city_distance(self):
        """
        Two points 0.01° apart in latitude (≈1.1 km) should produce a
        distance between 1 km and 2 km.
        """
        dist = haversine_km(26.0000, 91.7000, 26.0100, 91.7000)
        assert 1.0 <= dist <= 2.0, f"Short intra-city distance out of expected range: {dist:.3f} km"

    def test_result_is_non_negative(self):
        """Distance must always be non-negative."""
        dist = haversine_km(20.0, 85.0, 28.0, 97.0)
        assert dist >= 0.0


# ============================================================================
# calculate_air_route validation tests
# ============================================================================

class TestCalculateAirRoute:
    """Input validation and result structure of calculate_air_route()."""

    def test_valid_inputs_return_correct_structure(self):
        """A valid request must return all required keys with correct types."""
        result = calculate_air_route(26.1445, 91.7362, 25.5788, 91.8933)

        assert result["transport_mode"] == "AIRWAY"
        assert result["route_type"]     == "DIRECT_AIR_DISTANCE"
        assert isinstance(result["distance_km"], float)
        assert result["distance_km"] > 0.0
        assert isinstance(result["coords"], list)
        assert len(result["coords"]) == 2
        assert result["eta_available"] is False
        assert "disclaimer" in result
        assert len(result["disclaimer"]) > 0

    def test_distance_matches_haversine(self):
        """distance_km in the result must match the raw haversine_km() value."""
        lat1, lon1 = 26.1445, 91.7362
        lat2, lon2 = 25.5788, 91.8933

        result = calculate_air_route(lat1, lon1, lat2, lon2)
        expected = round(haversine_km(lat1, lon1, lat2, lon2), 3)

        assert result["distance_km"] == expected

    def test_coords_are_origin_and_destination(self):
        """The coords list must be [[origin_lat, origin_lon], [dest_lat, dest_lon]]."""
        lat1, lon1 = 26.1445, 91.7362
        lat2, lon2 = 25.5788, 91.8933

        result = calculate_air_route(lat1, lon1, lat2, lon2)

        assert result["coords"][0] == [lat1, lon1]
        assert result["coords"][1] == [lat2, lon2]

    def test_identical_endpoints_raise_error(self):
        """Identical origin and destination must raise AirwayValidationError."""
        with pytest.raises(AirwayValidationError, match="identical"):
            calculate_air_route(26.1445, 91.7362, 26.1445, 91.7362)

    def test_latitude_out_of_range_raises_error(self):
        """Latitude > 90 must raise AirwayValidationError."""
        with pytest.raises(AirwayValidationError):
            calculate_air_route(91.0, 91.7362, 25.5788, 91.8933)

    def test_latitude_below_range_raises_error(self):
        """Latitude < -90 must raise AirwayValidationError."""
        with pytest.raises(AirwayValidationError):
            calculate_air_route(-91.0, 91.7362, 25.5788, 91.8933)

    def test_longitude_out_of_range_raises_error(self):
        """Longitude > 180 must raise AirwayValidationError."""
        with pytest.raises(AirwayValidationError):
            calculate_air_route(26.1445, 181.0, 25.5788, 91.8933)

    def test_invalid_nan_latitude_raises_error(self):
        """NaN latitude must raise AirwayValidationError."""
        with pytest.raises(AirwayValidationError):
            calculate_air_route(float("nan"), 91.7362, 25.5788, 91.8933)

    def test_invalid_inf_longitude_raises_error(self):
        """Infinite longitude must raise AirwayValidationError."""
        with pytest.raises(AirwayValidationError):
            calculate_air_route(26.1445, float("inf"), 25.5788, 91.8933)

    def test_disclaimer_text_mentions_not_a_flight_route(self):
        """The disclaimer must explicitly state it is not a verified flight route."""
        result = calculate_air_route(26.1445, 91.7362, 25.5788, 91.8933)
        assert "not a verified flight route" in result["disclaimer"]
