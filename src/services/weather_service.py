import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "").strip()
OPENWEATHER_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"

def get_weather_for_location(lat: float, lon: float, default_rainfall: float = 80.0) -> Dict[str, Any]:
    """
    Retrieve live weather observation using OpenWeatherMap API if WEATHER_API_KEY is configured.
    Otherwise gracefully falls back to dataset climatology.
    """
    if WEATHER_API_KEY:
        try:
            params = {
                "lat": lat,
                "lon": lon,
                "appid": WEATHER_API_KEY,
                "units": "metric"
            }
            response = requests.get(OPENWEATHER_ENDPOINT, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                temp = data.get("main", {}).get("temp", 24.0)
                humidity = data.get("main", {}).get("humidity", 80.0)
                rain_dict = data.get("rain", {})
                rain_1h = rain_dict.get("1h", 0.0)
                rain_3h = rain_dict.get("3h", 0.0)
                rain_mm = max(rain_1h * 24.0, rain_3h * 8.0, 5.0) # Estimated 24h daily rate

                return {
                    "source": "Live OpenWeatherMap API",
                    "temperature_c": temp,
                    "humidity_pct": humidity,
                    "rainfall_mm": rain_mm,
                    "is_live": True,
                    "message": "Live weather telemetry active."
                }
        except Exception as e:
            pass # Fall back to dataset climatology on any network error

    return {
        "source": "Historical Dataset Climatology",
        "temperature_c": 24.5,
        "humidity_pct": 82.0,
        "rainfall_mm": default_rainfall,
        "is_live": False,
        "message": "Live weather unavailable. Using historical/dataset weather information."
    }
