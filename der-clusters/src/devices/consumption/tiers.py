from src.devices.consumption.base import ConsumptionTier


class LowerPowerTier(ConsumptionTier):
    """
    Tier 1: Minimal energy consumption devices (LED lights, routers, phone chargers)
    """

    def __init__(self):
        super().__init__(default_kw=1, tier_no=1)


class LowPowerTier(ConsumptionTier):
    """
    Tier 2: Small household electronics (TVs, desktop computers, microwaves on standby)
    """

    def __init__(self):
        super().__init__(default_kw=2, tier_no=2)


class MediumPowerTier(ConsumptionTier):
    """
    Tier 3: Moderate appliances (Washing machines, ovens, microwaves in use)
    """

    def __init__(self):
        super().__init__(default_kw=3, tier_no=3)


class HighPowerTier(ConsumptionTier):
    """
    Tier 4: High power appliances (Air conditioners, dryers, electric stoves)
    """

    def __init__(self):
        super().__init__(default_kw=4, tier_no=4)


class HigherPowerTier(ConsumptionTier):
    """
    Tier 5: Extreme energy usage devices (EV chargers, industrial HVAC, electric
    furnaces)
    """

    def __init__(self):
        super().__init__(default_kw=5, tier_no=5)
