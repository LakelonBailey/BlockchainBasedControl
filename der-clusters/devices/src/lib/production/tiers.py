from src.lib.production.base import ProductionTier


class LowProductionTier(ProductionTier):
    """
    Tier 1: Low-scale energy production (e.g., small solar panels, micro wind turbines)
    """

    def __init__(self):
        super().__init__(default_kw=0.3, tier_no=1)


class ModerateProductionTier(ProductionTier):
    """
    Tier 2: Moderate energy production (e.g., residential solar panels, small wind
    turbines)
    """

    def __init__(self):
        super().__init__(default_kw=5.0, tier_no=2)


class HighProductionTier(ProductionTier):
    """
    Tier 3: High energy production (e.g., mid-sized wind turbines, larger solar farms)
    """

    def __init__(self):
        super().__init__(default_kw=10.0, tier_no=3)


class VeryHighProductionTier(ProductionTier):
    """
    Tier 4: Very high energy production (e.g., industrial wind turbines, hydroelectric
    power)
    """

    def __init__(self):
        super().__init__(default_kw=50.0, tier_no=4)


class ExtremeProductionTier(ProductionTier):
    """
    Tier 5: Extreme energy production (e.g., large power plants, industrial-scale
    generation)
    """

    def __init__(self):
        super().__init__(default_kw=100.0, tier_no=5)
