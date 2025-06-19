"""
Tests for data models (dataclasses)
"""

import pytest
from datetime import datetime
from src.storm_radar.models import WeatherStation, WeatherData, MarineData, LightningData


class TestWeatherStation:
    """Test cases for WeatherStation dataclass"""

    def test_weather_station_creation(self):
        """Test basic WeatherStation creation"""
        station = WeatherStation(
            name="TestStation",
            lat=43.6167,
            lon=13.4000,
            distance_km=10.5,
            direction="NE",
            priority=1,
            station_type="coastal",
        )

        assert station.name == "TestStation"
        assert station.lat == 43.6167
        assert station.lon == 13.4000
        assert station.distance_km == 10.5
        assert station.direction == "NE"
        assert station.priority == 1
        assert station.station_type == "coastal"

    def test_weather_station_default_station_type(self):
        """Test WeatherStation with default station_type"""
        station = WeatherStation("Test", 43.0, 13.0, 10, "N", 1)

        assert station.station_type == "inland"  # Default value

    def test_weather_station_equality(self):
        """Test WeatherStation equality comparison"""
        station1 = WeatherStation("Test", 43.0, 13.0, 10, "N", 1, "coastal")
        station2 = WeatherStation("Test", 43.0, 13.0, 10, "N", 1, "coastal")
        station3 = WeatherStation("Different", 43.0, 13.0, 10, "N", 1, "coastal")

        assert station1 == station2
        assert station1 != station3

    def test_weather_station_repr(self):
        """Test WeatherStation string representation"""
        station = WeatherStation("TestStation", 43.6167, 13.4000, 10.5, "NE", 1, "coastal")
        repr_str = repr(station)

        assert "WeatherStation" in repr_str
        assert "TestStation" in repr_str
        assert "43.6167" in repr_str
        assert "coastal" in repr_str


class TestWeatherData:
    """Test cases for WeatherData dataclass"""

    def test_weather_data_creation(self):
        """Test basic WeatherData creation"""
        timestamp = datetime.now()
        data = WeatherData(
            station_name="TestStation",
            timestamp=timestamp,
            temperature=18.5,
            pressure=1015.0,
            humidity=72,
            wind_speed=25.3,
            wind_direction=225.0,
        )

        assert data.station_name == "TestStation"
        assert data.timestamp == timestamp
        assert data.temperature == 18.5
        assert data.pressure == 1015.0
        assert data.humidity == 72
        assert data.wind_speed == 25.3
        assert data.wind_direction == 225.0

        # Check default values
        assert data.visibility is None
        assert data.weather_main == ""
        assert data.station_type == "inland"

    def test_weather_data_with_optional_fields(self):
        """Test WeatherData with all optional fields"""
        timestamp = datetime.now()
        data = WeatherData(
            station_name="TestStation",
            timestamp=timestamp,
            temperature=18.5,
            pressure=1015.0,
            humidity=72,
            wind_speed=25.3,
            wind_direction=225.0,
            visibility=10000.0,
            weather_main="Clear",
            station_type="coastal",
        )

        assert data.visibility == 10000.0
        assert data.weather_main == "Clear"
        assert data.station_type == "coastal"

    def test_weather_data_equality(self):
        """Test WeatherData equality comparison"""
        timestamp = datetime.now()
        data1 = WeatherData("Test", timestamp, 18.0, 1015, 70, 25, 180)
        data2 = WeatherData("Test", timestamp, 18.0, 1015, 70, 25, 180)
        data3 = WeatherData("Different", timestamp, 18.0, 1015, 70, 25, 180)

        assert data1 == data2
        assert data1 != data3


class TestMarineData:
    """Test cases for MarineData dataclass"""

    def test_marine_data_creation(self):
        """Test basic MarineData creation"""
        timestamp = datetime.now()
        data = MarineData(
            timestamp=timestamp,
            wave_height=2.5,
            wave_period=6.0,
            wave_direction=90.0,
            sea_temperature=16.5,
            location="TestLocation",
        )

        assert data.timestamp == timestamp
        assert data.wave_height == 2.5
        assert data.wave_period == 6.0
        assert data.wave_direction == 90.0
        assert data.sea_temperature == 16.5
        assert data.location == "TestLocation"

    def test_marine_data_edge_values(self):
        """Test MarineData with edge values"""
        timestamp = datetime.now()
        data = MarineData(
            timestamp=timestamp,
            wave_height=0.0,  # Calm sea
            wave_period=2.0,  # Very short period
            wave_direction=360.0,  # Full circle
            sea_temperature=0.0,  # Freezing
            location="Arctic",
        )

        assert data.wave_height == 0.0
        assert data.wave_period == 2.0
        assert data.wave_direction == 360.0
        assert data.sea_temperature == 0.0

    def test_marine_data_repr(self):
        """Test MarineData string representation"""
        timestamp = datetime.now()
        data = MarineData(timestamp, 2.5, 6.0, 90.0, 16.5, "TestLocation")
        repr_str = repr(data)

        assert "MarineData" in repr_str
        assert "2.5" in repr_str
        assert "TestLocation" in repr_str


class TestLightningData:
    """Test cases for LightningData dataclass"""

    def test_lightning_data_creation(self):
        """Test basic LightningData creation"""
        timestamp = datetime.now()
        data = LightningData(
            timestamp=timestamp, lat=43.5, lon=13.3, distance_km=25.5, intensity=85.0
        )

        assert data.timestamp == timestamp
        assert data.lat == 43.5
        assert data.lon == 13.3
        assert data.distance_km == 25.5
        assert data.intensity == 85.0

    def test_lightning_data_zero_distance(self):
        """Test LightningData with zero distance (direct hit)"""
        timestamp = datetime.now()
        data = LightningData(timestamp, 43.6167, 13.4000, 0.0, 100.0)

        assert data.distance_km == 0.0
        assert data.intensity == 100.0

    def test_lightning_data_far_distance(self):
        """Test LightningData with far distance"""
        timestamp = datetime.now()
        data = LightningData(timestamp, 45.0, 15.0, 500.0, 30.0)

        assert data.distance_km == 500.0
        assert data.intensity == 30.0

    def test_lightning_data_equality(self):
        """Test LightningData equality comparison"""
        timestamp = datetime.now()
        data1 = LightningData(timestamp, 43.5, 13.3, 25.0, 85.0)
        data2 = LightningData(timestamp, 43.5, 13.3, 25.0, 85.0)
        data3 = LightningData(timestamp, 43.6, 13.3, 25.0, 85.0)  # Different lat

        assert data1 == data2
        assert data1 != data3


class TestDataModelInteractions:
    """Test interactions between different data models"""

    def test_data_model_timestamps_consistency(self):
        """Test that all models handle timestamps consistently"""
        timestamp = datetime.now()

        weather = WeatherData("Station", timestamp, 18.0, 1015, 70, 25, 180)
        marine = MarineData(timestamp, 2.0, 6.0, 90, 16.0, "Location")
        lightning = LightningData(timestamp, 43.5, 13.3, 25.0, 85.0)

        # All should have the same timestamp
        assert weather.timestamp == marine.timestamp == lightning.timestamp

    def test_coordinate_consistency(self):
        """Test coordinate handling across models"""
        station = WeatherStation("Test", 43.6167, 13.4000, 10, "N", 1)
        lightning = LightningData(datetime.now(), 43.6167, 13.4000, 0.0, 100.0)

        # Coordinates should match
        assert station.lat == lightning.lat
        assert station.lon == lightning.lon

    def test_data_model_type_validation(self):
        """Test that models accept expected data types"""
        # Test numeric types
        timestamp = datetime.now()

        # Should accept both int and float for numeric fields
        weather_int = WeatherData("Test", timestamp, 18, 1015, 70, 25, 180)  # int values
        weather_float = WeatherData(
            "Test", timestamp, 18.5, 1015.2, 70.1, 25.3, 180.5
        )  # float values

        assert isinstance(weather_int.temperature, (int, float))
        assert isinstance(weather_float.temperature, (int, float))

    def test_data_model_immutability(self):
        """Test that dataclass fields can be accessed and modified if needed"""
        station = WeatherStation("Test", 43.0, 13.0, 10, "N", 1)

        # Fields should be accessible
        assert station.name == "Test"

        # Should be able to modify (dataclasses are mutable by default)
        station.name = "Modified"
        assert station.name == "Modified"

    def test_optional_fields_behavior(self):
        """Test behavior of optional fields across models"""
        timestamp = datetime.now()

        # WeatherData with minimal fields
        weather = WeatherData("Station", timestamp, 18.0, 1015, 70, 25, 180)
        assert weather.visibility is None
        assert weather.weather_main == ""
        assert weather.station_type == "inland"

        # Test setting optional fields
        weather_full = WeatherData(
            "Station",
            timestamp,
            18.0,
            1015,
            70,
            25,
            180,
            visibility=10000,
            weather_main="Clear",
            station_type="coastal",
        )
        assert weather_full.visibility == 10000
        assert weather_full.weather_main == "Clear"
        assert weather_full.station_type == "coastal"
