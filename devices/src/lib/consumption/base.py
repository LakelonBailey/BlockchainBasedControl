from abc import ABC, abstractmethod
from src.lib.general.energy_factors import EnergyFactor
from src.lib.general.base import Tier, Device
from src.constants import device_types


class ConsumptionTier(ABC, Tier):
    """Base class for consumption tiers"""


class ConsumptionDevice(ABC, Device):
    """Base class for consumption devices"""

    @abstractmethod
    def __init__(
        self,
        device_name: str,
        consumption_tier: ConsumptionTier,
        energy_factors: list[EnergyFactor],
    ):
        super().__init__(
            device_name, device_types.CONSUMPTION, consumption_tier, energy_factors
        )
