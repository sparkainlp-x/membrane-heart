# Changelog

## 0.1.0 (2026-10-26)

Starting point: the supplied v0.1.0 package, imported unchanged in the
first commit of this history. Changes made on top of it:

- Packaging: `membrane_heart/` package, `python -m membrane_heart` CLI,
  tests under `tests/` (unittest and pytest), CI, citation metadata.
- Fixed: `scrambled_field` described unit magnitudes with random phases
  but drew two independent angles per neuron (cos of one, sin of the
  other), so magnitudes were random. It now uses one phase per neuron.
  The old generator remains as `legacy_scrambled_field` and
  `--legacy-scrambled`; with it the supplied README numbers reproduce.
  Effect on the seed-42 demo: scrambled coherence 0.146 became 0.078;
  the refusal count stays 50/50.
- Fixed: a k-nearest-neighbour graph can be disconnected (every seed at
  k=1, about half of seeds at k=2, 3 of 300 seeds at n=128, k=4), which
  gave infinite delays and NaN fields. Components are now bridged by the
  shortest edge; connected graphs, including seed 42 at n=64, k=4, are
  unchanged.
- Changed (fail closed): `decide` on an uncalibrated gate used to accept
  any non-zero field; it now refuses. Use `classify` for ungated
  projection. Non-finite fields are refused instead of passing the
  `max_overlap < tau` test (NaN comparisons are false). A field of the
  wrong length raises `ValueError` instead of being silently truncated by
  `zip`.
- Fixed: `calibrate` raised `ZeroDivisionError` on empty probe lists; it
  now raises `ValueError`.
- Changed: the default tau rule is the midpoint of the longest contiguous
  run of maximal-J grid points. The supplied rule (midpoint of the first
  and last maximal-J point) is kept as `strategy="midpoint_all"`; it can
  land in a dip between two plateaus. For a single plateau, which covers
  the seed-42 demo, the two rules agree.
- Added: parameters `width`, `n_phases`, `k`, `envelope`, `pacemaker_xy`;
  `phase_times`, `pattern_gram`, `max_neighbour_overlap`; probe
  generators and baseline gate scores (`membrane_heart.probes`); statistics
  helpers (`membrane_heart.stats`); pre-registered studies.
- Supplied README, one number: "recognition 39/40" counts probes that the
  gate accepted and named correctly. Ungated projection names 40/40.
