"""
Storm Radar - Enhanced Weather Alert System for Falconara Marittima
"""

from .models import WeatherStation, WeatherData, MarineData, LightningData
from .config import Configuration
from .fetchers import WeatherDataFetcher
from .calculators import EnhancedAlertCalculator
from .notifiers import TelegramNotifier
from .main import EnhancedWeatherAlertSystem, main
from .logging import logger, WeatherLogger

__version__ = "1.0.0"
__author__ = "Storm Radar Team"

__all__ = [
    # Data models
    "WeatherStation",
    "WeatherData",
    "MarineData",
    "LightningData",
    # Core components
    "Configuration",
    "WeatherDataFetcher",
    "EnhancedAlertCalculator",
    "TelegramNotifier",
    # Main system
    "EnhancedWeatherAlertSystem",
    "main",
    # Logging
    "logger",
    "WeatherLogger",
]
