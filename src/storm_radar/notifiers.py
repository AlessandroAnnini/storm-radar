"""
Notification services for weather alerts
"""

import requests
from datetime import datetime, timedelta
from typing import List

from .logging import logger


class TelegramNotifier:
    """Enhanced Telegram notifier with better formatting"""

    def __init__(self, bot_token: str, chat_id: str, min_alert_level: str = "MEDIUM"):
        self.bot_token = bot_token
        # Handle chat_id conversion - it can be string or int
        try:
            # Try to convert to int if it's a valid number
            self.chat_id = int(chat_id)
        except ValueError:
            # Keep as string if it's a username (e.g., @channel)
            self.chat_id = chat_id

        self.last_alert_time = None
        self.last_alert_score = 0
        self.min_alert_level = min_alert_level.upper()

        # Define alert level hierarchy for comparison
        self.alert_levels = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

    def should_send_alert(self, score: float, alert_level: str) -> bool:
        """Enhanced alert logic with configurable minimum level"""
        now = datetime.now()

        # Check if alert level meets minimum threshold
        current_level_value = self.alert_levels.get(alert_level.upper(), 0)
        min_level_value = self.alert_levels.get(self.min_alert_level, 2)  # Default to MEDIUM

        if current_level_value < min_level_value:
            return False

        # Always send CRITICAL alerts (Bora)
        if alert_level == "CRITICAL":
            return True

        # Send HIGH alerts if no alert in last 20 minutes
        if alert_level == "HIGH" and score > 60:
            if self.last_alert_time is None or now - self.last_alert_time > timedelta(minutes=20):
                return True

        # Send MEDIUM alerts if no alert in last 45 minutes
        if alert_level == "MEDIUM" and score > 40:
            if self.last_alert_time is None or now - self.last_alert_time > timedelta(minutes=45):
                return True

        # Send LOW alerts if no alert in last 2 hours (and LOW is enabled)
        if alert_level == "LOW" and score > 20:
            if self.last_alert_time is None or now - self.last_alert_time > timedelta(hours=2):
                return True

        # Send if score significantly increased (regardless of level, if above minimum)
        if score > self.last_alert_score + 25:
            return True

        return False

    def send_message(self, message: str) -> bool:
        """Send message to Telegram chat with proper error handling"""
        try:
            # Validate message length (Telegram limit is 4096 characters)
            if len(message) > 4096:
                message = message[:4090] + "..."
                logger.log_error("Message truncated due to length limit", "Telegram API")

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

            # Prepare payload with proper types
            payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}

            # Send request with proper headers
            headers = {"Content-Type": "application/json", "User-Agent": "StormRadar/1.0"}

            response = requests.post(url, json=payload, headers=headers, timeout=10)

            # Detailed error handling
            if response.status_code == 400:
                error_data = (
                    response.json()
                    if response.headers.get("content-type", "").startswith("application/json")
                    else {}
                )
                error_description = error_data.get("description", "Bad Request")
                logger.log_error(f"Telegram API 400 Error: {error_description}", "Telegram API")
                logger.log_error(f"Request payload: {payload}", "Telegram API")

                # Try sending without Markdown if it's a parse error
                if "parse" in error_description.lower() or "markdown" in error_description.lower():
                    logger.log_error("Retrying without Markdown formatting", "Telegram API")
                    payload_plain = {"chat_id": self.chat_id, "text": self._strip_markdown(message)}
                    response = requests.post(url, json=payload_plain, headers=headers, timeout=10)

            response.raise_for_status()

            self.last_alert_time = datetime.now()
            logger.log_notification_sent(True, message)
            return True

        except requests.exceptions.RequestException as e:
            logger.log_notification_sent(False, message)
            logger.log_error(f"Failed to send Telegram message: {e}", "Telegram API")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.log_error(f"Telegram API error details: {error_detail}", "Telegram API")
                except:
                    logger.log_error(f"Telegram API response: {e.response.text}", "Telegram API")
            return False
        except Exception as e:
            logger.log_notification_sent(False, message)
            logger.log_error(f"Unexpected error sending Telegram message: {e}", "Telegram API")
            return False

    def _strip_markdown(self, text: str) -> str:
        """Remove Markdown formatting from text"""
        # Remove common markdown characters
        text = text.replace("*", "").replace("_", "").replace("`", "")
        text = text.replace("[", "").replace("]", "").replace("(", "").replace(")", "")
        return text

    def format_enhanced_message(
        self, score: float, reasons: List[str], alert_level: str, eta: str
    ) -> str:
        """Format enhanced alert message with safer Markdown"""

        # Alert level icons
        level_icons = {
            "CRITICAL": "🚨🚨🚨 CRITICAL ALERT",
            "HIGH": "🚨 HIGH ALERT",
            "MEDIUM": "⚠️ MEDIUM ALERT",
            "LOW": "ℹ️ LOW ALERT",
        }

        # Use safer markdown formatting
        message = f"*{level_icons.get(alert_level, '📊 ALERT')} - Falconara Marittima*\n"
        message += f"*Risk Score:* {score:.0f}%\n"
        message += f"*Estimated Arrival:* {eta}\n\n"

        if reasons:
            message += "*⚡ Active Conditions:*\n"
            for reason in reasons[:6]:  # Limit to 6 most important
                # Escape special markdown characters in reason text
                safe_reason = reason.replace("*", "").replace("_", "").replace("`", "")
                message += f"• {safe_reason}\n"

        # Add safety advice for critical alerts
        if alert_level == "CRITICAL":
            message += "\n*🚨 IMMEDIATE ACTION REQUIRED:*\n"
            message += "• Secure all outdoor items NOW\n"
            message += "• Avoid coastal areas\n"
            message += "• Check mooring lines\n"

        message += f"\n*🕐 Time:* {datetime.now().strftime('%H:%M - %d/%m/%Y')}"

        return message
