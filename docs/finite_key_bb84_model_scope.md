# Finite-Key BB84 Model Scope, Assumptions, and Open Questions

## Intended use

This project is a reproducible educational simulator for studying qualitative
and semi-quantitative BB84 behavior. It is suitable for classroom
demonstrations, parameter sensitivity studies, and software-development
practice.

It is not suitable for generating real keys, certifying a QKD link, claiming a
composable security parameter, or replacing a device-calibrated security proof.

## Implemented models

### Report-compatible asymptotic model

- Alice and Bob select binary values and Z/X bases independently.
- Detection follows either a clipped linear approximation or a Poisson
  at-least-one-photon model.
- The parameter named `intrinsic_bit_fidelity` is used as one minus the
  independent bit-flip probability.
- Intercept-resend causes an average QBER contribution of approximately one
  quarter of the attacked fraction.
- The asymptotic secret fraction is
  `max(1 - (1 + f_EC) h_2(Q), 0) (1 - leakage_fraction)`.
- A configured number of sifted bits is deducted from the key budget for
  parameter estimation. The deducted positions are selected by a deterministic
  random subset so auxiliary retained-bit knowledge excludes those positions.

### Illustrative finite-size model

- Detection uses the Poisson at-least-one-photon expression.
- A Gaussian normal approximation expands observed QBER to a phase-error upper
  estimate.
- Error-correction leakage, privacy-amplification cost, and logarithmic
  security-overhead terms are deducted from the sifted-key budget.
- The same heuristic leakage fraction is applied after the finite-size
  deductions.

## Important limitations

1. **QBER estimation uses all sifted bits.** The report-compatible simulator
   measures QBER over the complete sifted sequence and then deducts a configured
   disclosure count. The code uses an explicit random subset for deduction and
   retained-bit bookkeeping, but it does not recompute QBER from that subset. A
   real protocol estimates QBER from the disclosed sample and must propagate
   sampling uncertainty.

2. **No error-correction algorithm is implemented.** The program accounts for
   information leakage using `f_EC h_2(Q)`. It does not run Cascade, LDPC,
   Polar, or another reconciliation code.

3. **No privacy-amplification hash is implemented.** The program estimates the
   extractable length. It does not produce a universally hashed final key.

4. **The leakage coefficient is heuristic.** `leakage_fraction` is not a
   photon-number-splitting model and is not a substitute for decoy-state
   estimation of single-photon yields and error rates.

5. **The finite-size calculation is not a tight proof.** The Gaussian margin and
   simplified overhead are useful for trend exploration but are not equivalent
   to a composable finite-key proof such as a protocol-specific analysis based
   on smooth min-entropy and rigorously allocated failure probabilities.

6. **Device physics is simplified.** Dark counts, afterpulsing, dead time,
   detector-efficiency mismatch, source fluctuations, timing jitter,
   polarization drift, and correlated noise are not modeled.

7. **The classical channel is not authenticated.** Authentication is required
   by a secure QKD protocol but is outside this simulator.

8. **No decoy-state or MDI-QKD protocol is implemented.** These techniques are
   discussed in the source report as future extensions. The code does not
   support quantitative performance claims for either technique.

9. **Confidence intervals describe Monte Carlo variability only.** They are not
   experimental confidence intervals and do not represent a security failure
   probability.

## Corrections and report-to-code discrepancies

### Critical QBER

The supplied report states a collapse threshold near 10.3% for
`f_EC = 1.15`. Solving the formula actually implemented in the report,

`(1 + f_EC) h_2(Q_crit) = 1`,

gives `Q_crit = 0.0987799896`, or approximately **9.88%**. The standardized
code and summary use the calculated value.

### Finite-size cutoff

The report suggests that the finite-size secret fraction can be zero or very
small throughout the region below `N = 100000`. That is not a universal result
of the supplied implementation. With the displayed default channel
configuration, the original code gives a positive fraction at `N = 10000`, and
the standardized five-run sweep gives a mean finite-size fraction of about
0.559. A zero-key cutoff can occur under stricter security, higher QBER, or
larger loss, but it must be reported with its full parameter set.

### Channel terminology

The original variable `eta_ch` is described as channel efficiency, but the code
uses `1 - eta_ch` as a bit-flip probability. The standardized name
`intrinsic_bit_fidelity` reflects the implemented behavior. It must not be
interpreted as fiber transmittance.

### Detection model

Chapter 4 uses `min(mu * eta_abs, 1)`, whereas Chapter 5 uses
`1 - exp(-mu * eta_abs)`. Both are retained as explicit alternatives. The
Poisson form is the physically better at-least-one-photon expression for a
phase-randomized weak coherent source, but the model still omits dark counts and
photon-number-resolved security analysis.

## Bibliography audit

The source report's reference [18] could not be verified as written. The
reported title, authors, journal, year, pages, and DOI
`10.4236/jqis.2019.93006` do not form a consistent record. An exact-title search
instead identifies a different 2023 preprint by S. Harshvardhan, S. Jain,
J. E. McClure, C. McIrvin, and N. Q. Tran
([arXiv:2306.02111](https://arxiv.org/abs/2306.02111)). Reference [18] is
therefore excluded from the standardized summary.

The summary uses a small set of established primary sources. The complete
bibliography of the Vietnamese report was not independently revalidated.

## Publication decisions still required

- The author has not selected an open-source license; the public repository
  grants no reuse permission beyond applicable law.
- Public release of the original report and presentation has not been
  authorized; they are not included in the repository.
- Author e-mail and ORCID were not supplied and are omitted.
- Before journal or conference submission, the author should review every
  numerical claim, select the exact IEEE venue template, and update the
  acknowledgment and AI-use disclosure to that venue's policy.
