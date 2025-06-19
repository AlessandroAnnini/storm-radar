"""
Tests for main system orchestrator and EnhancedWeatherAlertSystem
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.storm_radar.main import EnhancedWeatherAlertSystem, main
from src.storm_radar.models import WeatherData, MarineData


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    with patch("src.storm_radar.main.Configuration") as mock:
        config = Mock()
        config.OPENWEATHER_API_KEY = "test_api_key"
        config.TELEGRAM_BOT_TOKEN = "test_bot_token"
        config.TELEGRAM_CHAT_ID = "test_chat_id"
        config.STATIONS = []
        config.MARINE_POINTS = []
        config.CHECK_INTERVAL = 60
        mock.return_value = config
        yield config


@pytest.fixture
def mock_system_components():
    """Mock all system components"""
    with (
        patch("src.storm_radar.main.WeatherDataFetcher") as mock_fetcher,
        patch("src.storm_radar.main.EnhancedAlertCalculator") as mock_calculator,
        patch("src.storm_radar.main.TelegramNotifier") as mock_notifier,
    ):

        # Mock fetcher
        fetcher_instance = Mock()
        fetcher_instance.fetch_all_data.return_value = ([], [], [])
        mock_fetcher.return_value = fetcher_instance

        # Mock calculator
        calculator_instance = Mock()
        calculator_instance.calculate_enhanced_alerts.return_value = (25.0, ["Test reason"], "LOW")
        calculator_instance.get_enhanced_eta.return_value = "2-3 hours"
        mock_calculator.return_value = calculator_instance

        # Mock notifier
        notifier_instance = Mock()
        notifier_instance.should_send_alert.return_value = False
        notifier_instance.send_message.return_value = True
        notifier_instance.format_enhanced_message.return_value = "Test message"
        mock_notifier.return_value = notifier_instance

        yield {
            "fetcher": fetcher_instance,
            "calculator": calculator_instance,
            "notifier": notifier_instance,
        }


@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing"""
    return [
        WeatherData(
            station_name="TestStation",
            timestamp=datetime.now(),
            temperature=15.0,
            pressure=1015.0,
            humidity=70,
            wind_speed=25.0,
            wind_direction=180,
            station_type="coastal",
        )
    ]


class TestEnhancedWeatherAlertSystem:
    """Test cases for EnhancedWeatherAlertSystem"""

    def test_system_initialization(self, mock_config, mock_system_components):
        """Test system initializes correctly"""
        with patch("src.storm_radar.main.Configuration", return_value=mock_config):
            system = EnhancedWeatherAlertSystem()

            assert system.config == mock_config
            assert system.fetcher is not None
            assert system.calculator is not None
            assert system.notifier is not None

    def test_run_enhanced_check_no_data(self, mock_config, mock_system_components):
        """Test enhanced check when no weather data is retrieved"""
        mock_system_components["fetcher"].fetch_all_data.return_value = ([], [], [])

        with patch("src.storm_radar.main.Configuration", return_value=mock_config):
            system = EnhancedWeatherAlertSystem()

            # Should not raise exception and should log warning
            with patch("src.storm_radar.main.logger") as mock_logger:
                system.run_enhanced_check()
                mock_logger.warning.assert_called_with("No weather data retrieved")

    def test_run_enhanced_check_with_data(
        self, mock_config, mock_system_components, sample_weather_data
    ):
        """Test enhanced check with weather data"""
        # Setup mock data
        mock_system_components["fetcher"].fetch_all_data.return_value = (
            sample_weather_data,
            [],
            [],
        )
        mock_system_components["calculator"].calculate_enhanced_alerts.return_value = (
            45.0,
            ["Test alert"],
            "MEDIUM",
        )
        mock_system_components["notifier"].should_send_alert.return_value = False

        with patch("src.storm_radar.main.Configuration", return_value=mock_config):
            system = EnhancedWeatherAlertSystem()

            with patch("src.storm_radar.main.logger") as mock_logger:
                system.run_enhanced_check()

                # Verify data flow
                mock_system_components["fetcher"].fetch_all_data.assert_called_once()
                mock_system_components["calculator"].store_data.assert_called_once()
                mock_system_components["calculator"].calculate_enhanced_alerts.assert_called_once()
                mock_logger.info.assert_called_with("Enhanced alert: MEDIUM - Score: 45.0%")

    def test_run_enhanced_check_sends_alert(
        self, mock_config, mock_system_components, sample_weather_data
    ):
        """Test enhanced check that triggers alert sending"""
        # Setup mock data for alert condition
        mock_system_components["fetcher"].fetch_all_data.return_value = (
            sample_weather_data,
            [],
            [],
        )
        mock_system_components["calculator"].calculate_enhanced_alerts.return_value = (
            75.0,
            ["🌪️ BORA: High winds detected"],
            "HIGH",
        )
        mock_system_components["notifier"].should_send_alert.return_value = True
        mock_system_components["notifier"].send_message.return_value = True
        mock_system_components["calculator"].get_enhanced_eta.return_value = "30-60 minutes"

        with patch("src.storm_radar.main.Configuration", return_value=mock_config):
            system = EnhancedWeatherAlertSystem()

            with patch("src.storm_radar.main.logger") as mock_logger:
                system.run_enhanced_check()

                # Verify alert was processed and sent
                mock_system_components["notifier"].should_send_alert.assert_called_with(
                    75.0, "HIGH"
                )
                mock_system_components["calculator"].get_enhanced_eta.assert_called_once()
                mock_system_components["notifier"].format_enhanced_message.assert_called_once()
                mock_system_components["notifier"].send_message.assert_called_once()
                mock_logger.info.assert_called_with("Enhanced alert sent - HIGH: 75.0%")

    def test_run_enhanced_check_alert_send_fails(
        self, mock_config, mock_system_components, sample_weather_data
    ):
        """Test enhanced check when alert sending fails"""
        # Setup mock data for alert condition but sending fails
        mock_system_components["fetcher"].fetch_all_data.return_value = (
            sample_weather_data,
            [],
            [],
        )
        mock_system_components["calculator"].calculate_enhanced_alerts.return_value = (
            80.0,
            ["Test critical alert"],
            "CRITICAL",
        )
        mock_system_components["notifier"].should_send_alert.return_value = True
        mock_system_components["notifier"].send_message.return_value = False  # Sending fails

        with patch("src.storm_radar.main.Configuration", return_value=mock_config):
            system = EnhancedWeatherAlertSystem()

            with patch("src.storm_radar.main.logger") as mock_logger:
                system.run_enhanced_check()

                # Verify failure was logged
                mock_logger.error.assert_called_with("Failed to send enhanced alert")

    def test_run_continuous_keyboard_interrupt(self, mock_config, mock_system_components):
        """Test continuous run stops gracefully on KeyboardInterrupt"""
        with (
            patch("src.storm_radar.main.Configuration", return_value=mock_config),
            patch("src.storm_radar.main.time.sleep") as mock_sleep,
        ):

            system = EnhancedWeatherAlertSystem()

            # Mock sleep to raise KeyboardInterrupt after first call
            mock_sleep.side_effect = KeyboardInterrupt()

            with patch("src.storm_radar.main.logger") as mock_logger:
                system.run_continuous()

                # Should log graceful stop
                mock_logger.info.assert_any_call("Enhanced monitoring stopped by user")

    def test_run_continuous_exception_handling(self, mock_config, mock_system_components):
        """Test continuous run handles exceptions properly"""
        with (
            patch("src.storm_radar.main.Configuration", return_value=mock_config),
            patch("src.storm_radar.main.time.sleep") as mock_sleep,
        ):

            system = EnhancedWeatherAlertSystem()

            # Mock run_enhanced_check to raise exception, then KeyboardInterrupt
            system.run_enhanced_check = Mock(
                side_effect=[Exception("Test error"), KeyboardInterrupt()]
            )

            with patch("src.storm_radar.main.logger") as mock_logger:
                system.run_continuous()

                # Should log error and continue
                mock_logger.error.assert_called_with(
                    "Error in enhanced monitoring loop: Test error"
                )

    def test_bora_detection_triggers_immediate_eta(
        self, mock_config, mock_system_components, sample_weather_data
    ):
        """Test that Bora detection triggers immediate ETA calculation"""
        # Setup Bora detection scenario
        mock_system_components["fetcher"].fetch_all_data.return_value = (
            sample_weather_data,
            [],
            [],
        )
        mock_system_components["calculator"].calculate_enhanced_alerts.return_value = (
            85.0,
            ["🌪️ BORA: Pattern detected"],
            "CRITICAL",
        )
        mock_system_components["notifier"].should_send_alert.return_value = True

        with patch("src.storm_radar.main.Configuration", return_value=mock_config):
            system = EnhancedWeatherAlertSystem()
            system.run_enhanced_check()

            # Verify get_enhanced_eta was called with bora_detected=True
            args, kwargs = mock_system_components["calculator"].get_enhanced_eta.call_args
            reasons, bora_detected = args
            assert bora_detected is True
            assert any("BORA" in reason for reason in reasons)


class TestMainFunction:
    """Test cases for main entry point function"""

    def test_main_missing_bot_token(self):
        """Test main function with missing bot token"""
        with (
            patch("src.storm_radar.main.Configuration") as mock_config_class,
            patch("src.storm_radar.main.logger") as mock_logger,
        ):

            config = Mock()
            config.TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Default placeholder
            config.OPENWEATHER_API_KEY = "real_api_key"
            mock_config_class.return_value = config

            main()

            mock_logger.error.assert_called_with(
                "Please configure TELEGRAM_BOT_TOKEN in Configuration class"
            )

    def test_main_missing_api_key(self):
        """Test main function with missing API key"""
        with (
            patch("src.storm_radar.main.Configuration") as mock_config_class,
            patch("src.storm_radar.main.logger") as mock_logger,
        ):

            config = Mock()
            config.TELEGRAM_BOT_TOKEN = "real_bot_token"
            config.OPENWEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY_HERE"  # Default placeholder
            mock_config_class.return_value = config

            main()

            mock_logger.error.assert_called_with(
                "Please configure OPENWEATHER_API_KEY in Configuration class"
            )

    def test_main_once_mode(self, mock_config, mock_system_components):
        """Test main function in --once mode"""
        with (
            patch("src.storm_radar.main.Configuration", return_value=mock_config),
            patch("src.storm_radar.main.sys.argv", ["main.py", "--once"]),
            patch("src.storm_radar.main.EnhancedWeatherAlertSystem") as mock_system_class,
        ):

            mock_config.TELEGRAM_BOT_TOKEN = "real_bot_token"
            mock_config.OPENWEATHER_API_KEY = "real_api_key"

            system_instance = Mock()
            mock_system_class.return_value = system_instance

            main()

            # Should call run_enhanced_check once, not run_continuous
            system_instance.run_enhanced_check.assert_called_once()
            system_instance.run_continuous.assert_not_called()

    def test_main_continuous_mode(self, mock_config, mock_system_components):
        """Test main function in continuous mode (default)"""
        with (
            patch("src.storm_radar.main.Configuration", return_value=mock_config),
            patch("src.storm_radar.main.sys.argv", ["main.py"]),
            patch("src.storm_radar.main.EnhancedWeatherAlertSystem") as mock_system_class,
        ):

            mock_config.TELEGRAM_BOT_TOKEN = "real_bot_token"
            mock_config.OPENWEATHER_API_KEY = "real_api_key"

            system_instance = Mock()
            mock_system_class.return_value = system_instance

            main()

            # Should call run_continuous, not run_enhanced_check
            system_instance.run_continuous.assert_called_once()
            system_instance.run_enhanced_check.assert_not_called()

    def test_system_components_integration(self, mock_config):
        """Test that system properly integrates all components"""
        # Test with real component classes but mocked external dependencies
        with (
            patch("src.storm_radar.main.Configuration", return_value=mock_config),
            patch("requests.get"),
            patch("requests.post"),
        ):

            mock_config.TELEGRAM_BOT_TOKEN = "real_bot_token"
            mock_config.OPENWEATHER_API_KEY = "real_api_key"
            mock_config.TELEGRAM_CHAT_ID = "real_chat_id"
            mock_config.STATIONS = []
            mock_config.MARINE_POINTS = []

            # Should create system without errors
            system = EnhancedWeatherAlertSystem()

            # Components should be properly initialized
            assert hasattr(system, "config")
            assert hasattr(system, "fetcher")
            assert hasattr(system, "calculator")
            assert hasattr(system, "notifier")
