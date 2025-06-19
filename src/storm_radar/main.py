#!/usr/bin/env python3
"""
Enhanced Weather Alert System for Falconara Marittima
Main orchestrator and entry point
"""

import sys
import time

from .config import Configuration
from .fetchers import WeatherDataFetcher
from .calculators import EnhancedAlertCalculator
from .notifiers import TelegramNotifier
from .logging import logger


class EnhancedWeatherAlertSystem:
    """Enhanced weather alert system orchestrator"""

    def __init__(self):
        self.config = Configuration()
        self.fetcher = WeatherDataFetcher(self.config.OPENWEATHER_API_KEY)
        self.calculator = EnhancedAlertCalculator(self.config)
        self.notifier = TelegramNotifier(
            self.config.TELEGRAM_BOT_TOKEN,
            self.config.TELEGRAM_CHAT_ID,
            self.config.MIN_ALERT_LEVEL,
        )
        logger.log_startup(config_loaded=True)

    def run_enhanced_check(self):
        """Run enhanced weather check cycle"""
        logger.log_system_status("running", "Starting enhanced weather check cycle")

        # Fetch all data types
        weather_data, marine_data, lightning_data = self.fetcher.fetch_all_data(
            self.config.STATIONS, self.config.MARINE_POINTS
        )

        if not weather_data:
            logger.log_error("No weather data retrieved", "Data fetch")
            return

        # Store for trend analysis
        self.calculator.store_data(weather_data, marine_data, lightning_data)

        # Calculate enhanced alerts
        score, reasons, alert_level = self.calculator.calculate_enhanced_alerts(
            weather_data, marine_data, lightning_data
        )

        # Send alert if needed
        if self.notifier.should_send_alert(score, alert_level):
            bora_detected = any("BORA" in reason for reason in reasons)
            eta = self.calculator.get_enhanced_eta(reasons, bora_detected)
            message = self.notifier.format_enhanced_message(score, reasons, alert_level, eta)

            if self.notifier.send_message(message):
                self.notifier.last_alert_score = score
            # Notification logging is handled in the notifier

    def run_continuous(self):
        """Run continuous enhanced monitoring"""
        logger.log_system_status("running", "Enhanced weather monitoring for Falconara Marittima")
        logger.log_debug("Monitoring: Bora winds, Lightning, Marine conditions, Thermal gradients")

        while True:
            try:
                self.run_enhanced_check()
                logger.log_system_status(
                    "sleeping", f"Next check in {self.config.CHECK_INTERVAL} seconds"
                )
                time.sleep(self.config.CHECK_INTERVAL)

            except KeyboardInterrupt:
                logger.log_system_status("stopping", "Monitoring stopped by user")
                break
            except Exception as e:
                logger.log_system_status("error", f"Error in monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error


def main():
    """Main entry point for enhanced system"""

    config = Configuration()

    # Validate configuration
    if config.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.log_error("Please configure TELEGRAM_BOT_TOKEN in .env file", "Configuration")
        return

    if config.OPENWEATHER_API_KEY == "YOUR_OPENWEATHER_API_KEY_HERE":
        logger.log_error("Please configure OPENWEATHER_API_KEY in .env file", "Configuration")
        return

    # Start enhanced monitoring
    system = EnhancedWeatherAlertSystem()

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        system.run_enhanced_check()
    else:
        system.run_continuous()


if __name__ == "__main__":
    main()
