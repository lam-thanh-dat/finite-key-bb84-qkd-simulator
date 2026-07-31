# A Reproducible BB84 Quantum Key Distribution Simulator with Illustrative Finite-Key Analysis

**Lam Thanh Dat**  
Department of Telecommunications, Faculty of Electrical and Electronics Engineering  
Ho Chi Minh City University of Technology, Vietnam National University Ho Chi Minh City, Ho Chi Minh City, Vietnam

## Abstract

Quantum key distribution provides a physical mechanism for detecting
eavesdropping during secret-key establishment. This work develops a
reproducible Python model of the Bennett-Brassard 1984 quantum key distribution
protocol and evaluates the effects of intrinsic bit errors, detection loss,
intercept-resend attacks, heuristic information leakage, and finite block size.
The software separates an asymptotic secret-fraction model from an illustrative
finite-size correction and provides validated command-line and graphical
interfaces, deterministic parameter sweeps, automated tests, and tracked
results. For an ideal link, the simulation produces zero quantum bit error rate
and a unit secret fraction per retained sifted bit. A full intercept-resend
attack produces a quantum bit error rate of 24.79% and suppresses the secret
fraction to zero. With an error-correction inefficiency of 1.15, the implemented
asymptotic equation gives a critical error rate of 9.88%. Finite-size sweeps
show a measurable gap from the asymptotic estimate that decreases as the block
size increases. The model is suitable for education and sensitivity analysis,
but it does not implement decoy-state estimation, reconciliation codes,
universal-hash privacy amplification, or a composable finite-key security
proof.

**Index Terms—**BB84, finite-key analysis, Monte Carlo methods, quantum
communication, quantum key distribution.

## I. Introduction

The BB84 protocol uses nonorthogonal quantum states and public basis
reconciliation to establish correlated data between two legitimate users,
conventionally Alice and Bob [1]. Measurement disturbance provides a mechanism
for detecting an intercepting adversary. In an idealized asymptotic model,
Shor and Preskill showed that a positive secret key can be extracted below a
protocol-dependent error threshold [2].

Practical systems differ from the ideal model because sources, channels, and
detectors introduce loss and noise, while finite data blocks require statistical
allowances. This project translates those effects into a compact Monte Carlo
simulator. Its primary contribution is a transparent and reproducible software
implementation rather than a new security proof.

## II. System Model

### A. Channel and attack model

Alice generates independent random bits and Z/X bases. Bob independently
selects measurement bases, and only events with matching bases are retained.
The simulator treats `intrinsic_bit_fidelity` as the probability that an event
is not flipped by channel noise. This parameter is intentionally separated from
receiver efficiency, which controls the detection probability.

Two detection models are available. The Chapter 4 compatible approximation
uses `min(mu eta, 1)`, while the finite-size model uses the Poisson
at-least-one-photon expression `1 - exp(-mu eta)`. Intercept-resend attacks are
applied to a configurable fraction of events. On an otherwise ideal link, a
full attack is expected to contribute approximately 25% QBER.

### B. Asymptotic key estimate

For observed QBER `Q`, binary entropy `h_2`, error-correction inefficiency
`f_EC`, and heuristic leakage fraction `lambda`, the program estimates

`r_asym = max(1 - (1 + f_EC) h_2(Q), 0) (1 - lambda)`.

This equation is an information budget. Error correction and privacy
amplification are not executed as cryptographic algorithms.

### C. Illustrative finite-size estimate

The finite-size module expands the observed QBER by a Gaussian statistical
margin, uses the expanded value as a phase-error upper estimate, and deducts
error-correction leakage, privacy-amplification cost, and logarithmic security
overhead. The method reproduces the equations used in the source project but
does not replace tight finite-key analyses such as [4].

## III. Software Organization and Reproducibility

The implementation uses a modern Python `src/` package layout. Immutable
dataclasses define parameters and outputs, while input validation prevents
unphysical probabilities and invalid block sizes. The command-line interface
supports asymptotic, finite-size, and threshold calculations. A small desktop
interface provides the same validated single-run models. Independent
deterministic seeds are assigned to repeated sweep points.

The tracked reproduction script generates reference JSON, two CSV tables, and
publication-quality vector PDF figures with high-resolution PNG previews. A
locked research environment, numerical drift check, and automatic
paper-figure synchronization reduce the risk of future output divergence. The
test suite covers mathematical endpoints, detection models, attack behavior,
finite-size monotonicity, reproducibility, validation, command-line output,
and result synchronization.

## IV. Numerical Results

### A. Reference scenarios

Table I summarizes deterministic runs with 100000 emitted signal slots and
seed 2025. The ideal, attack, and intrinsic-error cases use unit source
intensity and unit receiver efficiency.

| Scenario | QBER | Secret fraction | Estimated secret bits |
|---|---:|---:|---:|
| Ideal baseline | 0.0000 | 1.0000 | 50001 |
| Full intercept-resend | 0.2479 | 0.0000 | 0 |
| Approximately 5% intrinsic error | 0.0513 | 0.3722 | 18611 |
| Above-threshold intrinsic error | 0.1361 | 0.0000 | 0 |

The intercept-resend sweep gives a mean QBER of 0.24979 at full attack across
eight deterministic independent runs, in close agreement with the expected
0.25. The secret fraction reaches zero between attack probabilities 0.3 and
0.4 because the induced QBER crosses the implemented asymptotic threshold.

For `f_EC = 1.15`, solving
`(1 + f_EC) h_2(Q_crit) = 1` gives
`Q_crit = 0.0987799896`, or approximately 9.88%. This corrects the 10.3% value
stated in the source report for the same equation and parameter.

### B. Finite-size trend

For mean photon number 0.4, receiver efficiency 0.9, intrinsic bit fidelity
0.98, and security parameters of `10^-9`, the mean finite-size secret fraction
increases from 0.559 at 10000 emitted slots to 0.689 at 3000000 slots. The
corresponding mean asymptotic estimate is approximately 0.696 at the largest
block size. This result supports the qualitative conclusion that finite-size
penalties decrease with increasing data volume, while also showing that a
universal zero-key cutoff below 100000 slots is not supported by the displayed
default parameter set.

## V. Limitations

The simulator omits dark counts, detector dead time, afterpulsing, timing
jitter, source fluctuations, basis-dependent detection efficiency, and
authenticated classical communication. The heuristic leakage coefficient is
not a physical photon-number-splitting model. Decoy-state BB84 [3] and
measurement-device-independent QKD are not implemented. The finite-size
calculation does not estimate single-photon yields or allocate all security
failure probabilities within a composable proof. Consequently, the numerical
outputs must not be interpreted as certified secure-key rates for a physical
system.

## VI. Conclusion

The standardized simulator reproduces the central qualitative behavior of
BB84: intercept-resend disturbance increases QBER, sufficiently high QBER
eliminates the asymptotic key budget, loss reduces detected and sifted events,
and finite data introduce an additional penalty. The repository adds
reproducibility, test coverage, explicit assumptions, and a clear boundary
between educational estimation and deployable QKD security analysis.

## Acknowledgment

This project was completed under the supervision of Prof. Le Tien Thuong.
OpenAI's ChatGPT/Codex was used to assist with English editing, software
refactoring, test preparation, and drafting this summary. The author remains
responsible for validating all technical claims before publication.

## References

[1] C. H. Bennett and G. Brassard, "Quantum cryptography: Public key
distribution and coin tossing," in *Proc. IEEE Int. Conf. Computers, Systems
and Signal Processing*, Bangalore, India, 1984, pp. 175-179.

[2] P. W. Shor and J. Preskill, "Simple proof of security of the BB84 quantum
key distribution protocol," *Phys. Rev. Lett.*, vol. 85, no. 2, pp. 441-444,
Jul. 2000, doi:
[10.1103/PhysRevLett.85.441](https://doi.org/10.1103/PhysRevLett.85.441).

[3] H.-K. Lo, X. Ma, and K. Chen, "Decoy state quantum key distribution,"
*Phys. Rev. Lett.*, vol. 94, no. 23, Art. no. 230504, Jun. 2005, doi:
[10.1103/PhysRevLett.94.230504](https://doi.org/10.1103/PhysRevLett.94.230504).

[4] M. Tomamichel, C. C. W. Lim, N. Gisin, and R. Renner, "Tight finite-key
analysis for quantum cryptography," *Nat. Commun.*, vol. 3, Art. no. 634,
Jan. 2012, doi:
[10.1038/ncomms1631](https://doi.org/10.1038/ncomms1631).

[5] V. Scarani *et al.*, "The security of practical quantum key distribution,"
*Rev. Mod. Phys.*, vol. 81, no. 3, pp. 1301-1350, Sep. 2009, doi:
[10.1103/RevModPhys.81.1301](https://doi.org/10.1103/RevModPhys.81.1301).

[6] F. Xu, X. Ma, Q. Zhang, H.-K. Lo, and J.-W. Pan, "Secure quantum key
distribution with realistic devices," *Rev. Mod. Phys.*, vol. 92, no. 2,
Art. no. 025002, May 2020, doi:
[10.1103/RevModPhys.92.025002](https://doi.org/10.1103/RevModPhys.92.025002).
