# Contributing

This is a small SYNTHETIC research toy; issues and pull requests are
welcome.

- Run `python -m unittest` and `python scripts/check_text.py` before you
  open a pull request. Runtime code stays standard-library only.
- Every random draw must come from an explicit seed. Calibration and
  evaluation probes must use separate seeds (`membrane_heart.stats.
  derive_seed`).
- Keep claims honest: label results SYNTHETIC, report null results, and
  never describe outputs as medical or clinical.
- Optional plotting libraries may be used in dev-only scripts but must not
  become a runtime dependency.
- Commit messages: imperative mood, one logical change per commit.
- Contributions are accepted under AGPL-3.0-only.
