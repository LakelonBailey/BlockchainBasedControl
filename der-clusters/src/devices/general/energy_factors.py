import math
import random
import pytz
from datetime import datetime
from abc import ABC, abstractmethod
from src.devices.constants.datetime import DEFAULT_TIMEZONE
from src.devices.general.base import EnergyFactor


class TimeBasedEnergyFactor(EnergyFactor, ABC):
    """Abstract base class for consumption factor that involves time"""

    @abstractmethod
    def __init__(self, factor_name: str, timezone: str = DEFAULT_TIMEZONE):
        super().__init__(factor_name)
        self.timezone = pytz.timezone(timezone)

    def get_datetime(self):
        return datetime.now(self.timezone)


class WindFactor(TimeBasedEnergyFactor):
    """Factor that adjusts production based on wind speed."""

    def __init__(
        self,
        min_wind_speed: float = 5.0,
        max_wind_speed: float = 25.0,
        optimal_wind_speed: float = 15.0,
        wind_variability: float = 3.0,
    ):
        super().__init__("Wind")
        self.min_wind_speed = min_wind_speed
        self.max_wind_speed = max_wind_speed
        self.optimal_wind_speed = optimal_wind_speed
        self.wind_variability = wind_variability

    def get_multiplier(self, context: dict) -> float:
        wind_speed = context.get(
            "wind_speed", random.uniform(self.min_wind_speed, self.max_wind_speed)
        )

        # If wind speed is below minimum threshold, no power is generated
        if wind_speed < self.min_wind_speed:
            return 0.0

        # Use a bell curve for efficiency scaling
        efficiency = math.exp(
            -((wind_speed - self.optimal_wind_speed) ** 2)
            / (2 * (self.wind_variability**2))
        )
        return min(1.0, efficiency)


class PeakHoursFactor(TimeBasedEnergyFactor):
    """Factor that increases consumption during peak hours (5-9 PM)"""

    def __init__(
        self,
        peak_multiplier=1.5,
        off_peak_multiplier=1.0,
        timezone: str = DEFAULT_TIMEZONE,
    ):
        super().__init__("Peak Hours", timezone=timezone)
        self.peak_multiplier = peak_multiplier
        self.off_peak_multiplier = off_peak_multiplier

    def get_multiplier(self, context: dict) -> float:
        hour = context.get("hour", self.get_datetime().hour)
        return self.peak_multiplier if 17 <= hour <= 21 else self.off_peak_multiplier


class WeekendFactor(TimeBasedEnergyFactor):
    """Factor that increases consumption on the weekend"""

    def __init__(
        self,
        weekend_multiplier=1.5,
        weekday_multiplier=1.0,
        timezone: str = DEFAULT_TIMEZONE,
    ):
        super().__init__("Weekend", timezone=timezone)
        self.weekend_multiplier = weekend_multiplier
        self.weekday_multiplier = weekday_multiplier

    def get_multiplier(self, context):
        weekday = context.get("weekday", self.get_datetime().weekday())
        return self.weekend_multiplier if weekday in [5, 6] else self.weekday_multiplier


class SolarFactor(TimeBasedEnergyFactor):
    """Factor that is dependent on sunlight"""

    def __init__(
        self,
        sunrise: float = 6,
        sunset: float = 18,
        peak_shift: float = math.pi / 6,
        overcast_multiplier: float = 0.5,
        overcast_probability: float = 0.05,
        timezone: str = DEFAULT_TIMEZONE,
    ):
        super().__init__("Solar", timezone=timezone)
        self.sunrise = sunrise
        self.sunset = sunset
        self.peak_shift = peak_shift
        self.overcast_multiplier = overcast_multiplier
        self.overcast_probability = overcast_probability

    def calculate_solar_efficiency(self, hour: int) -> float:
        """
        Simulate solar panel efficiency over a day.
        """
        if hour < self.sunrise or hour > self.sunset:
            return 0  # No solar output at night

        # Normalize hour into a range [0, π] to create a sinusoidal wave
        normalized_hour = math.pi * (hour - self.sunrise) / (self.sunset - self.sunrise)

        # Compute the solar efficiency curve with a slight shift, scaled to [0,1]
        efficiency = max(0, (math.sin(normalized_hour - self.peak_shift) + 1) / 2)
        if random.random() <= self.overcast_probability:
            efficiency *= self.overcast_multiplier
        return efficiency

    def get_multiplier(self, context: dict) -> float:
        hour = context.get("hour", self.get_datetime().hour)
        return self.calculate_solar_efficiency(hour)


class SeasonalFactor(TimeBasedEnergyFactor):
    """Factor that adjusts consumption based on the season"""

    def __init__(
        self,
        summer_multiplier=1.5,
        winter_multiplier=1.3,
        default_multiplier=1.0,
        timezone: str = DEFAULT_TIMEZONE,
    ):
        super().__init__("Seasonal", timezone=timezone)
        self.summer_multiplier = summer_multiplier
        self.winter_multiplier = winter_multiplier
        self.default_multiplier = default_multiplier

    def get_multiplier(self, context: dict) -> float:
        month = context.get("month", self.get_datetime().month)

        # Summer (June, July, August)
        if month in [6, 7, 8]:
            return self.summer_multiplier

        # Winter (December, January, February)
        elif month in [12, 1, 2]:
            return self.winter_multiplier

        # Spring/Fall (All other months)
        else:
            return self.default_multiplier


class RandomUsageFactor(TimeBasedEnergyFactor):
    """Factor that randomly increases consumption for unpredictable usage appliances"""

    def __init__(
        self,
        min_multiplier=1.0,
        max_multiplier=2.0,
        randomness_probability=0.2,
        timezone: str = DEFAULT_TIMEZONE,
    ):
        super().__init__("Random Usage", timezone=timezone)
        self.min_multiplier = min_multiplier
        self.max_multiplier = max_multiplier
        self.randomness_probability = randomness_probability

    def get_multiplier(self, context: dict) -> float:
        """
        Introduce random spikes for devices that are used unpredictably.
        """
        if random.random() < self.randomness_probability:
            return random.uniform(self.min_multiplier, self.max_multiplier)
        return self.min_multiplier
