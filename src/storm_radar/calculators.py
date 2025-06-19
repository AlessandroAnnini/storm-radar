"""
Alert calculation and weather pattern analysis
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from .models import WeatherData, MarineData, LightningData
from .logging import logger
from .config import Configuration


class EnhancedAlertCalculator:
    """Enhanced alert calculator with Bora, marine, and thermal analysis"""

    def __init__(self, config: Configuration):
        self.config = config
        self.historical_weather = {}
        self.historical_marine = {}
        self.historical_lightning = []

    def store_data(
        self,
        weather_data: List[WeatherData],
        marine_data: List[MarineData],
        lightning_data: List[LightningData],
    ):
        """Store all data types for trend analysis"""

        # Store weather data
        for data in weather_data:
            if data.station_name not in self.historical_weather:
                self.historical_weather[data.station_name] = []
            self.historical_weather[data.station_name].append(data)

        # Store marine data
        for data in marine_data:
            if data.location not in self.historical_marine:
                self.historical_marine[data.location] = []
            self.historical_marine[data.location].append(data)

        # Store lightning data
        self.historical_lightning.extend(lightning_data)

        # Clean old data
        cutoff_time = datetime.now() - timedelta(hours=self.config.DATA_RETENTION_HOURS)

        for station in self.historical_weather:
            self.historical_weather[station] = [
                d for d in self.historical_weather[station] if d.timestamp > cutoff_time
            ]

        for location in self.historical_marine:
            self.historical_marine[location] = [
                d for d in self.historical_marine[location] if d.timestamp > cutoff_time
            ]

        self.historical_lightning = [
            d for d in self.historical_lightning if d.timestamp > cutoff_time
        ]

    def check_bora_pattern(self, weather_data: List[WeatherData]) -> Tuple[bool, str]:
        """Check for Bora wind pattern - CRITICAL for Adriatic"""

        # Get NE stations (Trieste, Nova Gorica, Rijeka)
        ne_stations = [
            d for d in weather_data if d.station_name in ["Trieste", "Nova_Gorica", "Rijeka"]
        ]
        local_stations = [d for d in weather_data if d.station_name in ["Ancona", "Falconara"]]

        if not ne_stations or not local_stations:
            return False, ""

        # Calculate pressure differential
        avg_ne_pressure = sum(s.pressure for s in ne_stations) / len(ne_stations)
        avg_local_pressure = sum(s.pressure for s in local_stations) / len(local_stations)
        pressure_diff = avg_ne_pressure - avg_local_pressure

        # Check for high NE winds
        max_ne_wind = max(s.wind_speed for s in ne_stations)
        ne_wind_from_correct_direction = any(
            s.wind_speed > 30 and 0 <= s.wind_direction <= 90 for s in ne_stations
        )

        # Bora pattern detection
        if (
            pressure_diff > self.config.BORA_PRESSURE_DIFF_THRESHOLD
            and max_ne_wind > self.config.BORA_WIND_THRESHOLD
            and ne_wind_from_correct_direction
        ):

            return (
                True,
                f"BORA PATTERN DETECTED: Pressure diff {pressure_diff:.1f}hPa, NE winds {max_ne_wind:.1f}km/h",
            )

        return False, ""

    def calculate_enhanced_alerts(
        self,
        weather_data: List[WeatherData],
        marine_data: List[MarineData],
        lightning_data: List[LightningData],
    ) -> Tuple[float, List[str], str]:
        """Simplified alert calculation with identical functionality"""

        score = 0.0
        reasons = []
        alert_level = "LOW"

        # 1. BORA DETECTION (Highest Priority - Keep as separate method)
        bora_detected, bora_reason = self.check_bora_pattern(weather_data)
        if bora_detected:
            score += 60  # Immediate high score for Bora
            reasons.append(f"🌪️ BORA: {bora_reason}")
            alert_level = "CRITICAL"

        # 2. MARINE CONDITIONS (Inlined for simplicity)
        if marine_data:
            marine_alerts = []
            for data in marine_data:
                # Short wave period indicates storm
                if data.wave_period < self.config.WAVE_PERIOD_THRESHOLD:
                    marine_alerts.append(
                        f"{data.location}: Short wave period {data.wave_period:.1f}s"
                    )
                # High waves
                if data.wave_height > self.config.WAVE_HEIGHT_THRESHOLD:
                    marine_alerts.append(f"{data.location}: High waves {data.wave_height:.1f}m")

            if marine_alerts:
                score += 25
                reasons.append(f"🌊 MARINE: {'; '.join(marine_alerts)}")

        # 3. LIGHTNING ACTIVITY (Inlined for simplicity)
        if lightning_data:
            # Count recent strikes within approach distance
            recent_time = datetime.now() - timedelta(minutes=10)
            nearby_strikes = [
                strike
                for strike in lightning_data
                if (
                    strike.timestamp > recent_time
                    and strike.distance_km < self.config.LIGHTNING_APPROACH_DISTANCE
                )
            ]

            if len(nearby_strikes) > self.config.LIGHTNING_DENSITY_THRESHOLD:
                avg_distance = sum(s.distance_km for s in nearby_strikes) / len(nearby_strikes)
                score += 30
                reasons.append(
                    f"⚡ LIGHTNING: Lightning approaching: {len(nearby_strikes)} strikes, avg distance {avg_distance:.1f}km"
                )

        # 4. THERMAL GRADIENT (Inlined for simplicity)
        coastal_temps = [d.temperature for d in weather_data if d.station_type == "coastal"]
        inland_temps = [d.temperature for d in weather_data if d.station_type == "inland"]

        if coastal_temps and inland_temps:
            avg_coastal = sum(coastal_temps) / len(coastal_temps)
            avg_inland = sum(inland_temps) / len(inland_temps)
            gradient = abs(avg_inland - avg_coastal)

            if gradient > self.config.THERMAL_GRADIENT_THRESHOLD:
                score += 15
                reasons.append(
                    f"🌡️ THERMAL: High thermal gradient: {gradient:.1f}°C difference (Inland: {avg_inland:.1f}°C, Coastal: {avg_coastal:.1f}°C)"
                )

        # 5. TRADITIONAL WEATHER PATTERNS
        traditional_score = self._calculate_traditional_patterns(weather_data)
        score += traditional_score

        # Determine alert level (don't override CRITICAL from Bora)
        if alert_level != "CRITICAL":
            if score > 70:
                alert_level = "HIGH"
            elif score > 40:
                alert_level = "MEDIUM"
            elif score > 20:
                alert_level = "LOW"

        final_score = min(score, 100)
        eta = self.get_enhanced_eta(reasons, bora_detected)

        # Log the alert calculation
        logger.log_alert_calculation(final_score, reasons, alert_level, eta)

        return final_score, reasons, alert_level

    def _calculate_traditional_patterns(self, weather_data: List[WeatherData]) -> float:
        """Simplified traditional pattern analysis"""
        score = 0.0

        for data in weather_data:
            # High winds
            if data.wind_speed > self.config.HIGH_WIND_THRESHOLD:
                score += 10

            # Thunderstorms
            if data.weather_main in ["Thunderstorm", "Rain"]:
                score += 15

            # High humidity
            if data.humidity > 85:
                score += 5

        return score

    def get_enhanced_eta(self, reasons: List[str], bora_detected: bool) -> str:
        """Enhanced ETA calculation"""

        if bora_detected:
            return "15-45 minutes (BORA - IMMEDIATE DANGER)"

        if any("LIGHTNING" in reason for reason in reasons):
            return "30-60 minutes"

        if any("MARINE" in reason for reason in reasons):
            return "45-90 minutes"

        if any("Gubbio" in reason or "Fabriano" in reason for reason in reasons):
            return "1-2 hours"

        return "2-3 hours"
