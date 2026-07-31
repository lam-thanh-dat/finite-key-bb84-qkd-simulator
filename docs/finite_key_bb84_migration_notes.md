# Migration Notes

## Source-to-repository mapping

| Original item | Standardized destination | Treatment |
|---|---|---|
| `bb84_core.py` | `src/bb84_qkd/bb84_simulation.py` | Refactored into typed, validated asymptotic simulation functions |
| `bb84.py` | `src/bb84_qkd/bb84_gui.py`, `src/bb84_qkd/bb84_cli.py`, and `scripts/reproduce_bb84_results.py` | Split into maintainable interfaces and reproducible headless sweeps |
| `chuong5.py` | `src/bb84_qkd/bb84_finite_key.py` and `src/bb84_qkd/bb84_sweeps.py` | Separated finite-size equations from presentation logic |
| `__pycache__/` and `.pyc` | Not included | Generated artifacts are ignored |
| Vietnamese PDF/PPTX reports | Not included | Large, duplicated, non-executable source artifacts; the English summary replaces them for GitHub use |

The uploaded files remain unchanged. The repository is a clean derivative
package rather than an in-place overwrite.

## Engineering changes

- Translated user-facing text, comments, and documentation into English.
- Adopted a `src/` package layout and modern `pyproject.toml` metadata.
- Added type annotations, immutable parameter/result dataclasses, docstrings,
  explicit validation, and JSON-serializable result objects.
- Replaced ambiguous parameter names with names that match implemented
  behavior.
- Handled binary-entropy endpoints exactly.
- Added a conservative estimate of Eve's retained-bit knowledge from
  intercept-resend and heuristic leakage.
- Applied the configured disclosure count through an explicit
  seed-reproducible random subset before reporting Eve's retained-bit
  knowledge; the earlier prefix slice did not represent removal of disclosed
  positions.
- Removed displayed pseudo-keys. The code now reports estimated key length
  rather than presenting truncated bits as a cryptographic final key.
- Replaced unrestricted formula evaluation in the finite-size GUI with fixed,
  reviewed output metrics.
- Assigned independent deterministic seeds to repeated sweep points.
- Added Monte Carlo confidence intervals, reproducible CSV/PNG outputs, unit
  tests, and continuous integration.
- Added a locked research environment, CI drift detection for tracked numerical
  outputs, Ruff quality checks, and automatic synchronization of paper figures.
- Added a security notice, contribution guide, citation metadata, model-scope
  statement, and concise research summary.

## Repository naming convention

- Project artifacts use descriptive lowercase `snake_case` names.
- The repository directory uses the GitHub-compatible slug
  `finite-key-bb84-qkd-simulator`.
- Ecosystem-defined names such as `README.md`, `pyproject.toml`, `__init__.py`,
  `__main__.py`, `IEEEtran.cls`, and `type1ec.sty` retain their canonical
  spellings because GitHub, Python, or LaTeX resolves them by name.

## Behavior intentionally preserved

- Random Alice/Bob bit and basis generation.
- Basis sifting and aggregate QBER calculation.
- Approximately 25% QBER for a full intercept-resend attack on an ideal link.
- The report's asymptotic key-fraction equation.
- The linear Chapter 4 detection model as the default report-compatible option.
- The Poisson Chapter 5 detection model.
- The Gaussian finite-size margin and logarithmic overhead used by the supplied
  code, with an explicit limitation notice.

## Behavior intentionally changed

- `eta_ch` is exposed as `intrinsic_bit_fidelity` because it controls bit
  flips, not optical loss.
- Ideal binary entropy is exactly zero, so an ideal channel no longer receives
  a tiny floating-point entropy penalty.
- Eve's intercept-resend knowledge is no longer reported as zero.
- Eve's retained-bit knowledge excludes the explicit randomly disclosed subset
  rather than incorrectly omitting the final positions of the sifted array.
- Negative random seeds and Boolean values supplied as integer parameters are
  rejected during parameter construction.
- Sweeps no longer reuse a single correlated random stream at every point.
- The GUI is smaller and focuses on validated single-run analysis; systematic
  sweeps are performed by the reproducibility script.
- The critical-QBER value for `f_EC = 1.15` is corrected from the report's
  approximate 10.3% to 9.88% according to the implemented equation.

## Excluded legal choice

No license file was added because the author did not select a license. No reuse
permission is granted by default. Adding an open-source license remains an
ownership and publication decision rather than a formatting operation.
