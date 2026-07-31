"""Tests for mathematical helper functions."""

from __future__ import annotations

import math
import unittest

from bb84_qkd.bb84_math import (
    binary_entropy,
    critical_qber,
    detection_probability,
    upper_normal_quantile,
)


class MathUtilsTests(unittest.TestCase):
    def test_binary_entropy_endpoints_and_symmetry(self) -> None:
        self.assertEqual(binary_entropy(0.0), 0.0)
        self.assertEqual(binary_entropy(1.0), 0.0)
        self.assertEqual(binary_entropy(0.5), 1.0)
        self.assertAlmostEqual(
            binary_entropy(0.2),
            binary_entropy(0.8),
            places=14,
        )

    def test_detection_models(self) -> None:
        self.assertAlmostEqual(
            detection_probability(0.4, 0.9, "linear"),
            0.36,
        )
        self.assertAlmostEqual(
            detection_probability(0.4, 0.9, "poisson"),
            1.0 - math.exp(-0.36),
        )
        self.assertEqual(
            detection_probability(2.0, 1.0, "linear"),
            1.0,
        )

    def test_upper_normal_quantile(self) -> None:
        self.assertAlmostEqual(
            upper_normal_quantile(0.025),
            1.96,
            places=2,
        )

    def test_critical_qber(self) -> None:
        threshold = critical_qber(1.15)
        self.assertGreater(threshold, 0.098)
        self.assertLess(threshold, 0.0995)
        self.assertAlmostEqual(
            2.15 * binary_entropy(threshold),
            1.0,
            places=12,
        )

    def test_invalid_probability_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            binary_entropy(-0.01)
        with self.assertRaises(ValueError):
            detection_probability(0.4, 1.1, "linear")


if __name__ == "__main__":
    unittest.main()
