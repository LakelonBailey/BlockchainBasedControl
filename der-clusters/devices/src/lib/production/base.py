from abc import ABC, abstractmethod
from src.lib.general.energy_factors import EnergyFactor
from src.lib.general.base import Tier, Device
from src.constants import device_types


class ProductionTier(Tier, ABC):
    """Base class for production tiers"""


class ProductionDevice(Device, ABC):
    """Base class for production devices"""

    @abstractmethod
    def __init__(
        self,
        device_name: str,
        production_tier: ProductionTier,
        energy_factors: list[EnergyFactor],
    ):
        super().__init__(
            device_name, device_types.PRODUCTION, production_tier, energy_factors
        )
