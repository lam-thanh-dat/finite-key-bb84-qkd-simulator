# Finite-Key BB84 QKD Simulation Study

This package is self-contained for Overleaf and local pdfLaTeX compilation.
It uses the `IEEEtran` conference class supplied in the official IEEE template.

## Compile

Run pdfLaTeX twice:

```bash
pdflatex finite_key_bb84_qkd_simulation_study.tex
pdflatex finite_key_bb84_qkd_simulation_study.tex
```

The source intentionally does not load `geometry`, `titlesec`, `caption`, or
font-replacement packages. Page dimensions, typography, headings, captions,
and the two-column layout are controlled by `IEEEtran`.

The author e-mail, ORCID, conference copyright notice, funding footnote, and
paper identifier are not included because no verified values or target
conference requirements were supplied. Add only the items required by the
selected conference before submission.

The compiled paper is
`finite_key_bb84_qkd_simulation_study.pdf`. The canonical external class file
`IEEEtran.cls` intentionally retains its official name because
`\documentclass[conference]{IEEEtran}` resolves that exact basename.

Regenerate and synchronize both vector figures from the repository root with:

```bash
python scripts/reproduce_bb84_results.py \
  --publication --sync-paper-figures
```

`IEEEtran.cls` is version 1.8b and is distributed under LPPL 1.3. The file is
included unchanged from the IEEE conference template; see
`../THIRD_PARTY_NOTICES.md` for the retained third-party notice and upstream
references.
