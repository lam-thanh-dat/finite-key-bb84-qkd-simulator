# Changelog

## 1.0.3 - 2026-07-31

### Corrected

- Forced generated CSV records to use LF line endings so Git normalization does
  not cause false reproducibility failures after commit and checkout.
- Clarified the distinction between untracked standard previews and tracked
  publication figures in the reproduction instructions.

### Added

- Regression coverage that rejects CRLF line endings in generated CSV files.

## 1.0.2 - 2026-07-30

### Corrected

- Rejected `NaN`, positive infinity, and negative infinity for every public
  floating-point parameter used by the simulator, finite-key model, sweeps,
  and QBER-threshold calculation.
- Enforced strict JSON serialization so non-finite values cannot be emitted as
  non-standard `NaN` or infinity tokens.
- Aligned the development and citation wording with the repository's
  intentional no-license policy.

### Added

- Complete transitive reproducibility lock with package hashes.
- API and CLI regression tests for non-finite inputs.

### Removed

- Generated `build/` package copies from the release archive.

## 1.0.1 - 2026-07-30

### Corrected

- Removed disclosed positions through an explicit seed-reproducible random mask
  before computing Eve's retained-bit knowledge.
- Rejected negative random seeds and Boolean values supplied for integer
  parameters during validation.

### Added

- Locked research dependencies for numerical and figure reproduction.
- Automatic synchronization of generated vector figures into `paper/figures/`.
- CI checks for tracked JSON/CSV drift and Ruff code quality.
- Tests for malformed parameters, zero-detection limits, CLI file output,
  figure synchronization, and result drift.
- Third-party notice for the bundled IEEEtran class.
