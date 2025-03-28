import importlib
import inspect
from typing import Literal
from src.devices.general.base import Device
from src.devices.consumption.base import ConsumptionDevice
from src.devices.production.base import ProductionDevice


def get_device_name_map(device_type: Literal["production", "consumption"] = None):
    all_classes = []
    production_devices_module = importlib.import_module(
        "src.devices.production.devices"
    )
    consumption_devices_module = importlib.import_module(
        "src.devices.consumption.devices"
    )
    if device_type is None:
        all_classes.extend(
            inspect.getmembers(production_devices_module, inspect.isclass)
        )
        all_classes.extend(
            inspect.getmembers(consumption_devices_module, inspect.isclass)
        )
    elif device_type == "production":
        all_classes.extend(
            inspect.getmembers(production_devices_module, inspect.isclass)
        )
    elif device_type == "consumption":
        all_classes.extend(
            inspect.getmembers(consumption_devices_module, inspect.isclass)
        )
    else:
        raise ValueError(f"Invalid device_type arg: {device_type}")

    return {
        name: cls
        for name, cls in all_classes
        if issubclass(cls, Device)
        and cls is not Device
        and cls is not ConsumptionDevice
        and cls is not ProductionDevice
    }
