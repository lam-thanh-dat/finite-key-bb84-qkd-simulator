"""Smoke tests for the command-line interface."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from bb84_qkd.bb84_cli import main


class CliTests(unittest.TestCase):
    def test_simulate_command_outputs_json(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(
                [
                    "simulate",
                    "--pulses",
                    "10000",
                    "--mean-photon-number",
                    "1",
                    "--intrinsic-bit-fidelity",
                    "1",
                    "--receiver-efficiency",
                    "1",
                ]
            )
        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["emitted_pulses"], 10_000)
        self.assertEqual(payload["qber"], 0.0)

    def test_threshold_command(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(["threshold"])
        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertGreater(payload["critical_qber"], 0.098)
        self.assertLess(payload["critical_qber"], 0.0995)

    def test_finite_command_writes_json_file(self) -> None:
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "nested" / "finite_result.json"
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "finite",
                        "--pulses",
                        "10000",
                        "--output",
                        str(output_path),
                    ]
                )
            printed_payload = json.loads(stdout.getvalue())
            file_payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(file_payload, printed_payload)
        self.assertEqual(file_payload["emitted_pulses"], 10_000)

    def test_invalid_values_return_nonzero_status(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "simulate",
                        "--receiver-efficiency",
                        "1.5",
                    ]
                )
        self.assertEqual(exit_code, 2)
        self.assertIn("receiver_efficiency", stderr.getvalue())

    def test_negative_seed_returns_nonzero_status(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = main(["simulate", "--seed", "-1"])
        self.assertEqual(exit_code, 2)
        self.assertIn("seed must be a nonnegative integer", stderr.getvalue())

    def test_non_finite_simulation_input_returns_validation_error(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "simulate",
                        "--mean-photon-number",
                        "nan",
                    ]
                )
        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("mean_photon_number must be finite", stderr.getvalue())

    def test_non_finite_threshold_input_returns_validation_error(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "threshold",
                        "--error-correction-efficiency",
                        "nan",
                    ]
                )
        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn(
            "error_correction_efficiency must be finite",
            stderr.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
