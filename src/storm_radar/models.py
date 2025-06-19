"""
Data models for the Storm Radar weather alert system
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WeatherStation:
    """Weather station configuration"""

    name: str
    lat: float
    lon: float
    distance_km: float
    direction: str
    priority: int
    station_type: str = "inland"  # inland, coastal, mountain


@dataclass
class WeatherData:
    """Weather data structure"""

    station_name: str
    timestamp: datetime
    temperature: float
    pressure: float
    humidity: float
    wind_speed: float
    wind_direction: float
    visibility: Optional[float] = None
    weather_main: str = ""
    station_type: str = "inland"


@dataclass
class MarineData:
    """Marine data structure"""

    timestamp: datetime
    wave_height: float
    wave_period: float
    wave_direction: float
    sea_temperature: float
    location: str


@dataclass
class LightningData:
    """Lightning strike data"""

    timestamp: datetime
    lat: float
    lon: float
    distance_km: float
    intensity: float
