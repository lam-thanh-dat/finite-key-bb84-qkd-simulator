"""Tests for the illustrative finite-size model."""

from __future__ import annotations

import unittest

from bb84_qkd.bb84_finite_key import (
    FiniteKeyParameters,
    estimate_finite_key_from_observations,
    run_finite_key_trial,
)


class FiniteKeyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = FiniteKeyParameters(
            pulses=1_000_000,
            mean_photon_number=0.4,
            intrinsic_bit_fidelity=0.98,
            receiver_efficiency=0.9,
            seed=2025,
        )

    def test_finite_fraction_increases_with_sample_size(self) -> None:
        small = estimate_finite_key_from_observations(
            self.parameters,
            sifted_bits=10_000,
            qber=0.02,
        )
        large = estimate_finite_key_from_observations(
            self.parameters,
            sifted_bits=1_000_000,
            qber=0.02,
        )
        self.assertLess(
            small.finite_secret_fraction,
            large.finite_secret_fraction,
        )
        self.assertLessEqual(
            large.finite_secret_fraction,
            large.asymptotic_secret_fraction,
        )

    def test_high_qber_produces_no_secret_bits(self) -> None:
        result = estimate_finite_key_from_observations(
            self.parameters,
            sifted_bits=100_000,
            qber=0.15,
        )
        self.assertEqual(result.estimated_secret_bits, 0)
        self.assertEqual(result.finite_secret_fraction, 0.0)

    def test_trial_is_reproducible(self) -> None:
        first = run_finite_key_trial(self.parameters)
        second = run_finite_key_trial(self.parameters)
        self.assertEqual(first, second)
        self.assertGreater(first.sifted_bits, 0)

    def test_zero_source_or_receiver_efficiency_yields_no_key(self) -> None:
        zero_source = run_finite_key_trial(FiniteKeyParameters(mean_photon_number=0.0))
        zero_receiver = run_finite_key_trial(
            FiniteKeyParameters(receiver_efficiency=0.0)
        )
        self.assertEqual(zero_source.detected_events, 0)
        self.assertEqual(zero_receiver.detected_events, 0)
        self.assertEqual(zero_source.estimated_secret_bits, 0)
        self.assertEqual(zero_receiver.estimated_secret_bits, 0)

    def test_invalid_security_parameter_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            FiniteKeyParameters(secrecy_epsilon=0.0)
        with self.assertRaises(ValueError):
            FiniteKeyParameters(seed=-1)

    def test_boolean_integer_parameters_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            FiniteKeyParameters(pulses=True)
        with self.assertRaises(ValueError):
            FiniteKeyParameters(seed=True)
        with self.assertRaises(ValueError):
            FiniteKeyParameters(mean_photon_number=True)
        with self.assertRaises(ValueError):
            FiniteKeyParameters(error_correction_efficiency=True)

    def test_non_finite_parameters_are_rejected(self) -> None:
        parameter_names = (
            "mean_photon_number",
            "intrinsic_bit_fidelity",
            "receiver_efficiency",
            "intercept_resend_probability",
            "leakage_fraction",
            "error_correction_efficiency",
            "secrecy_epsilon",
            "correctness_epsilon",
        )
        for parameter_name in parameter_names:
            for value in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(parameter=parameter_name, value=value):
                    with self.assertRaisesRegex(ValueError, "must be finite"):
                        FiniteKeyParameters(**{parameter_name: value})

    def test_non_finite_observed_qber_is_rejected(self) -> None:
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "qber must be finite"):
                    estimate_finite_key_from_observations(
                        self.parameters,
                        sifted_bits=100_000,
                        qber=value,
                    )


if __name__ == "__main__":
    unittest.main()
