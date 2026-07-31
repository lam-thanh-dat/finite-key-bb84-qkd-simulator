"""Reproducible multi-run sweeps for the BB84 models."""

from __future__ import annotations

import math
import statistics
from collections.abc import Iterable
from dataclasses import replace

from .bb84_finite_key import FiniteKeyParameters, run_finite_key_trial
from .bb84_math import validate_probability
from .bb84_simulation import SimulationParameters, simulate_bb84


def _summary(values: list[float]) -> dict[str, float]:
    if not values:
        raise ValueError("at least one value is required")
    mean = statistics.fmean(values)
    if len(values) == 1:
        standard_deviation = 0.0
        half_width = 0.0
    else:
        standard_deviation = statistics.stdev(values)
        half_width = 1.96 * standard_deviation / math.sqrt(len(values))
    return {
        "mean": mean,
        "standard_deviation": standard_deviation,
        "ci95_low": mean - half_width,
        "ci95_high": mean + half_width,
    }


def run_attack_sweep(
    attack_probabilities: Iterable[float],
    base_parameters: SimulationParameters,
    *,
    repeats: int = 8,
) -> list[dict[str, float | int]]:
    """Sweep intercept-resend probability with independent deterministic seeds."""

    if not isinstance(repeats, int) or isinstance(repeats, bool) or repeats <= 0:
        raise ValueError("repeats must be a positive integer")

    rows: list[dict[str, float | int]] = []
    for point_index, attack_probability in enumerate(attack_probabilities):
        if isinstance(attack_probability, bool):
            raise ValueError("attack probabilities must be numeric probabilities")
        attack_probability = float(attack_probability)
        validate_probability("intercept_resend_probability", attack_probability)
        qber_values: list[float] = []
        secret_fraction_values: list[float] = []
        secret_bits_per_pulse: list[float] = []
        for repeat_index in range(repeats):
            seed = base_parameters.seed + point_index * 100_003 + repeat_index
            result = simulate_bb84(
                replace(
                    base_parameters,
                    intercept_resend_probability=attack_probability,
                    seed=seed,
                )
            )
            qber_values.append(result.qber)
            secret_fraction_values.append(result.asymptotic_secret_fraction)
            secret_bits_per_pulse.append(
                result.estimated_secret_bits / result.emitted_pulses
            )

        qber_summary = _summary(qber_values)
        secret_summary = _summary(secret_fraction_values)
        pulse_summary = _summary(secret_bits_per_pulse)
        rows.append(
            {
                "intercept_resend_probability": attack_probability,
                "repeats": repeats,
                "qber_mean": qber_summary["mean"],
                "qber_ci95_low": qber_summary["ci95_low"],
                "qber_ci95_high": qber_summary["ci95_high"],
                "secret_fraction_mean": secret_summary["mean"],
                "secret_fraction_ci95_low": secret_summary["ci95_low"],
                "secret_fraction_ci95_high": secret_summary["ci95_high"],
                "secret_bits_per_pulse_mean": pulse_summary["mean"],
            }
        )
    return rows


def run_finite_key_sweep(
    pulse_counts: Iterable[int],
    base_parameters: FiniteKeyParameters,
    *,
    repeats: int = 5,
) -> list[dict[str, float | int]]:
    """Sweep block size with independent deterministic seeds."""

    if not isinstance(repeats, int) or isinstance(repeats, bool) or repeats <= 0:
        raise ValueError("repeats must be a positive integer")

    rows: list[dict[str, float | int]] = []
    for point_index, pulses in enumerate(pulse_counts):
        if not isinstance(pulses, int) or isinstance(pulses, bool) or pulses <= 0:
            raise ValueError("pulse counts must be positive integers")
        finite_fraction_values: list[float] = []
        asymptotic_fraction_values: list[float] = []
        qber_values: list[float] = []
        bits_per_pulse_values: list[float] = []
        for repeat_index in range(repeats):
            seed = base_parameters.seed + point_index * 100_003 + repeat_index
            result = run_finite_key_trial(
                replace(
                    base_parameters,
                    pulses=int(pulses),
                    seed=seed,
                )
            )
            finite_fraction_values.append(result.finite_secret_fraction)
            asymptotic_fraction_values.append(result.asymptotic_secret_fraction)
            qber_values.append(result.qber)
            bits_per_pulse_values.append(result.secret_bits_per_pulse)

        finite_summary = _summary(finite_fraction_values)
        asymptotic_summary = _summary(asymptotic_fraction_values)
        qber_summary = _summary(qber_values)
        pulse_summary = _summary(bits_per_pulse_values)
        rows.append(
            {
                "pulses": int(pulses),
                "repeats": repeats,
                "qber_mean": qber_summary["mean"],
                "finite_secret_fraction_mean": finite_summary["mean"],
                "finite_secret_fraction_ci95_low": finite_summary["ci95_low"],
                "finite_secret_fraction_ci95_high": finite_summary["ci95_high"],
                "asymptotic_secret_fraction_mean": (asymptotic_summary["mean"]),
                "secret_bits_per_pulse_mean": pulse_summary["mean"],
            }
        )
    return rows
