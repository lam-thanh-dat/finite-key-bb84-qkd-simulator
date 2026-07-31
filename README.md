# Finite-Key BB84 QKD Simulator

A reproducible Python simulator for studying the Bennett-Brassard 1984 (BB84)
quantum key distribution protocol under detection loss, intrinsic bit errors,
intercept-resend attacks, heuristic information leakage, and finite-size
penalties.

The repository reorganizes and documents the code developed for a
telecommunications engineering project. The implementation is intended for
education and numerical exploration. It is not a cryptographic product or a
complete security proof.

## Main capabilities

- Monte Carlo simulation of Alice/Bob basis selection and sifting.
- Configurable linear or Poisson detection model.
- Intrinsic bit-error and intercept-resend attack models.
- Shor-Preskill-inspired asymptotic secret-fraction estimate.
- Illustrative finite-size correction with explicit statistical and security
  overhead terms.
- Command-line and desktop graphical interfaces.
- Reproducible parameter sweeps, CSV outputs, and figures.
- Automated unit tests and GitHub Actions continuous integration.

## Repository layout

```text
.
├── .github/workflows/bb84_validation.yml
├── docs/
│   ├── finite_key_bb84_migration_notes.md
│   ├── finite_key_bb84_model_scope.md
│   └── finite_key_bb84_research_summary.md
├── paper/
│   ├── figures/
│   │   ├── bb84_finite_key_scaling.pdf
│   │   └── bb84_intercept_resend_sweep.pdf
│   ├── IEEEtran.cls
│   ├── finite_key_bb84_qkd_simulation_study.pdf
│   ├── finite_key_bb84_qkd_simulation_study.tex
│   └── README.md
├── results/
│   ├── bb84_finite_key_scaling.csv
│   ├── bb84_finite_key_scaling.pdf
│   ├── bb84_finite_key_scaling.png
│   ├── bb84_intercept_resend_sweep.csv
│   ├── bb84_intercept_resend_sweep.pdf
│   ├── bb84_intercept_resend_sweep.png
│   ├── bb84_reference_scenarios.json
│   └── README.md
├── requirements-reproducibility.lock
├── requirements-reproducibility.txt
├── scripts/reproduce_bb84_results.py
├── src/bb84_qkd/
│   ├── bb84_cli.py
│   ├── bb84_finite_key.py
│   ├── bb84_gui.py
│   ├── bb84_math.py
│   ├── bb84_simulation.py
│   └── bb84_sweeps.py
├── tests/test_bb84_*.py
├── CHANGELOG.md
└── THIRD_PARTY_NOTICES.md
```

## Installation

Python 3.10 or newer is required.

### Normal installation

```bash
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux or macOS
source .venv/bin/activate
```

Install the project:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

On Linux, the graphical interface may additionally require the operating-system
package that provides Tkinter.

### Reproduction of tracked results

The broad dependencies in `pyproject.toml` are appropriate for normal package
use. For long-term numerical and figure reproducibility, use the complete
transitive dependency lock with package hashes, validated with CPython 3.12.13:

```bash
python -m venv .venv-repro
source .venv-repro/bin/activate
python -m pip install \
  --require-hashes \
  -r requirements-reproducibility.lock
python -m pip install -e . --no-deps --no-build-isolation
```

On Windows PowerShell, activate it with
`.venv-repro\Scripts\Activate.ps1`. The locked environment requires Python
3.11 or newer; normal package installation remains supported on Python 3.10.
`requirements-reproducibility.txt` is the human-readable exact input
specification used to generate the hashed lock.

Maintainers can regenerate the lock with:

```bash
uv pip compile requirements-reproducibility.txt \
  --generate-hashes \
  --output-file requirements-reproducibility.lock \
  --python-version 3.12
```

## Quick start

Run one report-compatible asymptotic simulation:

```bash
bb84-qkd simulate --pulses 100000 --mean-photon-number 1 \
  --intrinsic-bit-fidelity 1 --receiver-efficiency 1
```

Run a full intercept-resend case:

```bash
bb84-qkd simulate --pulses 200000 --mean-photon-number 1 \
  --intrinsic-bit-fidelity 1 --receiver-efficiency 1 \
  --intercept-resend-probability 1
```

Run the illustrative finite-key model:

```bash
bb84-qkd finite --pulses 1000000 --mean-photon-number 0.4 \
  --intrinsic-bit-fidelity 0.98 --receiver-efficiency 0.9
```

Launch the graphical interface:

```bash
bb84-qkd-gui
```

Generate standard preview figures without modifying the tracked publication
artifacts:

```bash
python scripts/reproduce_bb84_results.py \
  --output-dir outputs/standard
```

The `outputs/` directory is ignored by Git. To regenerate the tracked numerical
results, publication vector figures, and self-contained copies used by the
LaTeX paper, run:

```bash
python scripts/reproduce_bb84_results.py \
  --publication --sync-paper-figures
```

Running the script without `--output-dir` writes directly to `results/`.
Publication mode is therefore required when intentionally refreshing tracked
figures; otherwise standard Matplotlib rendering would replace the tracked
publication variants.

Publication mode requires a LaTeX installation, Ghostscript (`gs`), and
Poppler (`pdftoppm`). It renders plot labels with LaTeX and converts them to
vector outlines so the paper PDF has no external figure-font conflicts.

Verify that the tracked JSON and CSV outputs match a clean full regeneration:

```bash
python scripts/reproduce_bb84_results.py --check
```

Run the test suite:

```bash
python -m unittest discover -s tests -v
```

Run the development quality checks:

```bash
python -m pip install -e ".[dev]"
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
```

## Parameter terminology

The original report uses `eta_ch` as if it were an optical channel efficiency,
but the source code applies `1 - eta_ch` as a bit-flip probability. The
repository therefore uses the scientifically clearer name
`intrinsic_bit_fidelity`. Optical detection loss is represented separately by
`receiver_efficiency`.

| Report/source name | Repository name | Implemented meaning |
|---|---|---|
| `N`, `n_bits` | `pulses` | Number of emitted signal slots |
| `mu`, `photon_intensity` | `mean_photon_number` | Mean photon number or normalized source intensity |
| `eta_ch`, `channel_efficiency` | `intrinsic_bit_fidelity` | Probability that the channel does not flip a bit |
| `eta_abs`, `absorption_efficiency` | `receiver_efficiency` | Factor used in the detection-probability model |
| `p_atk`, `eve_attack_prob` | `intercept_resend_probability` | Fraction of signals attacked by Eve |
| `c_split`, `eve_split_coeff` | `leakage_fraction` | Heuristic fractional leakage penalty |
| `f_ec` | `error_correction_efficiency` | Error-correction inefficiency, at least 1 |

## Scientific interpretation

The asymptotic model estimates

`r = max(1 - (1 + f_EC) h_2(Q), 0) (1 - lambda)`,

where `Q` is the observed quantum bit error rate, `h_2` is binary entropy, and
`lambda` is the heuristic leakage fraction. The estimated key length is an
information budget, not a generated cryptographic key.

The configured parameter-estimation count is removed through a deterministic
random disclosure mask before auxiliary retained-bit knowledge is reported.
QBER is still evaluated over the complete sifted sequence for compatibility
with the original project; this is not a real sampling-based
parameter-estimation protocol.

The finite-size model adds a Gaussian statistical margin, a phase-error
penalty, and logarithmic security-overhead terms. This is useful for exploring
trends, but it is not equivalent to a tight composable finite-key proof.
Detailed assumptions and unresolved scientific questions are documented in
[`docs/finite_key_bb84_model_scope.md`](docs/finite_key_bb84_model_scope.md).

## Documentation

- [`docs/finite_key_bb84_research_summary.md`](docs/finite_key_bb84_research_summary.md):
  readable Markdown companion to the conference paper.
- [`paper/finite_key_bb84_qkd_simulation_study.tex`](paper/finite_key_bb84_qkd_simulation_study.tex):
  self-contained LaTeX source using the
  official `IEEEtran` conference class.
- [`paper/finite_key_bb84_qkd_simulation_study.pdf`](paper/finite_key_bb84_qkd_simulation_study.pdf):
  compiled three-page research paper.
- [`paper/README.md`](paper/README.md): report compilation notes and items that
  must be completed for a specific conference submission.
- [`docs/finite_key_bb84_model_scope.md`](docs/finite_key_bb84_model_scope.md):
  assumptions, limitations, and claims that should not be made from this
  simulator.
- [`docs/finite_key_bb84_migration_notes.md`](docs/finite_key_bb84_migration_notes.md):
  mapping from the
  original files to the standardized package.
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md): origin and license notice
  for the bundled IEEEtran class.
- [`CHANGELOG.md`](CHANGELOG.md): release-level changes.

Compile the LaTeX report from the `paper` directory with:

```bash
cd paper
pdflatex finite_key_bb84_qkd_simulation_study.tex
pdflatex finite_key_bb84_qkd_simulation_study.tex
```

## Naming convention

Project artifacts use descriptive lowercase `snake_case` names; the repository
directory uses the `finite-key-bb84-qkd-simulator` slug. Canonical tool files
such as `README.md`, `pyproject.toml`, `__init__.py`, `__main__.py`,
`IEEEtran.cls`, and `type1ec.sty` keep their ecosystem-defined names so GitHub,
Python, and LaTeX continue to recognize them automatically.

## License

No open-source license has been selected. No permission is granted to copy,
modify, or redistribute the project beyond rights provided by applicable law.
This repository may be viewed for academic evaluation; add a license only after
the author confirms ownership and release permission for the university-derived
code.
