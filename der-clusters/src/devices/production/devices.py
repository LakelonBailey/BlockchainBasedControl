from src.devices.production.base import ProductionDevice
from src.devices.general.energy_factors import (
    PeakHoursFactor,
    SolarFactor,
    SeasonalFactor,
    RandomUsageFactor,
    WindFactor,
)
from src.devices.production.tiers import (
    LowProductionTier,
    ModerateProductionTier,
    HighProductionTier,
    VeryHighProductionTier,
    ExtremeProductionTier,
)


class SmallSolarPanel(ProductionDevice):
    """A small solar panel that follows solar energy production"""

    def __init__(self):
        super().__init__(
            device_name="Small Solar Panel",
            production_tier=LowProductionTier(),
            energy_factors=[SolarFactor()],
        )


class LargeSolarArray(ProductionDevice):
    """A large solar panel array that produces more energy"""

    def __init__(self):
        super().__init__(
            device_name="Large Solar Array",
            production_tier=ModerateProductionTier(),
            energy_factors=[SolarFactor(), SeasonalFactor()],
        )


class ResidentialWindTurbine(ProductionDevice):
    """A small residential wind turbine that generates energy based on wind speed"""

    def __init__(self):
        super().__init__(
            device_name="Residential Wind Turbine",
            production_tier=ModerateProductionTier(),
            energy_factors=[WindFactor()],
        )


class IndustrialWindTurbine(ProductionDevice):
    """A large wind turbine for industrial energy production"""

    def __init__(self):
        super().__init__(
            device_name="Industrial Wind Turbine",
            production_tier=HighProductionTier(),
            energy_factors=[WindFactor(), SeasonalFactor()],
        )


class HydroPowerPlant(ProductionDevice):
    """A hydroelectric power plant that produces stable energy"""

    def __init__(self):
        super().__init__(
            device_name="Hydro Power Plant",
            production_tier=VeryHighProductionTier(),
            energy_factors=[],
        )


class DieselGenerator(ProductionDevice):
    """A backup diesel generator that runs mostly during peak hours"""

    def __init__(self):
        super().__init__(
            device_name="Diesel Generator",
            production_tier=HighProductionTier(),
            energy_factors=[PeakHoursFactor(), RandomUsageFactor()],
        )


class IndustrialBackupGenerator(ProductionDevice):
    """A large industrial backup generator that operates unpredictably"""

    def __init__(self):
        super().__init__(
            device_name="Industrial Backup Generator",
            production_tier=ExtremeProductionTier(),
            energy_factors=[RandomUsageFactor()],
        )
