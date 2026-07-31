"""Mathematical helpers shared by the finite-key BB84 models."""

from __future__ import annotations

import math
from numbers import Real
from typing import Literal

DetectionModel = Literal["linear", "poisson"]


def validate_finite_number(name: str, value: float) -> None:
    """Require a finite real-valued parameter."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real number")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def validate_probability(name: str, value: float) -> None:
    """Validate a finite scalar probability."""

    validate_finite_number(name, value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be in [0, 1]")


def binary_entropy(probability: float) -> float:
    """Return the binary Shannon entropy in bits.

    The endpoint values are handled exactly so an ideal zero-error channel does
    not acquire a small numerical penalty.
    """

    validate_probability("probability", probability)
    if probability in (0.0, 1.0):
        return 0.0
    return -probability * math.log2(probability) - (1.0 - probability) * math.log2(
        1.0 - probability
    )


def detection_probability(
    mean_photon_number: float,
    receiver_efficiency: float,
    model: DetectionModel,
) -> float:
    """Return the event-detection probability for the selected source model."""

    validate_finite_number("mean_photon_number", mean_photon_number)
    if mean_photon_number < 0.0:
        raise ValueError("mean_photon_number must be nonnegative")
    validate_probability("receiver_efficiency", receiver_efficiency)

    mean_detected_photons = mean_photon_number * receiver_efficiency
    if model == "linear":
        return min(mean_detected_photons, 1.0)
    if model == "poisson":
        return 1.0 - math.exp(-mean_detected_photons)
    raise ValueError(f"unsupported detection model: {model!r}")


def upper_normal_quantile(tail_probability: float) -> float:
    """Approximate the upper-tail standard-normal quantile.

    The approximation is the same Hastings-style rational form used by the
    original finite-size simulator. It is retained for report compatibility,
    not presented as a rigorous concentration bound.
    """

    validate_finite_number("tail_probability", tail_probability)
    if not 0.0 < tail_probability < 0.5:
        raise ValueError("tail_probability must be between 0 and 0.5")

    t_value = math.sqrt(-2.0 * math.log(tail_probability))
    numerator = 2.515517 + 0.802853 * t_value + 0.010328 * t_value**2
    denominator = (
        1.0 + 1.432788 * t_value + 0.189269 * t_value**2 + 0.001308 * t_value**3
    )
    return t_value - numerator / denominator


def critical_qber(error_correction_efficiency: float) -> float:
    """Solve ``(1 + f_EC) h_2(Q) = 1`` on the interval [0, 0.5]."""

    validate_finite_number(
        "error_correction_efficiency",
        error_correction_efficiency,
    )
    if error_correction_efficiency < 1.0:
        raise ValueError("error_correction_efficiency must be at least 1")

    lower = 0.0
    upper = 0.5
    for _ in range(100):
        midpoint = (lower + upper) / 2.0
        value = (1.0 + error_correction_efficiency) * binary_entropy(midpoint)
        if value < 1.0:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2.0
