"""Command-line interface for the BB84 simulators."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .bb84_finite_key import FiniteKeyParameters, run_finite_key_trial
from .bb84_math import critical_qber
from .bb84_simulation import SimulationParameters, simulate_bb84


def _add_shared_channel_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--pulses",
        type=int,
        default=100_000,
        help="Number of emitted signal slots (default: 100000).",
    )
    parser.add_argument(
        "--mean-photon-number",
        type=float,
        default=0.5,
        help="Mean photon number or normalized source intensity.",
    )
    parser.add_argument(
        "--intrinsic-bit-fidelity",
        type=float,
        default=0.985,
        help="Probability that the channel does not flip a bit.",
    )
    parser.add_argument(
        "--receiver-efficiency",
        type=float,
        default=0.90,
        help="Efficiency factor used in the detection model.",
    )
    parser.add_argument(
        "--intercept-resend-probability",
        type=float,
        default=0.0,
        help="Fraction of signals attacked by intercept-resend.",
    )
    parser.add_argument(
        "--leakage-fraction",
        type=float,
        default=0.0,
        help="Heuristic fractional information-leakage penalty.",
    )
    parser.add_argument(
        "--error-correction-efficiency",
        type=float,
        default=1.15,
        help="Error-correction inefficiency f_EC (must be at least 1).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2025,
        help="Deterministic random seed.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Results are always printed.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bb84-qkd",
        description=(
            "Educational BB84 QKD Monte Carlo simulator. "
            "Do not use it to generate real cryptographic keys."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate_parser = subparsers.add_parser(
        "simulate",
        help="Run the report-compatible asymptotic model.",
    )
    _add_shared_channel_arguments(simulate_parser)
    simulate_parser.add_argument(
        "--parameter-estimation-bits",
        type=int,
        default=192,
        help="Number of sifted bits deducted for parameter estimation.",
    )
    simulate_parser.add_argument(
        "--detection-model",
        choices=("linear", "poisson"),
        default="linear",
        help="Detection-probability model (default: linear).",
    )

    finite_parser = subparsers.add_parser(
        "finite",
        help="Run the illustrative finite-size model.",
    )
    _add_shared_channel_arguments(finite_parser)
    finite_parser.add_argument(
        "--secrecy-epsilon",
        type=float,
        default=1e-9,
        help="Allowed secrecy failure probability.",
    )
    finite_parser.add_argument(
        "--correctness-epsilon",
        type=float,
        default=1e-9,
        help="Allowed correctness failure probability.",
    )

    threshold_parser = subparsers.add_parser(
        "threshold",
        help="Compute the asymptotic QBER cutoff for a selected f_EC.",
    )
    threshold_parser.add_argument(
        "--error-correction-efficiency",
        type=float,
        default=1.15,
    )
    threshold_parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Results are always printed.",
    )
    return parser


def _write_result(payload: dict[str, Any], output: Path | None) -> None:
    serialized = json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    print(serialized)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized + "\n", encoding="utf-8")


def _run_simulation(args: argparse.Namespace) -> dict[str, Any]:
    parameters = SimulationParameters(
        pulses=args.pulses,
        mean_photon_number=args.mean_photon_number,
        intrinsic_bit_fidelity=args.intrinsic_bit_fidelity,
        receiver_efficiency=args.receiver_efficiency,
        intercept_resend_probability=(args.intercept_resend_probability),
        leakage_fraction=args.leakage_fraction,
        parameter_estimation_bits=args.parameter_estimation_bits,
        error_correction_efficiency=(args.error_correction_efficiency),
        seed=args.seed,
        detection_model=args.detection_model,
    )
    return simulate_bb84(parameters).to_dict()


def _run_finite(args: argparse.Namespace) -> dict[str, Any]:
    parameters = FiniteKeyParameters(
        pulses=args.pulses,
        mean_photon_number=args.mean_photon_number,
        intrinsic_bit_fidelity=args.intrinsic_bit_fidelity,
        receiver_efficiency=args.receiver_efficiency,
        intercept_resend_probability=(args.intercept_resend_probability),
        leakage_fraction=args.leakage_fraction,
        error_correction_efficiency=(args.error_correction_efficiency),
        secrecy_epsilon=args.secrecy_epsilon,
        correctness_epsilon=args.correctness_epsilon,
        seed=args.seed,
    )
    return run_finite_key_trial(parameters).to_dict()


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "simulate":
            payload = _run_simulation(args)
        elif args.command == "finite":
            payload = _run_finite(args)
        else:
            payload = {
                "error_correction_efficiency": (args.error_correction_efficiency),
                "critical_qber": critical_qber(args.error_correction_efficiency),
            }
        _write_result(payload, args.output)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
