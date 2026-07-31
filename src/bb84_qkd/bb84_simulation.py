"""Report-compatible Monte Carlo model for asymptotic BB84 analysis."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .bb84_math import (
    DetectionModel,
    binary_entropy,
    detection_probability,
    validate_finite_number,
    validate_probability,
)


@dataclass(frozen=True, slots=True)
class SimulationParameters:
    """Input parameters for one asymptotic BB84 simulation."""

    pulses: int = 100_000
    mean_photon_number: float = 0.5
    intrinsic_bit_fidelity: float = 0.985
    receiver_efficiency: float = 0.90
    intercept_resend_probability: float = 0.0
    leakage_fraction: float = 0.0
    parameter_estimation_bits: int = 192
    error_correction_efficiency: float = 1.15
    seed: int = 2025
    detection_model: DetectionModel = "linear"

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
        if (
            not isinstance(self.parameter_estimation_bits, int)
            or isinstance(self.parameter_estimation_bits, bool)
            or self.parameter_estimation_bits < 0
        ):
            raise ValueError("parameter_estimation_bits must be a nonnegative integer")
        validate_finite_number(
            "error_correction_efficiency",
            self.error_correction_efficiency,
        )
        if self.error_correction_efficiency < 1.0:
            raise ValueError("error_correction_efficiency must be at least 1")
        if (
            not isinstance(self.seed, int)
            or isinstance(self.seed, bool)
            or self.seed < 0
        ):
            raise ValueError("seed must be a nonnegative integer")
        detection_probability(
            self.mean_photon_number,
            self.receiver_efficiency,
            self.detection_model,
        )


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Aggregate outputs from one asymptotic BB84 simulation."""

    emitted_pulses: int
    detection_probability: float
    detected_events: int
    sifted_bits: int
    disclosed_bits: int
    retained_bits: int
    qber: float
    channel_flip_events: int
    intercept_resend_flip_events: int
    error_correction_leakage_fraction: float
    asymptotic_secret_fraction: float
    estimated_secret_bits: int
    intercept_known_retained_bits: int
    heuristic_leakage_bits: int
    conservative_eve_known_bits: int
    parameters: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return asdict(self)


def simulate_bb84(parameters: SimulationParameters) -> SimulationResult:
    """Run one report-compatible BB84 Monte Carlo trial.

    QBER is evaluated over all sifted bits, matching the original project code.
    ``parameter_estimation_bits`` is then deducted from the available key
    budget. This is a pedagogical accounting model, not an implementation of a
    real parameter-estimation protocol.
    """

    rng = np.random.default_rng(parameters.seed)
    event_probability = detection_probability(
        parameters.mean_photon_number,
        parameters.receiver_efficiency,
        parameters.detection_model,
    )

    alice_bits = rng.integers(0, 2, parameters.pulses, dtype=np.int8)
    alice_bases = rng.integers(0, 2, parameters.pulses, dtype=np.int8)
    detected = rng.random(parameters.pulses) < event_probability
    bob_bases = rng.integers(0, 2, parameters.pulses, dtype=np.int8)

    attacked = rng.random(parameters.pulses) < parameters.intercept_resend_probability
    eve_bases = rng.integers(0, 2, parameters.pulses, dtype=np.int8)

    channel_flip_probability = 1.0 - parameters.intrinsic_bit_fidelity
    channel_flips = rng.random(parameters.pulses) < channel_flip_probability
    eve_wrong_basis = attacked & (eve_bases != alice_bases)
    eve_randomized_flip = (rng.random(parameters.pulses) < 0.5) & eve_wrong_basis

    bob_bits = (
        alice_bits ^ channel_flips.astype(np.int8) ^ eve_randomized_flip.astype(np.int8)
    )
    wrong_bob_basis = bob_bases != alice_bases
    random_measurements = rng.integers(0, 2, parameters.pulses, dtype=np.int8)
    bob_bits = np.where(wrong_bob_basis, random_measurements, bob_bits)

    detected_alice_bits = alice_bits[detected]
    detected_alice_bases = alice_bases[detected]
    detected_bob_bits = bob_bits[detected]
    detected_bob_bases = bob_bases[detected]
    sift_mask = detected_alice_bases == detected_bob_bases

    alice_sifted = detected_alice_bits[sift_mask]
    bob_sifted = detected_bob_bits[sift_mask]
    sifted_bits = int(alice_sifted.size)
    detected_events = int(np.count_nonzero(detected))

    if sifted_bits == 0:
        return SimulationResult(
            emitted_pulses=parameters.pulses,
            detection_probability=event_probability,
            detected_events=detected_events,
            sifted_bits=0,
            disclosed_bits=0,
            retained_bits=0,
            qber=0.0,
            channel_flip_events=0,
            intercept_resend_flip_events=0,
            error_correction_leakage_fraction=0.0,
            asymptotic_secret_fraction=0.0,
            estimated_secret_bits=0,
            intercept_known_retained_bits=0,
            heuristic_leakage_bits=0,
            conservative_eve_known_bits=0,
            parameters=asdict(parameters),
        )

    qber = float(np.mean(alice_sifted != bob_sifted))
    disclosed_bits = min(parameters.parameter_estimation_bits, sifted_bits)
    retained_bits = sifted_bits - disclosed_bits
    retained_mask = np.ones(sifted_bits, dtype=bool)
    if disclosed_bits:
        disclosed_indices = rng.choice(
            sifted_bits,
            size=disclosed_bits,
            replace=False,
        )
        retained_mask[disclosed_indices] = False

    entropy = binary_entropy(qber)
    ec_leakage_fraction = parameters.error_correction_efficiency * entropy
    base_secret_fraction = max(1.0 - ec_leakage_fraction - entropy, 0.0)
    secret_fraction = base_secret_fraction * (1.0 - parameters.leakage_fraction)
    estimated_secret_bits = math.floor(retained_bits * secret_fraction)

    sifted_channel_flips = channel_flips[detected][sift_mask]
    sifted_eve_flips = eve_randomized_flip[detected][sift_mask]
    channel_flip_events = int(np.count_nonzero(sifted_channel_flips))
    intercept_flip_events = int(np.count_nonzero(sifted_eve_flips))

    sifted_attacked = attacked[detected][sift_mask]
    sifted_eve_bases = eve_bases[detected][sift_mask]
    sifted_alice_bases = detected_alice_bases[sift_mask]
    intercept_known_mask = sifted_attacked & (sifted_eve_bases == sifted_alice_bases)
    intercept_known_retained = int(
        np.count_nonzero(intercept_known_mask[retained_mask])
    )
    heuristic_leakage_bits = math.floor(retained_bits * parameters.leakage_fraction)
    conservative_eve_known_bits = min(
        retained_bits,
        intercept_known_retained + heuristic_leakage_bits,
    )

    return SimulationResult(
        emitted_pulses=parameters.pulses,
        detection_probability=event_probability,
        detected_events=detected_events,
        sifted_bits=sifted_bits,
        disclosed_bits=disclosed_bits,
        retained_bits=retained_bits,
        qber=qber,
        channel_flip_events=channel_flip_events,
        intercept_resend_flip_events=intercept_flip_events,
        error_correction_leakage_fraction=ec_leakage_fraction,
        asymptotic_secret_fraction=secret_fraction,
        estimated_secret_bits=estimated_secret_bits,
        intercept_known_retained_bits=intercept_known_retained,
        heuristic_leakage_bits=heuristic_leakage_bits,
        conservative_eve_known_bits=conservative_eve_known_bits,
        parameters=asdict(parameters),
    )
