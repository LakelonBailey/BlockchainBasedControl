from src.devices.consumption.base import ConsumptionDevice
from src.devices.general.energy_factors import (
    PeakHoursFactor,
    WeekendFactor,
    SolarFactor,
    SeasonalFactor,
    RandomUsageFactor,
)
from src.devices.consumption.tiers import (
    LowerPowerTier,
    LowPowerTier,
    MediumPowerTier,
    HighPowerTier,
    HigherPowerTier,
)


class LEDLight(ConsumptionDevice):
    """A simple LED light with peak-hour increased usage"""

    def __init__(self):
        super().__init__(
            device_name="LED Light",
            consumption_tier=LowerPowerTier(),
            energy_factors=[RandomUsageFactor()],
        )


class DesktopComputer(ConsumptionDevice):
    """A desktop computer that consumes slightly more energy on weekends"""

    def __init__(self):
        super().__init__(
            device_name="Desktop Computer",
            consumption_tier=LowPowerTier(),
            energy_factors=[RandomUsageFactor()],
        )


class WashingMachine(ConsumptionDevice):
    """A washing machine that has random energy spikes when in use"""

    def __init__(self):
        super().__init__(
            device_name="Washing Machine",
            consumption_tier=MediumPowerTier(),
            energy_factors=[RandomUsageFactor()],
        )


# class ElectricOven(ConsumptionDevice):
#     """An electric oven that is more likely to be used on weekends and peak hours"""

#     def __init__(self):
#         super().__init__(
#             device_name="Electric Oven",
#             consumption_tier=MediumPowerTier(),
#             energy_factors=[WeekendFactor(), PeakHoursFactor()],
#         )


class AirConditioner(ConsumptionDevice):
    """An air conditioner that consumes more power in the summer"""

    def __init__(self):
        super().__init__(
            device_name="Air Conditioner",
            consumption_tier=HighPowerTier(),
            energy_factors=[RandomUsageFactor()],
        )


class EVCharger(ConsumptionDevice):
    """An electric vehicle charger that uses the most power and follows peak hours"""

    def __init__(self):
        super().__init__(
            device_name="EV Charger",
            consumption_tier=HigherPowerTier(),
            energy_factors=[RandomUsageFactor()],
        )


# class IndustrialHVAC(ConsumptionDevice):
#     """
#     An industrial HVAC system that uses more power in the summer and operates
#     unpredictably
#     """

#     def __init__(self):
#         super().__init__(
#             device_name="Industrial HVAC",
#             consumption_tier=HigherPowerTier(),
#             energy_factors=[SeasonalFactor(), RandomUsageFactor()],
#         )


# class SolarPoweredDevice(ConsumptionDevice):
#     """A device that only functions efficiently when solar energy is available"""

#     def __init__(self):
#         super().__init__(
#             device_name="Solar Powered Device",
#             consumption_tier=LowPowerTier(),
#             energy_factors=[SolarFactor()],
#         )


# class SmartHomeSystem(ConsumptionDevice):
#     """
#     A smart home system that operates at minimal power but increases usage on
#     weekends
#     """

#     def __init__(self):
#         super().__init__(
#             device_name="Smart Home System",
#             consumption_tier=LowerPowerTier(),
#             energy_factors=[WeekendFactor()],
#         )


# class Microwave(ConsumptionDevice):
#     """A microwave that consumes high energy in short bursts, randomly used"""

#     def __init__(self):
#         super().__init__(
#             device_name="Microwave",
#             consumption_tier=MediumPowerTier(),
#             energy_factors=[RandomUsageFactor()],
#         )
