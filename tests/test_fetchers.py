"""
Tests for WeatherDataFetcher class
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.storm_radar.fetchers import WeatherDataFetcher
from src.storm_radar.models import WeatherStation, WeatherData, MarineData


@pytest.fixture
def fetcher():
    """WeatherDataFetcher instance for testing"""
    return WeatherDataFetcher("test_api_key")


@pytest.fixture
def sample_station():
    """Sample weather station for testing"""
    return WeatherStation(
        name="TestStation",
        lat=43.6167,
        lon=13.4000,
        distance_km=10,
        direction="N",
        priority=1,
        station_type="coastal",
    )


@pytest.fixture
def sample_marine_point():
    """Sample marine monitoring point"""
    return {"name": "Test_Offshore", "lat": 43.7, "lon": 13.6}


@pytest.fixture
def mock_weather_api_response():
    """Mock OpenWeatherMap API response"""
    return {
        "main": {"temp": 18.5, "pressure": 1015, "humidity": 72},
        "wind": {"speed": 8.2, "deg": 225},  # m/s
        "weather": [{"main": "Clear"}],
        "visibility": 10000,
    }


@pytest.fixture
def mock_marine_api_response():
    """Mock Open-Meteo marine API response"""
    return {
        "hourly": {
            "wave_height": [1.5, 1.8, 2.1, 2.0] + [1.5] * 20,
            "wave_period": [6.0, 5.8, 5.5, 5.7] + [6.0] * 20,
            "wave_direction": [90, 95, 100, 92] + [90] * 20,
            "ocean_current_velocity": [0.5, 0.6, 0.7, 0.6] + [0.5] * 20,
        }
    }


class TestWeatherDataFetcher:
    """Test cases for WeatherDataFetcher"""

    def test_fetcher_initialization(self):
        """Test fetcher initializes correctly"""
        fetcher = WeatherDataFetcher("test_api_key")

        assert fetcher.api_key == "test_api_key"
        assert "openweathermap.org" in fetcher.weather_url
        assert "open-meteo.com" in fetcher.marine_url
        assert "blitzortung.org" in fetcher.lightning_url

    @patch("requests.get")
    def test_fetch_station_data_success(
        self, mock_get, fetcher, sample_station, mock_weather_api_response
    ):
        """Test successful weather station data fetch"""
        # Setup mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_weather_api_response
        mock_get.return_value = mock_response

        # Fetch data
        result = fetcher.fetch_station_data(sample_station)

        # Verify result
        assert result is not None
        assert isinstance(result, WeatherData)
        assert result.station_name == "TestStation"
        assert result.temperature == 18.5
        assert result.pressure == 1015
        assert result.humidity == 72
        assert result.wind_speed == 8.2 * 3.6  # Converted to km/h
        assert result.wind_direction == 225
        assert result.weather_main == "Clear"
        assert result.station_type == "coastal"

        # Verify API call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "params" in kwargs
        assert kwargs["params"]["lat"] == 43.6167
        assert kwargs["params"]["lon"] == 13.4000
        assert kwargs["params"]["appid"] == "test_api_key"

    @patch("requests.get")
    def test_fetch_station_data_api_error(self, mock_get, fetcher, sample_station):
        """Test weather station data fetch with API error"""
        # Setup mock to raise exception
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        # Fetch data should return None on error
        result = fetcher.fetch_station_data(sample_station)

        assert result is None

    @patch("requests.get")
    def test_fetch_station_data_http_error(self, mock_get, fetcher, sample_station):
        """Test weather station data fetch with HTTP error"""
        # Setup mock response with HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        mock_get.return_value = mock_response

        # Fetch data should return None on error
        result = fetcher.fetch_station_data(sample_station)

        assert result is None

    @patch("requests.get")
    def test_fetch_station_data_missing_wind_direction(self, mock_get, fetcher, sample_station):
        """Test weather station data fetch with missing wind direction"""
        # Setup mock response without wind direction
        incomplete_response = {
            "main": {"temp": 18.5, "pressure": 1015, "humidity": 72},
            "wind": {"speed": 8.2},  # Missing 'deg'
            "weather": [{"main": "Clear"}],
        }

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = incomplete_response
        mock_get.return_value = mock_response

        # Should handle missing data gracefully
        result = fetcher.fetch_station_data(sample_station)

        assert result is not None
        assert result.wind_direction == 0  # Default value

    @patch("requests.get")
    def test_fetch_marine_data_success(
        self, mock_get, fetcher, sample_marine_point, mock_marine_api_response
    ):
        """Test successful marine data fetch"""
        # Setup mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_marine_api_response
        mock_get.return_value = mock_response

        # Mock current hour
        with patch("src.storm_radar.fetchers.datetime") as mock_datetime:
            mock_datetime.now.return_value.hour = 2

            result = fetcher.fetch_marine_data(sample_marine_point)

        # Verify result
        assert result is not None
        assert isinstance(result, MarineData)
        assert result.location == "Test_Offshore"
        assert result.wave_height == 2.1  # Hour 2 data
        assert result.wave_period == 5.5
        assert result.wave_direction == 100
        assert result.sea_temperature == 20.0  # Default value

        # Verify API call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "params" in kwargs
        assert kwargs["params"]["latitude"] == 43.7
        assert kwargs["params"]["longitude"] == 13.6

    @patch("requests.get")
    def test_fetch_marine_data_api_error(self, mock_get, fetcher, sample_marine_point):
        """Test marine data fetch with API error"""
        # Setup mock to raise exception
        mock_get.side_effect = requests.exceptions.RequestException("Marine API Error")

        # Fetch data should return None on error
        result = fetcher.fetch_marine_data(sample_marine_point)

        assert result is None

    @patch("requests.get")
    def test_fetch_marine_data_missing_data(self, mock_get, fetcher, sample_marine_point):
        """Test marine data fetch with missing hourly data"""
        # Setup mock response with missing data
        incomplete_response = {"hourly": {}}

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = incomplete_response
        mock_get.return_value = mock_response

        # Should handle missing data gracefully
        with patch("src.storm_radar.fetchers.datetime") as mock_datetime:
            mock_datetime.now.return_value.hour = 2

            result = fetcher.fetch_marine_data(sample_marine_point)

        assert result is None  # Should return None when data is missing

    def test_fetch_lightning_data_placeholder(self, fetcher):
        """Test lightning data fetch (currently placeholder)"""
        # Current implementation returns empty list
        result = fetcher.fetch_lightning_data()

        assert result == []
        assert isinstance(result, list)

    @patch("requests.get")
    @patch("time.sleep")  # Mock sleep to speed up tests
    def test_fetch_all_data_success(
        self,
        mock_sleep,
        mock_get,
        fetcher,
        sample_station,
        sample_marine_point,
        mock_weather_api_response,
        mock_marine_api_response,
    ):
        """Test fetching all data types successfully"""

        # Setup mock responses for different APIs
        def mock_response_side_effect(url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None

            if "openweathermap" in url:
                mock_response.json.return_value = mock_weather_api_response
            elif "open-meteo" in url:
                mock_response.json.return_value = mock_marine_api_response

            return mock_response

        mock_get.side_effect = mock_response_side_effect

        # Mock current hour for marine data
        with patch("src.storm_radar.fetchers.datetime") as mock_datetime:
            mock_datetime.now.return_value.hour = 1

            weather_data, marine_data, lightning_data = fetcher.fetch_all_data(
                [sample_station], [sample_marine_point]
            )

        # Verify all data types returned
        assert len(weather_data) == 1
        assert len(marine_data) == 1
        assert len(lightning_data) == 0  # Placeholder returns empty

        # Verify data content
        assert isinstance(weather_data[0], WeatherData)
        assert isinstance(marine_data[0], MarineData)

        # Verify rate limiting was applied
        assert mock_sleep.call_count == 2  # Once for weather, once for marine

    @patch("requests.get")
    def test_fetch_all_data_partial_failure(
        self, mock_get, fetcher, sample_station, sample_marine_point
    ):
        """Test fetching all data with some failures"""

        # Setup mock to fail weather but succeed marine
        def mock_response_side_effect(url, **kwargs):
            if "openweathermap" in url:
                raise requests.exceptions.RequestException("Weather API down")
            elif "open-meteo" in url:
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                mock_response.json.return_value = {"hourly": {"wave_height": [1.5] * 24}}
                return mock_response

        mock_get.side_effect = mock_response_side_effect

        weather_data, marine_data, lightning_data = fetcher.fetch_all_data(
            [sample_station], [sample_marine_point]
        )

        # Should handle partial failures gracefully
        assert len(weather_data) == 0  # Failed
        assert len(marine_data) == 0  # Also failed due to missing data
        assert len(lightning_data) == 0

    @patch("requests.get")
    def test_fetch_station_data_timeout(self, mock_get, fetcher, sample_station):
        """Test weather station data fetch with timeout"""
        # Setup mock to timeout
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

        # Should handle timeout gracefully
        result = fetcher.fetch_station_data(sample_station)

        assert result is None

    def test_api_urls_configuration(self, fetcher):
        """Test that API URLs are properly configured"""
        # Check weather API URL
        assert "http://api.openweathermap.org/data/2.5/weather" == fetcher.weather_url

        # Check marine API URL
        assert "https://marine-api.open-meteo.com/v1/marine" == fetcher.marine_url

        # Check lightning API URL (placeholder)
        assert "https://api.blitzortung.org/v1/strikes" == fetcher.lightning_url
