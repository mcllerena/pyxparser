"""Constants used throughout the pyxparser package."""

from enum import Enum


class VariableLimits(float, Enum):
    """Variable limit values."""

    INFINITY = 99999.0
    NEG_INFINITY = -99999.0
    BASE_POWER = 100.0
    DEFAULT_VMAX = 1.100
    DEFAULT_VMIN = 0.950


INFINITY_VALUE = VariableLimits.INFINITY.value
BASE_POWER_MVA = VariableLimits.BASE_POWER.value
DEFAULT_VMAX = VariableLimits.DEFAULT_VMAX.value
DEFAULT_VMIN = VariableLimits.DEFAULT_VMIN.value
