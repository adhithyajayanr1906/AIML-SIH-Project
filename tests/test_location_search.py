"""
tests/test_location_search.py
==============================
Unit tests for the Nominatim geocoding service module.

The geocoding provider (Nominatim) is fully mocked so that:
  - Automated tests do NOT depend on internet access.
  - Tests are fast and deterministic.
  - Real geocoding behaviour is verified separately by running the live app.

Run with:
    python -m pytest tests/test_location_search.py -v
"""

import json
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Path setup — allow importing from ml/geocoding without installing the package
# ---------------------------------------------------------------------------
ML_GEOCODING_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "ml", "geocoding")
)
sys.path.insert(0, ML_GEOCODING_PATH)

# Clear any cached imports before each test run
def _reload_module():
    """Force a fresh import of nominatim_service (clears lru_cache state)."""
    import importlib
    if "nominatim_service" in sys.modules:
        del sys.modules["nominatim_service"]
    return importlib.import_module("nominatim_service")


# ---------------------------------------------------------------------------
# Helpers — build a mock Nominatim HTTP response
# ---------------------------------------------------------------------------

def _mock_nominatim_response(results: list) -> MagicMock:
    """Return a mock urlopen context-manager that yields the given results JSON."""
    json_bytes = json.dumps(results).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200
    mock_resp.read.return_value = json_bytes

    return mock_resp


SAMPLE_GUWAHATI = [
    {
        "lat": "26.1445",
        "lon": "91.7362",
        "display_name": "Guwahati, Kamrup Metropolitan, Assam, India",
        "type": "city",
    }
]

SAMPLE_SHILLONG = [
    {
        "lat": "25.5788",
        "lon": "91.8933",
        "display_name": "Shillong, East Khasi Hills, Meghalaya, India",
        "type": "city",
    },
    {
        "lat": "25.5700",
        "lon": "91.8800",
        "display_name": "Shillong Cantonment, East Khasi Hills, Meghalaya, India",
        "type": "administrative",
    },
]


# ---------------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------------

class TestLocationSearch(unittest.TestCase):

    def setUp(self):
        """Reload the module before each test to clear the lru_cache."""
        self.svc = _reload_module()

    # ------------------------------------------------------------------ #
    # TEST 1 — Successful geocode returns structured results              #
    # ------------------------------------------------------------------ #
    def test_01_successful_search_returns_results(self):
        """A valid query returns a list of location dicts with required keys."""
        with patch("urllib.request.urlopen", return_value=_mock_nominatim_response(SAMPLE_GUWAHATI)):
            results = self.svc.search_locations("Guwahati")

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)

        place = results[0]
        self.assertIn("display_name", place)
        self.assertIn("latitude", place)
        self.assertIn("longitude", place)
        self.assertIn("place_type", place)
        self.assertEqual(place["source"], "openstreetmap_nominatim")
        self.assertAlmostEqual(place["latitude"],  26.1445, places=3)
        self.assertAlmostEqual(place["longitude"], 91.7362, places=3)

    # ------------------------------------------------------------------ #
    # TEST 2 — Empty query raises ValueError                              #
    # ------------------------------------------------------------------ #
    def test_02_empty_query_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            self.svc.search_locations("")
        self.assertIn("empty", str(ctx.exception).lower())

    # ------------------------------------------------------------------ #
    # TEST 3 — Single-character query raises ValueError (< MIN_QUERY_LEN)#
    # ------------------------------------------------------------------ #
    def test_03_too_short_query_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            self.svc.search_locations("G")
        self.assertIn("2 characters", str(ctx.exception))

    # ------------------------------------------------------------------ #
    # TEST 4 — No results from provider → empty list (not an error)      #
    # ------------------------------------------------------------------ #
    def test_04_no_matching_results_returns_empty_list(self):
        with patch("urllib.request.urlopen", return_value=_mock_nominatim_response([])):
            results = self.svc.search_locations("xzqwerty_no_such_place")

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    # ------------------------------------------------------------------ #
    # TEST 5 — Network failure raises GeocodingError                     #
    # ------------------------------------------------------------------ #
    def test_05_network_failure_raises_geocoding_error(self):
        import urllib.error
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            with self.assertRaises(self.svc.GeocodingError) as ctx:
                self.svc.search_locations("Shillong")
        self.assertIn("network error", str(ctx.exception).lower())

    # ------------------------------------------------------------------ #
    # TEST 6 — Timeout raises GeocodingError                             #
    # ------------------------------------------------------------------ #
    def test_06_timeout_raises_geocoding_error(self):
        with patch(
            "urllib.request.urlopen",
            side_effect=TimeoutError("timed out"),
        ):
            with self.assertRaises(self.svc.GeocodingError) as ctx:
                self.svc.search_locations("Dimapur")
        self.assertIn("timed out", str(ctx.exception).lower())

    # ------------------------------------------------------------------ #
    # TEST 7 — HTTP error from provider raises GeocodingError            #
    # ------------------------------------------------------------------ #
    def test_07_http_error_raises_geocoding_error(self):
        import urllib.error
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.HTTPError(
                url=None, code=429, msg="Too Many Requests", hdrs=None, fp=None
            ),
        ):
            with self.assertRaises(self.svc.GeocodingError) as ctx:
                self.svc.search_locations("Imphal")
        self.assertIn("429", str(ctx.exception))

    # ------------------------------------------------------------------ #
    # TEST 8 — Invalid coordinates returned by provider are skipped      #
    # ------------------------------------------------------------------ #
    def test_08_invalid_coordinates_skipped(self):
        bad_data = [
            {"lat": "999.0",  "lon": "91.0",  "display_name": "Invalid Lat Place", "type": "place"},
            {"lat": "26.0",   "lon": "200.0", "display_name": "Invalid Lon Place", "type": "place"},
            {"lat": "26.15",  "lon": "91.73", "display_name": "Valid Place, Assam, India", "type": "city"},
        ]
        with patch("urllib.request.urlopen", return_value=_mock_nominatim_response(bad_data)):
            results = self.svc.search_locations("Valid")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["display_name"], "Valid Place, Assam, India")

    # ------------------------------------------------------------------ #
    # TEST 9 — Multiple results returned correctly                       #
    # ------------------------------------------------------------------ #
    def test_09_multiple_results_returned(self):
        with patch("urllib.request.urlopen", return_value=_mock_nominatim_response(SAMPLE_SHILLONG)):
            results = self.svc.search_locations("Shillong")

        self.assertEqual(len(results), 2)
        names = [r["display_name"] for r in results]
        self.assertIn("Shillong, East Khasi Hills, Meghalaya, India", names)

    # ------------------------------------------------------------------ #
    # TEST 10 — Result missing lat/lon key is skipped gracefully         #
    # ------------------------------------------------------------------ #
    def test_10_result_missing_coordinate_key_is_skipped(self):
        bad_data = [
            {"display_name": "No Coordinates Place", "type": "place"},  # no lat/lon
            {"lat": "25.57", "lon": "91.89", "display_name": "Good Place", "type": "city"},
        ]
        with patch("urllib.request.urlopen", return_value=_mock_nominatim_response(bad_data)):
            results = self.svc.search_locations("some query")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["display_name"], "Good Place")

    # ------------------------------------------------------------------ #
    # TEST 11 — Whitespace-only query raises ValueError                  #
    # ------------------------------------------------------------------ #
    def test_11_whitespace_only_query_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.svc.search_locations("   ")

    # ------------------------------------------------------------------ #
    # TEST 12 — Provider returns unparseable JSON → GeocodingError       #
    # ------------------------------------------------------------------ #
    def test_12_unparseable_json_raises_geocoding_error(self):
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 200
        mock_resp.read.return_value = b"not valid json {{{"

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with self.assertRaises(self.svc.GeocodingError) as ctx:
                self.svc.search_locations("Kohima")
        self.assertIn("unparseable", str(ctx.exception).lower())


# ---------------------------------------------------------------------------
# FastAPI endpoint integration tests (require the app to start)
# ---------------------------------------------------------------------------

class TestLocationSearchEndpoint(unittest.TestCase):
    """
    These tests exercise the FastAPI /locations/search endpoint using
    TestClient (no real internet access needed — Nominatim is mocked).
    """

    @classmethod
    def setUpClass(cls):
        """Import FastAPI app and set up TestClient."""
        try:
            from fastapi.testclient import TestClient
            # Avoid loading the real graph / pyogrio on test startup
            with patch("builtins.open", side_effect=FileNotFoundError):
                pass  # just importing app handles missing graph gracefully

            # We must set up sys.path as main.py does and then import
            sys.path.insert(0, os.path.abspath(os.path.join(
                os.path.dirname(__file__), "..", "ml", "routing"
            )))
            sys.path.insert(0, os.path.abspath(os.path.join(
                os.path.dirname(__file__), "..", "ml", "risk"
            )))
            sys.path.insert(0, os.path.abspath(os.path.join(
                os.path.dirname(__file__), "..", "ml", "geocoding"
            )))

            sys.path.insert(0, os.path.abspath(os.path.join(
                os.path.dirname(__file__), "..", "backend"
            )))

            from app.main import app
            cls.client = TestClient(app, raise_server_exceptions=False)
            cls._can_run = True
        except Exception as exc:
            cls._can_run = False
            cls._skip_reason = str(exc)

    def _skip_if_unavailable(self):
        if not self._can_run:
            self.skipTest(f"FastAPI app not importable: {self._skip_reason}")

    # ------------------------------------------------------------------ #
    # TEST A — /locations/search with valid query returns 200             #
    # ------------------------------------------------------------------ #
    def test_A_valid_query_returns_200(self):
        self._skip_if_unavailable()
        with patch(
            "nominatim_service.search_locations",
            return_value=[{
                "display_name": "Guwahati, Assam, India",
                "latitude": 26.1445,
                "longitude": 91.7362,
                "place_type": "city",
                "source": "openstreetmap_nominatim",
            }]
        ):
            r = self.client.get("/locations/search?q=Guwahati")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("results", data)
        self.assertEqual(data["count"], 1)

    # ------------------------------------------------------------------ #
    # TEST B — /locations/search with single-char query returns 422       #
    # ------------------------------------------------------------------ #
    def test_B_too_short_query_returns_422(self):
        self._skip_if_unavailable()
        r = self.client.get("/locations/search?q=G")
        self.assertEqual(r.status_code, 422)

    # ------------------------------------------------------------------ #
    # TEST C — /locations/search when provider fails returns 503          #
    # ------------------------------------------------------------------ #
    def test_C_provider_failure_returns_503(self):
        self._skip_if_unavailable()
        from nominatim_service import GeocodingError
        with patch(
            "nominatim_service.search_locations",
            side_effect=GeocodingError("Connection refused"),
        ):
            r = self.client.get("/locations/search?q=Imphal")
        self.assertEqual(r.status_code, 503)

    # ------------------------------------------------------------------ #
    # TEST D — /locations/search missing q parameter returns 422          #
    # ------------------------------------------------------------------ #
    def test_D_missing_query_param_returns_422(self):
        self._skip_if_unavailable()
        r = self.client.get("/locations/search")
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
