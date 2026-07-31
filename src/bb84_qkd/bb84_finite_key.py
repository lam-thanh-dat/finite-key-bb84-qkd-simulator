"""Illustrative finite-size extension of the BB84 simulator."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

from .bb84_math import (
    binary_entropy,
    upper_normal_quantile,
    validate_finite_number,
    validate_probability,
)
from .bb84_simulation import SimulationParameters, simulate_bb84


@dataclass(frozen=True, slots=True)
class FiniteKeyParameters:
    """Input parameters for the illustrative finite-size calculation."""

    pulses: int = 100_000
    mean_photon_number: float = 0.5
    intrinsic_bit_fidelity: float = 0.985
    receiver_efficiency: float = 0.90
    intercept_resend_probability: float = 0.0
    leakage_fraction: float = 0.0
    error_correction_efficiency: float = 1.15
    secrecy_epsilon: float = 1e-9
    correctness_epsilon: float = 1e-9
    seed: int = 2025

    def __post_init__(self) -> None:
        if (
            not isinstance(self.pulses, int)
            or isinstance(self.pulses, bool)
            or self.pulses <= 0
        ):
            raise ValueError("pulses must be a positive integer")
        validate_finite_number("mean_photon_number", self.mean_photon_number)
        if self.mean_photon_number < 0.0:
            raise ValueError("mean_photon_number must be nonnegative")
        validate_probability("intrinsic_bit_fidelity", self.intrinsic_bit_fidelity)
        validate_probability("receiver_efficiency", self.receiver_efficiency)
        validate_probability(
            "intercept_resend_probability",
            self.intercept_resend_probability,
        )
        validate_probability("leakage_fraction", self.leakage_fraction)
        validate_finite_number(
            "error_correction_efficiency",
            self.error_correction_efficiency,
        )
        if self.error_correction_efficiency < 1.0:
            raise ValueError("error_correction_efficiency must be at least 1")
        validate_finite_number("secrecy_epsilon", self.secrecy_epsilon)
        if not 0.0 < self.secrecy_epsilon < 1.0:
            raise ValueError("secrecy_epsilon must be between 0 and 1")
        validate_finite_number("correctness_epsilon", self.correctness_epsilon)
        if not 0.0 < self.correctness_epsilon < 1.0:
            raise ValueError("correctness_epsilon must be between 0 and 1")
        if (
            not isinstance(self.seed, int)
            or isinstance(self.seed, bool)
            or self.seed < 0
        ):
            raise ValueError("seed must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class FiniteKeyResult:
    """Aggregate outputs from one finite-size calculation."""

    emitted_pulses: int
    detection_probability: float
    detected_events: int
    sifted_bits: int
    qber: float
    normal_quantile: float
    statistical_margin: float
    phase_error_upper_bound: float
    error_correction_leakage_bits: float
    privacy_amplification_bits: float
    security_overhead_bits: float
    secure_budget_before_leakage_bits: float
    estimated_secret_bits: int
    finite_secret_fraction: float
    secret_bits_per_pulse: float
    asymptotic_secret_fraction: float
    parameters: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return asdict(self)


def _estimate_from_observations(
    parameters: FiniteKeyParameters,
    *,
    detected_events: int,
    sifted_bits: int,
    qber: float,
    event_probability: float,
) -> FiniteKeyResult:
    """Apply the report-compatible finite-size equations to observations."""

    if sifted_bits < 0:
        raise ValueError("sifted_bits must be nonnegative")
    validate_probability("qber", qber)

    if sifted_bits == 0:
        return FiniteKeyResult(
            emitted_pulses=parameters.pulses,
            detection_probability=event_probability,
            detected_events=detected_events,
            sifted_bits=0,
            qber=0.0,
            normal_quantile=0.0,
            statistical_margin=0.0,
            phase_error_upper_bound=0.0,
            error_correction_leakage_bits=0.0,
            privacy_amplification_bits=0.0,
            security_overhead_bits=0.0,
            secure_budget_before_leakage_bits=0.0,
            estimated_secret_bits=0,
            finite_secret_fraction=0.0,
            secret_bits_per_pulse=0.0,
            asymptotic_secret_fraction=0.0,
            parameters=asdict(parameters),
        )

    normal_quantile = upper_normal_quantile(parameters.secrecy_epsilon / 2.0)
    variance_term = max(qber * (1.0 - qber), 1e-12)
    statistical_margin = normal_quantile * math.sqrt(variance_term / sifted_bits)
    phase_error_upper_bound = min(qber + statistical_margin, 0.5)

    ec_leakage_bits = (
        sifted_bits * parameters.error_correction_efficiency * binary_entropy(qber)
    )
    privacy_amplification_bits = sifted_bits * binary_entropy(phase_error_upper_bound)
    security_overhead_bits = 2.0 * math.log2(
        1.0 / parameters.secrecy_epsilon
    ) + math.log2(2.0 / parameters.correctness_epsilon)
    secure_budget = (
        sifted_bits
        - ec_leakage_bits
        - privacy_amplification_bits
        - security_overhead_bits
    )
    estimated_secret_bits = math.floor(
        max(
            0.0,
            secure_budget * (1.0 - parameters.leakage_fraction),
        )
    )
    finite_secret_fraction = estimated_secret_bits / sifted_bits
    secret_bits_per_pulse = estimated_secret_bits / parameters.pulses

    qber_entropy = binary_entropy(qber)
    asymptotic_secret_fraction = max(
        0.0,
        1.0 - qber_entropy - parameters.error_correction_efficiency * qber_entropy,
    ) * (1.0 - parameters.leakage_fraction)

    return FiniteKeyResult(
        emitted_pulses=parameters.pulses,
        detection_probability=event_probability,
        detected_events=detected_events,
        sifted_bits=sifted_bits,
        qber=qber,
        normal_quantile=normal_quantile,
        statistical_margin=statistical_margin,
        phase_error_upper_bound=phase_error_upper_bound,
        error_correction_leakage_bits=ec_leakage_bits,
        privacy_amplification_bits=privacy_amplification_bits,
        security_overhead_bits=security_overhead_bits,
        secure_budget_before_leakage_bits=secure_budget,
        estimated_secret_bits=estimated_secret_bits,
        finite_secret_fraction=finite_secret_fraction,
        secret_bits_per_pulse=secret_bits_per_pulse,
        asymptotic_secret_fraction=asymptotic_secret_fraction,
        parameters=asdict(parameters),
    )


def run_finite_key_trial(
    parameters: FiniteKeyParameters,
) -> FiniteKeyResult:
    """Run one channel trial and apply the illustrative finite-size penalty."""

    channel_result = simulate_bb84(
        SimulationParameters(
            pulses=parameters.pulses,
            mean_photon_number=parameters.mean_photon_number,
            intrinsic_bit_fidelity=parameters.intrinsic_bit_fidelity,
            receiver_efficiency=parameters.receiver_efficiency,
            intercept_resend_probability=(parameters.intercept_resend_probability),
            leakage_fraction=parameters.leakage_fraction,
            parameter_estimation_bits=0,
            error_correction_efficiency=(parameters.error_correction_efficiency),
            seed=parameters.seed,
            detection_model="poisson",
        )
    )
    return _estimate_from_observations(
        parameters,
        detected_events=channel_result.detected_events,
        sifted_bits=channel_result.sifted_bits,
        qber=channel_result.qber,
        event_probability=channel_result.detection_probability,
    )


def estimate_finite_key_from_observations(
    parameters: FiniteKeyParameters,
    *,
    sifted_bits: int,
    qber: float,
) -> FiniteKeyResult:
    """Evaluate the finite-size equations for fixed aggregate observations.

    This helper is useful for deterministic sensitivity studies. The detected
    event count is set equal to the sifted count because it is not required by
    the finite-size equations implemented here.
    """

    event_probability = 1.0 - math.exp(
        -parameters.mean_photon_number * parameters.receiver_efficiency
    )
    return _estimate_from_observations(
        parameters,
        detected_events=sifted_bits,
        sifted_bits=sifted_bits,
        qber=qber,
        event_probability=event_probability,
    )
