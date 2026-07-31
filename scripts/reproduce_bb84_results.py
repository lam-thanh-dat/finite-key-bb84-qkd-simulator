#!/usr/bin/env python3
"""Reproduce the finite-key BB84 tables and figures tracked by the repository."""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from bb84_qkd import (  # noqa: E402
    FiniteKeyParameters,
    SimulationParameters,
    critical_qber,
    simulate_bb84,
)
from bb84_qkd.bb84_sweeps import (  # noqa: E402
    run_attack_sweep,
    run_finite_key_sweep,
)

_IEEE_FIGURE_WIDTH_IN = 3.45
_IEEE_FIGURE_HEIGHT_IN = 2.35
_NUMERICAL_RESULT_FILES = (
    "bb84_reference_scenarios.json",
    "bb84_intercept_resend_sweep.csv",
    "bb84_finite_key_scaling.csv",
)
_PAPER_FIGURE_FILES = (
    "bb84_intercept_resend_sweep.pdf",
    "bb84_finite_key_scaling.pdf",
)


def _configure_plot_style(*, publication: bool) -> None:
    """Configure compact, publication-readable figures for IEEE columns."""

    if publication:
        type1ec_check = subprocess.run(
            ["kpsewhich", "type1ec.sty"],
            check=False,
            capture_output=True,
            text=True,
        )
        if not type1ec_check.stdout.strip():
            tex_support_dir = Path(__file__).with_name("tex_support")
            current_texinputs = os.environ.get("TEXINPUTS", "")
            os.environ["TEXINPUTS"] = (
                f"{tex_support_dir}{os.pathsep}{current_texinputs}"
            )

    style: dict[str, Any] = {
        "font.family": "serif",
        "font.serif": [
            "Times New Roman",
            "Times",
            "Nimbus Roman",
            "DejaVu Serif",
        ],
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 6.5,
        "lines.linewidth": 1.1,
        "lines.markersize": 3.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
    if publication:
        style.update(
            {
                "text.usetex": True,
                "text.latex.preamble": r"\usepackage{mathptmx}",
            }
        )
    plt.rcParams.update(style)


def _save_figure(
    figure: plt.Figure,
    path: Path,
    *,
    publication: bool,
) -> None:
    """Save both a high-resolution preview and a vector publication figure."""

    vector_path = path.with_suffix(".pdf")
    if not publication:
        figure.savefig(path, dpi=600, bbox_inches="tight")
        figure.savefig(vector_path, bbox_inches="tight")
        return

    with tempfile.TemporaryDirectory(prefix="bb84-figure-") as temp_dir:
        raw_vector_path = Path(temp_dir) / vector_path.name
        figure.savefig(raw_vector_path, bbox_inches="tight")
        subprocess.run(
            [
                "gs",
                "-dSAFER",
                "-dBATCH",
                "-dNOPAUSE",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                "-dNoOutputFonts",
                "-dAutoRotatePages=/None",
                f"-sOutputFile={vector_path}",
                str(raw_vector_path),
            ],
            check=True,
            capture_output=True,
        )
    subprocess.run(
        [
            "pdftoppm",
            "-singlefile",
            "-png",
            "-r",
            "600",
            str(vector_path),
            str(path.with_suffix("")),
        ],
        check=True,
    )


def _write_csv(
    path: Path,
    rows: list[dict[str, float | int]],
) -> None:
    if not rows:
        raise ValueError("cannot write an empty CSV table")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def synchronize_paper_figures(
    results_dir: Path,
    paper_figures_dir: Path,
) -> None:
    """Copy generated vector figures into the self-contained paper tree."""

    paper_figures_dir.mkdir(parents=True, exist_ok=True)
    for file_name in _PAPER_FIGURE_FILES:
        source = results_dir / file_name
        if not source.is_file():
            raise FileNotFoundError(f"generated paper figure is missing: {source}")
        shutil.copy2(source, paper_figures_dir / file_name)


def find_numerical_result_drift(
    generated_dir: Path,
    tracked_dir: Path,
) -> list[str]:
    """Return tracked numerical files that differ from regenerated outputs."""

    drifted_files: list[str] = []
    for file_name in _NUMERICAL_RESULT_FILES:
        generated_path = generated_dir / file_name
        tracked_path = tracked_dir / file_name
        if (
            not generated_path.is_file()
            or not tracked_path.is_file()
            or generated_path.read_bytes() != tracked_path.read_bytes()
        ):
            drifted_files.append(file_name)
    return drifted_files


def _print_result_diffs(
    generated_dir: Path,
    tracked_dir: Path,
    drifted_files: list[str],
) -> None:
    """Print concise text diffs for numerical reproducibility failures."""

    for file_name in drifted_files:
        generated_path = generated_dir / file_name
        tracked_path = tracked_dir / file_name
        if not generated_path.is_file():
            print(f"missing generated file: {file_name}")
            continue
        if not tracked_path.is_file():
            print(f"missing tracked file: {file_name}")
            continue
        tracked_lines = tracked_path.read_text(encoding="utf-8").splitlines()
        generated_lines = generated_path.read_text(encoding="utf-8").splitlines()
        diff = difflib.unified_diff(
            tracked_lines,
            generated_lines,
            fromfile=f"tracked/{file_name}",
            tofile=f"generated/{file_name}",
            lineterm="",
        )
        print("\n".join(diff))


def _reference_scenarios(pulses: int) -> dict[str, Any]:
    baseline = SimulationParameters(
        pulses=pulses,
        mean_photon_number=1.0,
        intrinsic_bit_fidelity=1.0,
        receiver_efficiency=1.0,
        parameter_estimation_bits=192,
        detection_model="linear",
    )
    scenarios = {
        "ideal_baseline": baseline,
        "full_intercept_resend": replace(
            baseline,
            intercept_resend_probability=1.0,
        ),
        "five_percent_intrinsic_error": replace(
            baseline,
            intrinsic_bit_fidelity=0.95,
        ),
        "above_threshold_error": replace(
            baseline,
            intrinsic_bit_fidelity=0.865,
        ),
        "high_loss": replace(
            baseline,
            receiver_efficiency=0.01,
        ),
        "weak_source": replace(
            baseline,
            mean_photon_number=0.1,
            receiver_efficiency=0.5,
        ),
    }
    payload: dict[str, Any] = {
        "model": "report-compatible asymptotic simulation",
        "critical_qber_f_ec_1_15": critical_qber(1.15),
        "scenarios": {},
    }
    for name, parameters in scenarios.items():
        payload["scenarios"][name] = simulate_bb84(parameters).to_dict()
    return payload


def _plot_attack_sweep(
    rows: list[dict[str, float | int]],
    path: Path,
    *,
    publication: bool,
) -> None:
    attack = np.array(
        [row["intercept_resend_probability"] for row in rows],
        dtype=float,
    )
    qber = np.array([row["qber_mean"] for row in rows], dtype=float)
    qber_low = np.array([row["qber_ci95_low"] for row in rows], dtype=float)
    qber_high = np.array([row["qber_ci95_high"] for row in rows], dtype=float)
    secret = np.array([row["secret_fraction_mean"] for row in rows], dtype=float)

    fig, axis = plt.subplots(figsize=(_IEEE_FIGURE_WIDTH_IN, _IEEE_FIGURE_HEIGHT_IN))
    axis.plot(
        attack,
        qber,
        "o-",
        color="#1261A0",
        label="Simulated QBER",
    )
    axis.fill_between(
        attack,
        qber_low,
        qber_high,
        color="#1261A0",
        alpha=0.18,
        linewidth=0,
        label=r"95\% CI",
    )
    axis.plot(
        attack,
        0.25 * attack,
        "--",
        color="#303030",
        label=r"Expected QBER: $0.25p_{\mathrm{atk}}$",
    )
    axis.plot(
        attack,
        secret,
        "s-",
        color="#B23A48",
        label="Secret fraction",
    )
    axis.set_xlabel("Intercept-resend probability")
    axis.set_ylabel("Fraction")
    axis.set_xlim(0.0, 1.0)
    axis.set_ylim(0.0, 1.02)
    axis.grid(alpha=0.25)
    axis.legend(frameon=False, ncol=2, loc="upper center")
    fig.tight_layout()
    _save_figure(fig, path, publication=publication)
    plt.close(fig)


def _plot_finite_sweep(
    rows: list[dict[str, float | int]],
    path: Path,
    *,
    publication: bool,
) -> None:
    pulses = np.array([row["pulses"] for row in rows], dtype=float)
    finite = np.array(
        [row["finite_secret_fraction_mean"] for row in rows],
        dtype=float,
    )
    finite_low = np.array(
        [row["finite_secret_fraction_ci95_low"] for row in rows],
        dtype=float,
    )
    finite_high = np.array(
        [row["finite_secret_fraction_ci95_high"] for row in rows],
        dtype=float,
    )
    asymptotic = np.array(
        [row["asymptotic_secret_fraction_mean"] for row in rows],
        dtype=float,
    )

    fig, axis = plt.subplots(figsize=(_IEEE_FIGURE_WIDTH_IN, _IEEE_FIGURE_HEIGHT_IN))
    axis.plot(
        pulses,
        finite,
        "o-",
        color="#1261A0",
        label="Finite-size estimate",
    )
    axis.fill_between(
        pulses,
        finite_low,
        finite_high,
        color="#1261A0",
        alpha=0.18,
        linewidth=0,
        label=r"95\% CI",
    )
    axis.plot(
        pulses,
        asymptotic,
        "--",
        color="#B23A48",
        label="Asymptotic estimate",
    )
    axis.set_xscale("log")
    axis.set_xlabel("Emitted signal slots")
    axis.set_ylabel("Secret bits per sifted bit")
    axis.set_ylim(bottom=0.0)
    axis.grid(alpha=0.25, which="both")
    axis.legend(frameon=False)
    fig.tight_layout()
    _save_figure(fig, path, publication=publication)
    plt.close(fig)


def build_results(
    output_dir: Path,
    *,
    quick: bool,
    publication: bool,
    sync_paper_figures: bool = False,
    paper_figures_dir: Path | None = None,
) -> None:
    if sync_paper_figures and not publication:
        raise ValueError("sync_paper_figures requires publication-quality output")

    output_dir.mkdir(parents=True, exist_ok=True)

    if quick:
        scenario_pulses = 20_000
        attack_pulses = 20_000
        attack_points = np.linspace(0.0, 1.0, 3)
        attack_repeats = 2
        finite_points = [10_000, 30_000]
        finite_repeats = 2
    else:
        scenario_pulses = 100_000
        attack_pulses = 200_000
        attack_points = np.linspace(0.0, 1.0, 11)
        attack_repeats = 8
        finite_points = [
            10_000,
            30_000,
            100_000,
            300_000,
            1_000_000,
            3_000_000,
        ]
        finite_repeats = 5

    reference_payload = _reference_scenarios(scenario_pulses)
    (output_dir / "bb84_reference_scenarios.json").write_text(
        json.dumps(
            reference_payload,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    attack_base = SimulationParameters(
        pulses=attack_pulses,
        mean_photon_number=1.0,
        intrinsic_bit_fidelity=1.0,
        receiver_efficiency=1.0,
        parameter_estimation_bits=192,
        detection_model="linear",
    )
    attack_rows = run_attack_sweep(
        attack_points,
        attack_base,
        repeats=attack_repeats,
    )
    _write_csv(
        output_dir / "bb84_intercept_resend_sweep.csv",
        attack_rows,
    )
    _plot_attack_sweep(
        attack_rows,
        output_dir / "bb84_intercept_resend_sweep.png",
        publication=publication,
    )

    finite_base = FiniteKeyParameters(
        pulses=finite_points[0],
        mean_photon_number=0.4,
        intrinsic_bit_fidelity=0.98,
        receiver_efficiency=0.9,
        error_correction_efficiency=1.15,
        secrecy_epsilon=1e-9,
        correctness_epsilon=1e-9,
    )
    finite_rows = run_finite_key_sweep(
        finite_points,
        finite_base,
        repeats=finite_repeats,
    )
    _write_csv(
        output_dir / "bb84_finite_key_scaling.csv",
        finite_rows,
    )
    _plot_finite_sweep(
        finite_rows,
        output_dir / "bb84_finite_key_scaling.png",
        publication=publication,
    )

    if sync_paper_figures:
        if paper_figures_dir is None:
            paper_figures_dir = (
                Path(__file__).resolve().parents[1] / "paper" / "figures"
            )
        synchronize_paper_figures(output_dir, paper_figures_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use a small smoke-test configuration.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results",
    )
    parser.add_argument(
        "--publication",
        action="store_true",
        help=(
            "Render publication-quality figures with LaTeX text converted "
            "to vector outlines; requires LaTeX, Ghostscript, and Poppler."
        ),
    )
    parser.add_argument(
        "--sync-paper-figures",
        action="store_true",
        help=(
            "Copy regenerated vector PDFs into paper/figures. Requires --publication."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Regenerate numerical outputs in a temporary directory and fail "
            "if tracked JSON or CSV files are stale."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.check:
        if args.quick or args.publication or args.sync_paper_figures:
            print(
                "error: --check cannot be combined with --quick, "
                "--publication, or --sync-paper-figures"
            )
            return 2
        _configure_plot_style(publication=False)
        with tempfile.TemporaryDirectory(
            prefix="bb84-reproducibility-check-"
        ) as temp_dir:
            generated_dir = Path(temp_dir)
            build_results(
                generated_dir,
                quick=False,
                publication=False,
            )
            drifted_files = find_numerical_result_drift(
                generated_dir,
                args.output_dir,
            )
            if drifted_files:
                _print_result_diffs(
                    generated_dir,
                    args.output_dir,
                    drifted_files,
                )
                print(
                    "Tracked numerical results are stale: " + ", ".join(drifted_files)
                )
                return 1
        print("Tracked JSON and CSV results are reproducible.")
        return 0

    if args.sync_paper_figures and not args.publication:
        print("error: --sync-paper-figures requires --publication")
        return 2

    _configure_plot_style(publication=args.publication)
    build_results(
        args.output_dir,
        quick=args.quick,
        publication=args.publication,
        sync_paper_figures=args.sync_paper_figures,
    )
    print(f"Results written to {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
