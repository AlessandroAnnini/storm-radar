"""
Tests for TelegramNotifier class
"""

import pytest
import requests
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from src.storm_radar.notifiers import TelegramNotifier


@pytest.fixture
def notifier():
    """TelegramNotifier instance for testing"""
    return TelegramNotifier("test_bot_token", "test_chat_id")


@pytest.fixture
def sample_reasons():
    """Sample alert reasons for testing"""
    return [
        "🌪️ BORA: High pressure difference detected",
        "🌊 MARINE: High waves 3.2m",
        "⚡ LIGHTNING: 15 strikes approaching",
    ]


class TestTelegramNotifier:
    """Test cases for TelegramNotifier"""

    def test_notifier_initialization(self):
        """Test notifier initializes correctly"""
        notifier = TelegramNotifier("test_token", "test_chat")

        assert notifier.bot_token == "test_token"
        assert notifier.chat_id == "test_chat"
        assert notifier.last_alert_time is None
        assert notifier.last_alert_score == 0

    def test_should_send_alert_critical_always(self, notifier):
        """Test that CRITICAL alerts are always sent"""
        # CRITICAL alerts should always be sent
        assert notifier.should_send_alert(80.0, "CRITICAL") is True

        # Even if recently sent
        notifier.last_alert_time = datetime.now()
        assert notifier.should_send_alert(85.0, "CRITICAL") is True

    def test_should_send_alert_high_with_timing(self, notifier):
        """Test HIGH alert timing logic"""
        # HIGH alert should be sent initially
        assert notifier.should_send_alert(65.0, "HIGH") is True

        # Should not send again immediately
        notifier.last_alert_time = datetime.now()
        assert notifier.should_send_alert(65.0, "HIGH") is False

        # Should send again after 20+ minutes
        notifier.last_alert_time = datetime.now() - timedelta(minutes=25)
        assert notifier.should_send_alert(65.0, "HIGH") is True

    def test_should_send_alert_medium_with_timing(self, notifier):
        """Test MEDIUM alert timing logic"""
        # MEDIUM alert should be sent initially
        assert notifier.should_send_alert(45.0, "MEDIUM") is True

        # Should not send again immediately
        notifier.last_alert_time = datetime.now()
        assert notifier.should_send_alert(45.0, "MEDIUM") is False

        # Should send again after 45+ minutes
        notifier.last_alert_time = datetime.now() - timedelta(minutes=50)
        assert notifier.should_send_alert(45.0, "MEDIUM") is True

    def test_should_send_alert_score_increase(self, notifier):
        """Test alert sending on significant score increase"""
        notifier.last_alert_score = 30.0

        # Should send if score increased by >25 points
        assert notifier.should_send_alert(60.0, "MEDIUM") is True

        # Should not send for smaller increases
        assert notifier.should_send_alert(50.0, "MEDIUM") is False

    def test_should_send_alert_low_level(self, notifier):
        """Test LOW level alerts are not sent under normal conditions"""
        # LOW alerts generally shouldn't be sent
        assert notifier.should_send_alert(25.0, "LOW") is False

        # Unless there's a big score jump
        notifier.last_alert_score = 0.0
        assert notifier.should_send_alert(30.0, "LOW") is True

    @patch("requests.post")
    def test_send_message_success(self, mock_post, notifier):
        """Test successful message sending"""
        # Setup mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Send message
        result = notifier.send_message("Test message")

        # Verify success
        assert result is True
        assert notifier.last_alert_time is not None

        # Verify API call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args

        assert "sendMessage" in args[0]
        assert "json" in kwargs
        payload = kwargs["json"]
        assert payload["chat_id"] == "test_chat_id"
        assert payload["text"] == "Test message"
        assert payload["parse_mode"] == "Markdown"

    @patch("requests.post")
    def test_send_message_api_error(self, mock_post, notifier):
        """Test message sending with API error"""
        # Setup mock to raise exception
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        # Send message should return False on error
        result = notifier.send_message("Test message")

        assert result is False

    @patch("requests.post")
    def test_send_message_http_error(self, mock_post, notifier):
        """Test message sending with HTTP error"""
        # Setup mock response with HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("400")
        mock_post.return_value = mock_response

        # Send message should return False on error
        result = notifier.send_message("Test message")

        assert result is False

    def test_format_enhanced_message_critical(self, notifier, sample_reasons):
        """Test formatting of CRITICAL alert message"""
        message = notifier.format_enhanced_message(
            score=85.0,
            reasons=sample_reasons,
            alert_level="CRITICAL",
            eta="15-45 minutes (BORA - IMMEDIATE DANGER)",
        )

        # Verify critical alert formatting
        assert "🚨🚨🚨 CRITICAL ALERT" in message
        assert "85%" in message
        assert "15-45 minutes" in message
        assert "🌪️ BORA" in message
        assert "🌊 MARINE" in message
        assert "⚡ LIGHTNING" in message

        # Should include safety advice for critical alerts
        assert "IMMEDIATE ACTION REQUIRED" in message
        assert "Secure all outdoor items NOW" in message
        assert "Avoid coastal areas" in message

    def test_format_enhanced_message_high(self, notifier, sample_reasons):
        """Test formatting of HIGH alert message"""
        message = notifier.format_enhanced_message(
            score=70.0,
            reasons=sample_reasons[:2],  # Fewer reasons
            alert_level="HIGH",
            eta="30-60 minutes",
        )

        # Verify high alert formatting
        assert "🚨 HIGH ALERT" in message
        assert "70%" in message
        assert "30-60 minutes" in message
        assert "🌪️ BORA" in message
        assert "🌊 MARINE" in message

        # Should not include safety advice for non-critical
        assert "IMMEDIATE ACTION REQUIRED" not in message

    def test_format_enhanced_message_medium(self, notifier):
        """Test formatting of MEDIUM alert message"""
        message = notifier.format_enhanced_message(
            score=45.0,
            reasons=["🌊 MARINE: Test condition"],
            alert_level="MEDIUM",
            eta="45-90 minutes",
        )

        # Verify medium alert formatting
        assert "⚠️ MEDIUM ALERT" in message
        assert "45%" in message
        assert "45-90 minutes" in message

    def test_format_enhanced_message_low(self, notifier):
        """Test formatting of LOW alert message"""
        message = notifier.format_enhanced_message(
            score=25.0, reasons=["Minor condition detected"], alert_level="LOW", eta="2-3 hours"
        )

        # Verify low alert formatting
        assert "ℹ️ LOW ALERT" in message
        assert "25%" in message
        assert "2-3 hours" in message

    def test_format_enhanced_message_no_reasons(self, notifier):
        """Test formatting message with no reasons"""
        message = notifier.format_enhanced_message(
            score=30.0, reasons=[], alert_level="LOW", eta="2-3 hours"
        )

        # Should handle empty reasons gracefully
        assert "LOW ALERT" in message
        assert "30%" in message
        assert "Active Conditions" not in message  # Section should be omitted

    def test_format_enhanced_message_many_reasons(self, notifier):
        """Test formatting message with many reasons (should limit to 6)"""
        many_reasons = [f"Reason {i}" for i in range(10)]

        message = notifier.format_enhanced_message(
            score=60.0, reasons=many_reasons, alert_level="HIGH", eta="1 hour"
        )

        # Should limit to 6 reasons
        reason_count = message.count("• Reason")
        assert reason_count == 6

    def test_format_enhanced_message_includes_timestamp(self, notifier):
        """Test that formatted message includes timestamp"""
        with patch("src.storm_radar.notifiers.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 15, 14, 30, 0)
            mock_datetime.now.return_value = mock_now

            message = notifier.format_enhanced_message(
                score=40.0, reasons=["Test reason"], alert_level="MEDIUM", eta="1 hour"
            )

            # Should include formatted timestamp
            assert "14:30 - 15/01/2024" in message

    def test_format_enhanced_message_unknown_level(self, notifier):
        """Test formatting message with unknown alert level"""
        message = notifier.format_enhanced_message(
            score=50.0, reasons=["Test reason"], alert_level="UNKNOWN", eta="1 hour"
        )

        # Should fall back to generic alert
        assert "📊 ALERT" in message

    @patch("requests.post")
    def test_send_message_timeout(self, mock_post, notifier):
        """Test message sending with timeout"""
        # Setup mock to timeout
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        # Should handle timeout gracefully
        result = notifier.send_message("Test message")

        assert result is False

    def test_alert_timing_edge_cases(self, notifier):
        """Test edge cases in alert timing logic"""
        # Test with exactly threshold times
        notifier.last_alert_time = datetime.now() - timedelta(minutes=20)  # Exactly 20 minutes
        assert notifier.should_send_alert(65.0, "HIGH") is True

        notifier.last_alert_time = datetime.now() - timedelta(minutes=45)  # Exactly 45 minutes
        assert notifier.should_send_alert(45.0, "MEDIUM") is True

        # Test with just under threshold
        notifier.last_alert_time = datetime.now() - timedelta(minutes=19)
        assert notifier.should_send_alert(65.0, "HIGH") is False

        notifier.last_alert_time = datetime.now() - timedelta(minutes=44)
        assert notifier.should_send_alert(45.0, "MEDIUM") is False

    def test_score_tracking(self, notifier):
        """Test that scores are tracked correctly"""
        initial_score = notifier.last_alert_score
        assert initial_score == 0

        # Mock successful send to update score
        with patch.object(notifier, "send_message", return_value=True):
            # Score should be updated externally (in main system)
            # This tests the attribute exists and can be modified
            notifier.last_alert_score = 75.0
            assert notifier.last_alert_score == 75.0
