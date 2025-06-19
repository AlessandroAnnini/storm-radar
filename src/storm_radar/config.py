"""
Configuration settings for the Storm Radar weather alert system
"""

import os
from dotenv import load_dotenv
from .models import WeatherStation

# Load environment variables from .env file
load_dotenv()


class Configuration:
    """Enhanced system configuration"""

    # API Keys (loaded from environment variables)
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "YOUR_OPENWEATHER_API_KEY_HERE")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID_HERE")

    # Falconara Marittima coordinates
    TARGET_LAT = 43.6167
    TARGET_LON = 13.4000

    # Enhanced weather stations for Bora detection
    STATIONS = [
        # ===== BORA DETECTION STATIONS (CRITICAL) =====
        WeatherStation("Trieste", 45.6469, 13.7780, 150, "NE", 1, "coastal"),
        WeatherStation("Nova_Gorica", 45.9564, 13.6581, 140, "NE", 1, "mountain"),
        WeatherStation("Rijeka", 45.3431, 14.4078, 180, "NE", 1, "coastal"),
        # ===== APENNINE STORM FORMATION (HIGH PRIORITY) =====
        WeatherStation("Gubbio", 43.3506, 12.5781, 60, "SW", 1, "mountain"),
        WeatherStation("Foligno", 42.9563, 12.7033, 70, "SW", 1, "inland"),
        WeatherStation("Fabriano", 43.3359, 12.9044, 45, "W", 1, "mountain"),
        # ===== COASTAL TRACKING (MEDIUM PRIORITY) =====
        WeatherStation("Pesaro", 43.9073, 12.8946, 35, "N", 2, "coastal"),
        WeatherStation("Fano", 43.8433, 13.0172, 25, "NW", 2, "coastal"),
        WeatherStation("Ancona", 43.6167, 13.4000, 5, "LOCAL", 1, "coastal"),
        WeatherStation("Macerata", 43.3007, 13.4527, 35, "S", 2, "inland"),
        # ===== THERMAL GRADIENT MONITORING =====
        WeatherStation("Rimini", 44.0527, 12.5664, 60, "N", 3, "coastal"),
        WeatherStation("Bologna", 44.4949, 11.3426, 120, "NW", 3, "inland"),
    ]

    # Marine monitoring points
    MARINE_POINTS = [
        {"name": "Falconara_Offshore", "lat": 43.7, "lon": 13.6},
        {"name": "Ancona_Bay", "lat": 43.6, "lon": 13.5},
        {"name": "Rimini_Offshore", "lat": 44.1, "lon": 12.8},
    ]

    # Lightning monitoring areas (km radius)
    LIGHTNING_AREAS = [
        {"name": "West_Apennines", "radius": 100, "priority": 1},
        {"name": "Alpine_Approach", "radius": 120, "priority": 2},
        {"name": "Immediate_Area", "radius": 50, "priority": 1},
    ]

    # ===== ENHANCED ALERT THRESHOLDS =====

    # Bora detection thresholds
    BORA_PRESSURE_DIFF_THRESHOLD = 10.0  # hPa difference between NE and local
    BORA_WIND_THRESHOLD = 40.0  # km/h from NE

    # Standard weather thresholds
    PRESSURE_DROP_THRESHOLD = 3.0  # hPa in 3 hours
    WIND_INCREASE_THRESHOLD = 15.0  # km/h increase
    HIGH_WIND_THRESHOLD = 35.0  # km/h sustained

    # Marine thresholds
    WAVE_HEIGHT_THRESHOLD = 2.0  # meters
    WAVE_PERIOD_THRESHOLD = 4.0  # seconds (short period = storm)

    # Lightning thresholds
    LIGHTNING_DENSITY_THRESHOLD = 10  # strikes per 10 minutes
    LIGHTNING_APPROACH_DISTANCE = 100  # km

    # Thermal gradient thresholds
    THERMAL_GRADIENT_THRESHOLD = 8.0  # °C difference inland vs coastal

    # Notification settings
    MIN_ALERT_LEVEL = os.getenv("MIN_ALERT_LEVEL", "MEDIUM")  # Minimum level to send notifications

    # System settings (with environment variable overrides)
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "1800"))  # 30 minutes
    DATA_RETENTION_HOURS = int(os.getenv("DATA_RETENTION_HOURS", "12"))
