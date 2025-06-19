"""
Enhanced logging module using Rich package for beautiful console output.
Provides emoji-enhanced logging for weather data, conditions, and system operations.
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from functools import wraps

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich import box

from .models import WeatherData, MarineData, LightningData


def log_level_check(level: str):
    """Decorator to check log level before executing method"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self._should_log(level):
                return
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class WeatherLogger:
    """Enhanced weather logging with Rich formatting and emojis"""

    def __init__(self, verbose: bool = True):
        self.console = Console()
        self.verbose = verbose
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    def _should_log(self, level: str) -> bool:
        """Check if message should be logged based on level"""
        levels = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
        return levels.get(level, 1) >= levels.get(self.log_level, 1)

    def _get_emoji(self, data_type: str, data: Any = None) -> str:
        """Unified emoji dispatcher for all data types"""
        if data_type == "weather" and data:
            if data.wind_speed > 40:
                return "💨"
            elif data.temperature < 5:
                return "🥶"
            elif data.temperature > 30:
                return "🔥"
            elif data.pressure < 1000:
                return "⛈️"
            elif data.humidity > 90:
                return "🌧️"
            else:
                return "🌤️"

        elif data_type == "marine" and data:
            if data.wave_height > 3.0:
                return "🌊"
            elif data.wave_height > 1.5:
                return "〰️"
            else:
                return "🏖️"

        elif data_type == "lightning" and data:
            if data.distance_km < 10:
                return "⚡"
            elif data.distance_km < 50:
                return "🌩️"
            else:
                return "⛅"

        elif data_type == "alert":
            alert_map = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
            return alert_map.get(data, "⚪")

        elif data_type == "fetch":
            fetch_map = {"weather": "🌤️", "marine": "🌊", "lightning": "⚡"}
            return fetch_map.get(data, "📊")

        elif data_type == "status":
            status_map = {"running": "🟢", "stopping": "🟡", "error": "🔴", "sleeping": "😴"}
            return status_map.get(data, "⚪")

        return "📊"

    def _create_data_table(
        self, title: str, columns: List[tuple], data: List[Any], row_builder: Callable
    ) -> Table:
        """Unified table builder for all data types"""
        table = Table(title=title, box=box.ROUNDED)

        # Add columns with styles
        for col_name, style, justify in columns:
            table.add_column(col_name, style=style, justify=justify, no_wrap=(justify == "left"))

        # Add rows using the provided row builder
        for item in data:
            table.add_row(*row_builder(item))

        return table

    @log_level_check("INFO")
    def log_startup(self, config_loaded: bool = True) -> None:
        """Log system startup"""
        startup_panel = Panel.fit(
            "🌦️  [bold blue]Storm Radar Weather Alert System[/bold blue]  🌦️\n"
            f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Configuration: {'✅ Loaded' if config_loaded else '❌ Failed'}",
            box=box.DOUBLE,
            style="blue",
        )
        self.console.print(startup_panel)

    @log_level_check("INFO")
    def log_fetch_start(self, data_type: str, count: int) -> None:
        """Log start of data fetching"""
        emoji = self._get_emoji("fetch", data_type)
        self.console.print(
            f"{emoji} [bold]Fetching {data_type} data[/bold] from {count} sources..."
        )

    @log_level_check("INFO")
    def log_weather_data(self, weather_data: List[WeatherData]) -> None:
        """Log fetched weather data with beautiful formatting"""
        if not weather_data:
            return

        columns = [
            ("Station", "cyan", "left"),
            ("Temp", "magenta", "right"),
            ("Pressure", "blue", "right"),
            ("Wind", "green", "right"),
            ("Humidity", "yellow", "right"),
            ("Status", "", "center"),
        ]

        def build_weather_row(data: WeatherData) -> tuple:
            emoji = self._get_emoji("weather", data)
            wind_dir = f"{data.wind_direction}°" if data.wind_direction else "N/A"
            return (
                data.station_name,
                f"{data.temperature:.1f}°C",
                f"{data.pressure:.0f} hPa",
                f"{data.wind_speed:.1f} km/h {wind_dir}",
                f"{data.humidity}%",
                emoji,
            )

        table = self._create_data_table(
            "🌤️  Weather Station Data", columns, weather_data, build_weather_row
        )
        self.console.print(table)

    @log_level_check("INFO")
    def log_marine_data(self, marine_data: List[MarineData]) -> None:
        """Log fetched marine data with beautiful formatting"""
        if not marine_data:
            return

        columns = [
            ("Location", "cyan", "left"),
            ("Wave Height", "blue", "right"),
            ("Wave Period", "green", "right"),
            ("Wind Speed", "magenta", "right"),
            ("Wind Dir", "yellow", "right"),
            ("Status", "", "center"),
        ]

        def build_marine_row(data: MarineData) -> tuple:
            emoji = self._get_emoji("marine", data)
            return (
                data.location,
                f"{data.wave_height:.1f}m",
                f"{data.wave_period:.0f}s",
                "N/A",
                f"{data.wave_direction:.0f}°",
                emoji,
            )

        table = self._create_data_table(
            "🌊  Marine Conditions", columns, marine_data, build_marine_row
        )
        self.console.print(table)

    @log_level_check("INFO")
    def log_lightning_data(self, lightning_data: List[LightningData]) -> None:
        """Log lightning activity data"""
        if not lightning_data:
            return

        columns = [
            ("Area", "cyan", "left"),
            ("Strike Count", "red", "right"),
            ("Distance", "yellow", "right"),
            ("Intensity", "magenta", "right"),
            ("Status", "", "center"),
        ]

        def build_lightning_row(data: LightningData) -> tuple:
            emoji = self._get_emoji("lightning", data)
            return (
                f"{data.lat:.2f}, {data.lon:.2f}",
                "N/A",
                f"{data.distance_km:.1f} km",
                f"{data.intensity:.1f}",
                emoji,
            )

        table = self._create_data_table(
            "⚡  Lightning Activity", columns, lightning_data, build_lightning_row
        )
        self.console.print(table)

    @log_level_check("INFO")
    def log_alert_calculation(
        self, score: float, reasons: List[str], alert_level: str, eta: str
    ) -> None:
        """Log alert calculation results"""
        emoji = self._get_emoji("alert", alert_level)

        alert_text = f"[bold]Alert Score:[/bold] {score:.1f}/100\n"
        alert_text += f"[bold]Alert Level:[/bold] {alert_level}\n"
        alert_text += f"[bold]ETA:[/bold] {eta}\n\n"

        if reasons:
            alert_text += "[bold]Reasons:[/bold]\n"
            for reason in reasons:
                alert_text += f"  • {reason}\n"

        color_map = {"CRITICAL": "red", "HIGH": "orange3", "MEDIUM": "yellow", "LOW": "green"}
        color = color_map.get(alert_level, "white")

        panel = Panel(
            alert_text.strip(), title=f"{emoji} Alert Calculation", box=box.DOUBLE, style=color
        )
        self.console.print(panel)

    @log_level_check("INFO")
    def log_notification_sent(self, success: bool, message_preview: str) -> None:
        """Log notification sending result"""
        if success:
            self.console.print("📱 [green]✅ Telegram notification sent successfully[/green]")
            if self.verbose:
                preview = (
                    message_preview[:50] + "..." if len(message_preview) > 50 else message_preview
                )
                self.console.print(f"   Preview: [dim]{preview}[/dim]")
        else:
            self.console.print("📱 [red]❌ Failed to send Telegram notification[/red]")

    @log_level_check("INFO")
    def log_data_summary(self, weather_count: int, marine_count: int, lightning_count: int) -> None:
        """Log summary of fetched data"""
        summary_text = f"📊 [bold]Data Summary:[/bold]\n"
        summary_text += f"  🌤️  Weather stations: {weather_count}\n"
        summary_text += f"  🌊  Marine points: {marine_count}\n"
        summary_text += f"  ⚡  Lightning areas: {lightning_count}"

        self.console.print(Panel(summary_text, box=box.ROUNDED, style="blue"))

    @log_level_check("INFO")
    def log_system_status(self, status: str, details: str = None) -> None:
        """Log system status updates"""
        emoji = self._get_emoji("status", status)
        message = f"{emoji} System: {status.upper()}"
        if details:
            message += f" - {details}"
        self.console.print(message)

    @log_level_check("WARNING")
    def log_api_error(self, api_name: str, error: str, station_name: str = None) -> None:
        """Log API fetch errors"""
        location = f" for {station_name}" if station_name else ""
        self.console.print(f"🚨 [red]API Error[/red] ({api_name}{location}): {error}")

    @log_level_check("DEBUG")
    def log_debug(self, message: str, data: Dict[str, Any] = None) -> None:
        """Log debug information"""
        self.console.print(f"🔍 [dim]DEBUG: {message}[/dim]")
        if data and self.verbose:
            for key, value in data.items():
                self.console.print(f"    {key}: {value}")

    @log_level_check("ERROR")
    def log_error(self, error: str, context: str = None) -> None:
        """Log errors with context"""
        error_text = f"❌ [red bold]ERROR:[/red bold] {error}"
        if context:
            error_text += f"\n   Context: {context}"
        self.console.print(error_text)

    def create_progress_bar(self, description: str = "Processing"):
        """Create a progress bar for long operations"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        )


# Global logger instance
logger = WeatherLogger()
