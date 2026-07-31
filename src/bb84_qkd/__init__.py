"""Educational BB84 QKD simulation package."""

from importlib.metadata import PackageNotFoundError, version

from .bb84_finite_key import (
    FiniteKeyParameters,
    FiniteKeyResult,
    estimate_finite_key_from_observations,
    run_finite_key_trial,
)
from .bb84_math import (
    binary_entropy,
    critical_qber,
    detection_probability,
)
from .bb84_simulation import (
    SimulationParameters,
    SimulationResult,
    simulate_bb84,
)

__all__ = [
    "FiniteKeyParameters",
    "FiniteKeyResult",
    "SimulationParameters",
    "SimulationResult",
    "binary_entropy",
    "critical_qber",
    "detection_probability",
    "estimate_finite_key_from_observations",
    "run_finite_key_trial",
    "simulate_bb84",
]

try:
    __version__ = version("finite-key-bb84-qkd-simulator")
except PackageNotFoundError:
    __version__ = "0+unknown"
