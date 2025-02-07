from abc import ABC, abstractmethod
from typing import Literal
from datetime import datetime
from src.devices.constants import device_types
import uuid


class SerializableClass(ABC):

    @abstractmethod
    def to_dict(self) -> dict:
        pass

class EnergyFactor(SerializableClass, ABC):
    """Abstract base class for consumption energy_factors"""

    @abstractmethod
    def __init__(self, factor_name: str):
        self.name = factor_name

    @abstractmethod
    def get_multiplier(self, context: dict) -> float:
        """Compute multiplier based on context (e.g., time of day, temperature)."""
        pass

    def to_dict(self):
        return {
            'name': self.name,
        }



class Tier(SerializableClass, ABC):

    @abstractmethod
    def __init__(self, default_kw: float, tier_no: int):
        self.default_kw = default_kw
        self.tier_no = tier_no

    def to_dict(self):
        return {
            'tier_no': self.tier_no,
            'default_kw': self.default_kw
        }


class Device(SerializableClass, ABC):
    """Base class for consumption devices"""

    @abstractmethod
    def __init__(
        self,
        device_name: str,
        device_type: Literal["production", "consumption"],
        tier: Tier,
        energy_factors: list[EnergyFactor],
    ):
        if device_type not in device_types.DEVICE_TYPES:
            raise ValueError(f"Invalid device_type: {device_type}")

        self.id = uuid.uuid4()
        self.name = device_name
        self.device_type = device_type
        self.tier = tier
        self.energy_factors = energy_factors

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'type': self.device_type,
            'tier': self.tier.to_dict(),
            'energy_factors': [
                factor.to_dict() for factor in self.energy_factors
            ]
        }

    def calculate_kw(self, context: dict = None):
        """
        Calculate instantaneous kW consumption based on consumption energy_factors.

        Args:
            context (dict, optional): Environmental conditions (e.g., {"hour": 18, \
            "temperature": 85}).

        Returns:
            float: Current kW consumption.
        """
        if context is None:
            context = {}

        multiplier = 1
        for factor in self.energy_factors:
            multiplier *= factor.get_multiplier(context)

        return multiplier * self.tier.default_kw

    def calculate_kwh(self, start_time: datetime, end_time: datetime) -> float:
        """
        Calculate device kWh for the given time range.

        Args:
            start_time (datetime): Start time of the time interval
            end_time (datetime): End time of the time interval
        Returns:
            float: Consumption in kWh.

        """
        hours = (end_time - start_time).seconds / 3600
        context = {"start_time": start_time, "end_time": end_time}
        kwh = self.calculate_kw(context) * hours

        # NOTE: Removing this for now as it's probably better to implement
        # this type of logic further upstream
        # if self.device_type == device_types.CONSUMPTION:
        #     return kwh * -1

        return kwh
