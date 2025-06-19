"""
Tests for the alert calculation and weather pattern analysis module
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.storm_radar.calculators import EnhancedAlertCalculator
from src.storm_radar.config import Configuration
from src.storm_radar.models import WeatherData, MarineData, LightningData


@pytest.fixture
def config():
    """Test configuration"""
    return Configuration()


@pytest.fixture
def calculator(config):
    """Test calculator instance"""
    return EnhancedAlertCalculator(config)


@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing"""
    return [
        WeatherData(
            station_name="Trieste",
            timestamp=datetime.now(),
            temperature=15.0,
            pressure=1020.0,
            humidity=70,
            wind_speed=45.0,
            wind_direction=45,
            station_type="coastal",
        ),
        WeatherData(
            station_name="Ancona",
            timestamp=datetime.now(),
            temperature=18.0,
            pressure=1015.0,
            humidity=65,
            wind_speed=25.0,
            wind_direction=180,
            station_type="coastal",
        ),
        WeatherData(
            station_name="Gubbio",
            timestamp=datetime.now(),
            temperature=12.0,
            pressure=1010.0,
            humidity=80,
            wind_speed=30.0,
            wind_direction=225,
            station_type="mountain",
        ),
    ]


@pytest.fixture
def sample_marine_data():
    """Sample marine data for testing"""
    return [
        MarineData(
            timestamp=datetime.now(),
            wave_height=2.5,  # High waves (> 2.0 threshold)
            wave_period=3.0,  # Short period (< 4.0 threshold)
            wave_direction=90,
            sea_temperature=16.0,
            location="Falconara_Offshore",
        )
    ]


@pytest.fixture
def sample_lightning_data():
    """Sample lightning data for testing"""
    base_time = datetime.now()
    return [
        LightningData(
            timestamp=base_time - timedelta(minutes=5),
            lat=43.5,
            lon=13.3,
            distance_km=50.0,
            intensity=80.0,
        ),
        LightningData(
            timestamp=base_time - timedelta(minutes=3),
            lat=43.4,
            lon=13.2,
            distance_km=45.0,
            intensity=90.0,
        ),
    ]


class TestEnhancedAlertCalculator:
    """Test the enhanced alert calculator"""

    def test_calculator_initialization(self, config):
        """Test calculator initialization"""
        calc = EnhancedAlertCalculator(config)
        assert calc.config == config
        assert calc.historical_weather == {}
        assert calc.historical_marine == {}
        assert calc.historical_lightning == []

    def test_store_data(
        self, calculator, sample_weather_data, sample_marine_data, sample_lightning_data
    ):
        """Test data storage functionality"""
        calculator.store_data(sample_weather_data, sample_marine_data, sample_lightning_data)

        # Check weather data storage
        assert "Trieste" in calculator.historical_weather
        assert len(calculator.historical_weather["Trieste"]) == 1

        # Check marine data storage
        assert "Falconara_Offshore" in calculator.historical_marine
        assert len(calculator.historical_marine["Falconara_Offshore"]) == 1

        # Check lightning data storage
        assert len(calculator.historical_lightning) == 2

    def test_check_bora_pattern_detected(self, calculator, config):
        """Test Bora pattern detection - positive case"""
        # Create conditions for Bora detection
        weather_data = [
            WeatherData(
                "Trieste", datetime.now(), 15.0, 1025.0, 70, 50.0, 45, station_type="coastal"
            ),
            WeatherData(
                "Ancona", datetime.now(), 18.0, 1010.0, 65, 25.0, 180, station_type="coastal"
            ),
        ]

        detected, reason = calculator.check_bora_pattern(weather_data)

        assert detected is True
        assert "BORA PATTERN DETECTED" in reason
        assert "Pressure diff 15.0hPa" in reason

    def test_check_bora_pattern_not_detected(self, calculator):
        """Test Bora pattern detection - negative case"""
        # Normal conditions (no significant pressure diff or wind)
        weather_data = [
            WeatherData(
                "Trieste", datetime.now(), 18.0, 1015.0, 70, 20.0, 45, station_type="coastal"
            ),
            WeatherData(
                "Ancona", datetime.now(), 18.0, 1015.0, 65, 15.0, 180, station_type="coastal"
            ),
        ]

        detected, reason = calculator.check_bora_pattern(weather_data)

        assert detected is False
        assert reason == ""

    def test_calculate_enhanced_alerts_critical(self, calculator, config):
        """Test enhanced alert calculation - critical level (Bora)"""
        # Create Bora conditions with correct station names
        weather_data = [
            WeatherData(
                "Trieste", datetime.now(), 15.0, 1025.0, 70, 50.0, 45, station_type="coastal"
            ),
            WeatherData(
                "Ancona", datetime.now(), 18.0, 1010.0, 65, 25.0, 180, station_type="coastal"
            ),
        ]

        marine_data = []
        lightning_data = []

        score, reasons, alert_level = calculator.calculate_enhanced_alerts(
            weather_data, marine_data, lightning_data
        )

        assert alert_level == "CRITICAL"
        assert score >= 60  # Bora adds 60 points
        assert any("🌪️ BORA" in reason for reason in reasons)

    def test_calculate_enhanced_alerts_medium_with_marine(self, calculator, sample_marine_data):
        """Test enhanced alert calculation - medium level with marine conditions"""
        # Normal weather + marine issues
        normal_weather = [
            WeatherData(
                "Ancona", datetime.now(), 18.0, 1015.0, 65, 25.0, 180, station_type="coastal"
            )
        ]

        lightning_data = []

        score, reasons, alert_level = calculator.calculate_enhanced_alerts(
            normal_weather, sample_marine_data, lightning_data
        )

        assert alert_level in ["LOW", "MEDIUM"]
        assert any("🌊 MARINE" in reason for reason in reasons)
        assert "High waves 2.5m" in str(reasons)
        assert "Short wave period 3.0s" in str(reasons)

    def test_calculate_enhanced_alerts_with_lightning(self, calculator):
        """Test enhanced alert calculation with lightning activity"""
        # Create many recent lightning strikes
        weather_data = [
            WeatherData(
                "Ancona", datetime.now(), 18.0, 1015.0, 65, 25.0, 180, station_type="coastal"
            )
        ]

        # Create 15 recent lightning strikes (above threshold of 10)
        lightning_data = []
        for i in range(15):
            lightning_data.append(
                LightningData(
                    timestamp=datetime.now() - timedelta(minutes=2),
                    lat=43.5,
                    lon=13.3,
                    distance_km=50.0,  # Within approach distance
                    intensity=80.0,
                )
            )

        marine_data = []

        score, reasons, alert_level = calculator.calculate_enhanced_alerts(
            weather_data, marine_data, lightning_data
        )

        assert any("⚡ LIGHTNING" in reason for reason in reasons)
        assert "Lightning approaching" in str(reasons)
        assert "15 strikes" in str(reasons)
        assert score >= 30  # Lightning adds 30 points

    def test_calculate_enhanced_alerts_with_thermal_gradient(self, calculator):
        """Test enhanced alert calculation with thermal gradient"""
        # Create high thermal gradient conditions
        weather_data = [
            WeatherData(
                "Ancona", datetime.now(), 20.0, 1015.0, 70, 20.0, 45, station_type="coastal"
            ),
            WeatherData(
                "Gubbio", datetime.now(), 10.0, 1010.0, 80, 30.0, 225, station_type="inland"
            ),
        ]

        marine_data = []
        lightning_data = []

        score, reasons, alert_level = calculator.calculate_enhanced_alerts(
            weather_data, marine_data, lightning_data
        )

        assert any("🌡️ THERMAL" in reason for reason in reasons)
        assert "High thermal gradient: 10.0°C" in str(reasons)
        assert score >= 15  # Thermal adds 15 points

    def test_calculate_enhanced_alerts_low(self, calculator):
        """Test enhanced alert calculation - low level"""
        # Normal conditions
        normal_weather = [
            WeatherData(
                "Ancona", datetime.now(), 18.0, 1015.0, 65, 15.0, 180, station_type="coastal"
            )
        ]
        normal_marine = [MarineData(datetime.now(), 1.0, 6.0, 90, 16.0, "Falconara_Offshore")]
        lightning_data = []

        score, reasons, alert_level = calculator.calculate_enhanced_alerts(
            normal_weather, normal_marine, lightning_data
        )

        assert alert_level == "LOW"
        assert score < 40

    def test_get_enhanced_eta_bora(self, calculator):
        """Test ETA calculation for Bora conditions"""
        reasons = ["🌪️ BORA: Test"]
        eta = calculator.get_enhanced_eta(reasons, bora_detected=True)

        assert "15-45 minutes" in eta
        assert "IMMEDIATE DANGER" in eta

    def test_get_enhanced_eta_lightning(self, calculator):
        """Test ETA calculation for lightning"""
        reasons = ["⚡ LIGHTNING: Test"]
        eta = calculator.get_enhanced_eta(reasons, bora_detected=False)

        assert "30-60 minutes" in eta

    def test_get_enhanced_eta_marine(self, calculator):
        """Test ETA calculation for marine conditions"""
        reasons = ["🌊 MARINE: Test"]
        eta = calculator.get_enhanced_eta(reasons, bora_detected=False)

        assert "45-90 minutes" in eta

    def test_data_cleanup(self, calculator):
        """Test that old data gets cleaned up"""
        # Create old data (within retention period initially)
        old_data = [
            WeatherData(
                "Trieste",
                datetime.now() - timedelta(hours=6),  # Within retention period
                15.0,
                1020.0,
                70,
                45.0,
                45,
                station_type="coastal",
            )
        ]

        # Store old data first
        calculator.store_data(old_data, [], [])
        assert len(calculator.historical_weather["Trieste"]) == 1

        # Create very old data (beyond retention period)
        very_old_data = [
            WeatherData(
                "Trieste",
                datetime.now() - timedelta(hours=15),  # Beyond retention period
                14.0,
                1025.0,
                65,
                50.0,
                30,
                station_type="coastal",
            )
        ]

        # Store very old data (should be cleaned up immediately due to age)
        calculator.store_data(very_old_data, [], [])

        # Should still have the first old data (6 hours) but not the very old data (15 hours)
        assert len(calculator.historical_weather["Trieste"]) == 1
        remaining_data = calculator.historical_weather["Trieste"][0]
        assert remaining_data.timestamp > datetime.now() - timedelta(hours=10)

    def test_empty_data_handling(self, calculator):
        """Test handling of empty data sets"""
        score, reasons, alert_level = calculator.calculate_enhanced_alerts([], [], [])

        assert score >= 0
        assert alert_level == "LOW"
        assert isinstance(reasons, list)
