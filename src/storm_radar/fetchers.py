"""
Data fetchers for weather, marine, and lightning data
"""

import requests
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .models import WeatherStation, WeatherData, MarineData, LightningData
from .logging import logger


class WeatherDataFetcher:
    """Enhanced weather data fetcher with marine and lightning data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.weather_url = "http://api.openweathermap.org/data/2.5/weather"
        self.marine_url = "https://marine-api.open-meteo.com/v1/marine"
        self.lightning_url = "https://api.blitzortung.org/v1/strikes"  # Free lightning API

    def fetch_station_data(self, station: WeatherStation) -> Optional[WeatherData]:
        """Fetch current weather data for a station"""
        try:
            params = {
                "lat": station.lat,
                "lon": station.lon,
                "appid": self.api_key,
                "units": "metric",
            }

            response = requests.get(self.weather_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            weather_data = WeatherData(
                station_name=station.name,
                timestamp=datetime.now(),
                temperature=data["main"]["temp"],
                pressure=data["main"]["pressure"],
                humidity=data["main"]["humidity"],
                wind_speed=data["wind"]["speed"] * 3.6,  # Convert m/s to km/h
                wind_direction=data["wind"].get("deg", 0),
                visibility=data.get("visibility", None),
                weather_main=data["weather"][0]["main"],
                station_type=station.station_type,
            )

            logger.log_debug(
                f"Fetched weather data for {station.name}",
                {
                    "temperature": f"{weather_data.temperature:.1f}°C",
                    "wind_speed": f"{weather_data.wind_speed:.1f} km/h",
                    "pressure": f"{weather_data.pressure:.0f} hPa",
                },
            )

            return weather_data

        except Exception as e:
            logger.log_api_error("OpenWeatherMap", str(e), station.name)
            return None

    def fetch_marine_data(self, point: Dict) -> Optional[MarineData]:
        """Fetch marine data from Open-Meteo (free)"""
        try:
            params = {
                "latitude": point["lat"],
                "longitude": point["lon"],
                "hourly": "wave_height,wave_period,wave_direction,ocean_current_velocity",
                "forecast_days": 1,
            }

            response = requests.get(self.marine_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Get current hour data
            current_hour = datetime.now().hour
            hourly = data.get("hourly", {})

            marine_data = MarineData(
                timestamp=datetime.now(),
                wave_height=hourly.get("wave_height", [0])[current_hour] or 0,
                wave_period=hourly.get("wave_period", [8])[current_hour] or 8,
                wave_direction=hourly.get("wave_direction", [0])[current_hour] or 0,
                sea_temperature=20.0,  # Default - Open-Meteo doesn't provide this
                location=point["name"],
            )

            logger.log_debug(
                f"Fetched marine data for {point['name']}",
                {
                    "wave_height": f"{marine_data.wave_height:.1f}m",
                    "wave_period": f"{marine_data.wave_period:.0f}s",
                    "location": marine_data.location,
                },
            )

            return marine_data

        except Exception as e:
            logger.log_api_error("Open-Meteo Marine", str(e), point["name"])
            return None

    def fetch_lightning_data(self, radius_km: int = 100) -> List[LightningData]:
        """Fetch lightning strikes from free sources"""
        try:
            # Note: This is a simplified implementation
            # Real implementation would use Blitzortung.org or similar free API
            # For now, return empty list - you'd need to implement specific API integration

            # Blitzortung.org provides free data but requires special integration
            # Alternative: scrape from public lightning maps or use other free sources

            logger.log_debug("Lightning data fetch - using placeholder data")
            return []  # Placeholder - implement based on available free API

        except Exception as e:
            logger.log_api_error("Lightning API", str(e))
            return []

    def fetch_all_data(
        self, stations: List[WeatherStation], marine_points: List[Dict]
    ) -> Tuple[List[WeatherData], List[MarineData], List[LightningData]]:
        """Fetch all weather, marine, and lightning data"""

        # Fetch weather data
        logger.log_fetch_start("weather", len(stations))
        weather_data = []
        for station in stations:
            data = self.fetch_station_data(station)
            if data:
                weather_data.append(data)
            time.sleep(0.5)  # Rate limiting

        # Log weather data
        if weather_data:
            logger.log_weather_data(weather_data)

        # Fetch marine data
        logger.log_fetch_start("marine", len(marine_points))
        marine_data = []
        for point in marine_points:
            data = self.fetch_marine_data(point)
            if data:
                marine_data.append(data)
            time.sleep(0.5)

        # Log marine data
        if marine_data:
            logger.log_marine_data(marine_data)

        # Fetch lightning data
        logger.log_fetch_start("lightning", 1)
        lightning_data = self.fetch_lightning_data()

        # Log lightning data
        if lightning_data:
            logger.log_lightning_data(lightning_data)

        # Log summary
        logger.log_data_summary(len(weather_data), len(marine_data), len(lightning_data))

        return weather_data, marine_data, lightning_data
