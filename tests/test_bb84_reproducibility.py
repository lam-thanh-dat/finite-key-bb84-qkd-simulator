"""Tests for result drift detection and paper-figure synchronization."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


def _load_reproduction_script() -> ModuleType:
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "reproduce_bb84_results.py"
    )
    specification = importlib.util.spec_from_file_location(
        "reproduce_bb84_results",
        script_path,
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load reproduction script")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


REPRODUCTION_SCRIPT = _load_reproduction_script()


class ReproducibilityTests(unittest.TestCase):
    def test_generated_csv_uses_lf_line_endings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "generated.csv"
            rows = [
                {"pulses": 1000, "qber": 0.01},
                {"pulses": 2000, "qber": 0.02},
            ]

            REPRODUCTION_SCRIPT._write_csv(csv_path, rows)

            csv_bytes = csv_path.read_bytes()
            self.assertIn(b"\n", csv_bytes)
            self.assertNotIn(b"\r\n", csv_bytes)

    def test_paper_figures_are_synchronized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            results_dir = root / "results"
            paper_dir = root / "paper" / "figures"
            results_dir.mkdir()
            expected = {
                "bb84_intercept_resend_sweep.pdf": b"attack figure",
                "bb84_finite_key_scaling.pdf": b"finite figure",
            }
            for file_name, content in expected.items():
                (results_dir / file_name).write_bytes(content)

            REPRODUCTION_SCRIPT.synchronize_paper_figures(
                results_dir,
                paper_dir,
            )

            for file_name, content in expected.items():
                self.assertEqual(
                    (paper_dir / file_name).read_bytes(),
                    content,
                )

    def test_numerical_result_drift_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generated_dir = root / "generated"
            tracked_dir = root / "tracked"
            generated_dir.mkdir()
            tracked_dir.mkdir()
            file_names = (
                "bb84_reference_scenarios.json",
                "bb84_intercept_resend_sweep.csv",
                "bb84_finite_key_scaling.csv",
            )
            for file_name in file_names:
                (generated_dir / file_name).write_text(
                    "same\n",
                    encoding="utf-8",
                )
                (tracked_dir / file_name).write_text(
                    "same\n",
                    encoding="utf-8",
                )

            self.assertEqual(
                REPRODUCTION_SCRIPT.find_numerical_result_drift(
                    generated_dir,
                    tracked_dir,
                ),
                [],
            )

            drifted_name = "bb84_finite_key_scaling.csv"
            (tracked_dir / drifted_name).write_text(
                "stale\n",
                encoding="utf-8",
            )
            self.assertEqual(
                REPRODUCTION_SCRIPT.find_numerical_result_drift(
                    generated_dir,
                    tracked_dir,
                ),
                [drifted_name],
            )


if __name__ == "__main__":
    unittest.main()
