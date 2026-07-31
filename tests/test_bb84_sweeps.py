"""Tests for deterministic BB84 parameter sweeps."""

from __future__ import annotations

import unittest

from bb84_qkd.bb84_finite_key import FiniteKeyParameters
from bb84_qkd.bb84_simulation import SimulationParameters
from bb84_qkd.bb84_sweeps import (
    run_attack_sweep,
    run_finite_key_sweep,
)


class SweepTests(unittest.TestCase):
    def test_invalid_attack_probability_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_attack_sweep(
                [-0.01],
                SimulationParameters(pulses=1_000),
                repeats=1,
            )
        with self.assertRaises(ValueError):
            run_attack_sweep(
                [1.01],
                SimulationParameters(pulses=1_000),
                repeats=1,
            )
        with self.assertRaisesRegex(ValueError, "must be finite"):
            run_attack_sweep(
                [float("nan")],
                SimulationParameters(pulses=1_000),
                repeats=1,
            )

    def test_boolean_sweep_counts_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_attack_sweep(
                [0.0],
                SimulationParameters(pulses=1_000),
                repeats=True,
            )
        with self.assertRaises(ValueError):
            run_finite_key_sweep(
                [True],
                FiniteKeyParameters(pulses=1_000),
                repeats=1,
            )


if __name__ == "__main__":
    unittest.main()
