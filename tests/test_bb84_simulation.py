"""Tests for the report-compatible asymptotic simulator."""

from __future__ import annotations

import unittest
from dataclasses import replace

from bb84_qkd.bb84_simulation import (
    SimulationParameters,
    simulate_bb84,
)


class SimulationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ideal = SimulationParameters(
            pulses=100_000,
            mean_photon_number=1.0,
            intrinsic_bit_fidelity=1.0,
            receiver_efficiency=1.0,
            parameter_estimation_bits=192,
            seed=2025,
            detection_model="linear",
        )

    def test_ideal_channel_has_zero_qber(self) -> None:
        result = simulate_bb84(self.ideal)
        self.assertEqual(result.detected_events, self.ideal.pulses)
        self.assertEqual(result.qber, 0.0)
        self.assertEqual(result.asymptotic_secret_fraction, 1.0)
        self.assertEqual(result.estimated_secret_bits, result.retained_bits)

    def test_full_intercept_resend_is_near_25_percent_qber(self) -> None:
        result = simulate_bb84(
            replace(
                self.ideal,
                intercept_resend_probability=1.0,
            )
        )
        self.assertGreater(result.qber, 0.23)
        self.assertLess(result.qber, 0.27)
        self.assertEqual(result.estimated_secret_bits, 0)
        self.assertGreater(result.intercept_known_retained_bits, 0)

    def test_above_threshold_error_collapses_key(self) -> None:
        result = simulate_bb84(
            replace(
                self.ideal,
                intrinsic_bit_fidelity=0.865,
            )
        )
        self.assertGreater(result.qber, 0.12)
        self.assertEqual(result.asymptotic_secret_fraction, 0.0)
        self.assertEqual(result.estimated_secret_bits, 0)

    def test_results_are_reproducible(self) -> None:
        first = simulate_bb84(self.ideal)
        second = simulate_bb84(self.ideal)
        self.assertEqual(first, second)

    def test_zero_source_or_receiver_efficiency_yields_no_events(self) -> None:
        zero_source = simulate_bb84(replace(self.ideal, mean_photon_number=0.0))
        zero_receiver = simulate_bb84(replace(self.ideal, receiver_efficiency=0.0))
        self.assertEqual(zero_source.detected_events, 0)
        self.assertEqual(zero_receiver.detected_events, 0)
        self.assertEqual(zero_source.estimated_secret_bits, 0)
        self.assertEqual(zero_receiver.estimated_secret_bits, 0)

    def test_disclosure_larger_than_sifted_sequence_is_bounded(self) -> None:
        result = simulate_bb84(
            replace(
                self.ideal,
                pulses=2_000,
                intercept_resend_probability=1.0,
                parameter_estimation_bits=10_000,
            )
        )
        self.assertEqual(result.disclosed_bits, result.sifted_bits)
        self.assertEqual(result.retained_bits, 0)
        self.assertEqual(result.intercept_known_retained_bits, 0)
        self.assertEqual(result.conservative_eve_known_bits, 0)

    def test_invalid_parameter_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SimulationParameters(pulses=0)
        with self.assertRaises(ValueError):
            SimulationParameters(error_correction_efficiency=0.9)
        with self.assertRaises(ValueError):
            SimulationParameters(seed=-1)

    def test_boolean_integer_parameters_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SimulationParameters(pulses=True)
        with self.assertRaises(ValueError):
            SimulationParameters(parameter_estimation_bits=True)
        with self.assertRaises(ValueError):
            SimulationParameters(seed=True)
        with self.assertRaises(ValueError):
            SimulationParameters(mean_photon_number=True)
        with self.assertRaises(ValueError):
            SimulationParameters(error_correction_efficiency=True)

    def test_non_finite_parameters_are_rejected(self) -> None:
        parameter_names = (
            "mean_photon_number",
            "intrinsic_bit_fidelity",
            "receiver_efficiency",
            "intercept_resend_probability",
            "leakage_fraction",
            "error_correction_efficiency",
        )
        for parameter_name in parameter_names:
            for value in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(parameter=parameter_name, value=value):
                    with self.assertRaisesRegex(ValueError, "must be finite"):
                        SimulationParameters(**{parameter_name: value})


if __name__ == "__main__":
    unittest.main()
