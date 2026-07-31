# Development Guidelines

External contributions are not currently accepted because no public software
license or contribution terms have been selected. This document describes the
internal validation process used to maintain the repository.

1. Create a focused branch.
2. Keep public APIs and documentation in English.
3. Add or update tests for every behavioral change.
4. Install development tools with `python -m pip install -e ".[dev]"`.
5. Run `python -m ruff check src tests scripts`.
6. Run `python -m ruff format --check src tests scripts`.
7. Run `python -m unittest discover -s tests -v`.
8. Run
   `python scripts/reproduce_bb84_results.py --quick --output-dir outputs/quick`.
9. Run `python scripts/reproduce_bb84_results.py --check` after any numerical
   model or result-generation change.
10. State whether a change preserves the report-compatible model or introduces
    a new physical/security assumption.

Scientific changes should cite a primary source and identify which model
assumption, equation, or result is affected.
