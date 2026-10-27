# membrane-heart

A SYNTHETIC toy: a heart-shaped network of 64 simulated neurons carries a
travelling phase wave. Snapshots of the wave are stored in a complex
outer-product associative memory, and a calibrated gate either names the
snapshot or refuses the probe. Classical, stdlib-only Python, seeded and
reproducible.

Copyright (C) 2026 Jean-François Brisson (Spark AI NLP). Licensed under
AGPL-3.0-only; the full text is in `LICENSE`.

Status: version 0.1.0, released on GitHub on 2026-10-26 and archived on
Zenodo; the DOIs are listed under "How to cite" once the archive record
exists.

## Not a medical model

This is not a model of a human heart, not a medical device, not a
diagnosis, and not a measurement of any real person. It has no atria,
ventricles, valves, ionic currents, ECG, refractory period or re-entry.
The "heart" is a parametric curve, a "beat" is a phase wave, and a
"scrambled" field is random phases. No result here transfers to real
physiology, and no rate reported here is the accuracy of a clinical test.
Do not use it for health decisions.

## Honest limits, read first

- Everything is SYNTHETIC. Delays are in arbitrary distance units; the
  period of 40 time units is not milliseconds and nothing is a heart rate.
- The four stored phase names (rest, atrial, ventricular, recovery) are
  labels for four snapshots of one synthetic wave, not the cardiac cycle.
- The wave needs an amplitude envelope to be storable at all. With a pure
  phase wave the snapshots differ only by a global phase, which
  |overlap| cannot see (a documented failure, reproduced in
  `docs/RESULTS.md`).
- The gate is blind to a global phase rotation of a stored wave, accepts
  waves that sit between stored phases, and the studies in
  `docs/RESULTS.md` list further fields it does NOT refuse.
- "Holographic" means an outer-product associative memory in the sense of
  the lineage repositories below. It is not a laser hologram or a display.
- The noise parameter sigma is absolute per real and imaginary component,
  while each component of a unit-norm 64-neuron field has root-mean-square
  size 1/8 = 0.125. So sigma = 0.15 is larger than the signal per
  component; the toy still separates the four phases because the
  envelope concentrates the signal in a few neurons.
- Calibration uses random (Haar) fields as the out-of-library class. Other
  out-of-library kinds are tested separately and some are accepted.

## Quickstart

```bash
python -m membrane_heart          # or: python demo.py
python -m unittest                # or: python -m pytest
python -m experiments.run_all --set smoke --out smoke.json
```

Python 3.10 or newer. There are no runtime dependencies.

```python
import random
from membrane_heart import MembraneHeart, noisy, rand_field

heart = MembraneHeart(n=64, seed=42)            # geometry seed
rng = random.Random(11)                          # calibration stream
ins = [noisy(heart.patterns[k % 4], 0.15, rng) for k in range(100)]
ood = [rand_field(64, rng) for _ in range(100)]
tau, j = heart.calibrate(ins, ood)               # frozen afterwards
verdict, phase, probs = heart.decide(noisy(heart.patterns[2], 0.15,
                                           random.Random(99)))
```

`decide` refuses everything until the gate is calibrated (fail closed).
`classify` is ungated projection.

## Demo output (seed 42)

<!-- demo-output:begin -->
```text
membrane-heart v0.1.0 -- SYNTHETIC toy. Not a medical model, not a medical device, not a diagnosis.
64 neurons, 156 edges, pacemaker 0
delays: first 0.00, median 17.52, last 31.90
gate calibrated: tau = 0.351, Youden J = 1.000 (frozen)
fresh noisy recognition (sigma=0.15): 39/40 (gated; ungated 40/40)
fresh scrambled fields refused: 50/50
coherence: perfect wave 1.000, scrambled 0.078
```
<!-- demo-output:end -->

The recognition line counts probes that the gate accepted AND named
correctly, as in v0.1.0; one of 40 probes is refused by the gate, and
ungated projection names all 40. The scrambled-coherence value differs
from the v0.1.0 README (0.146) because the v0.1.0 scrambled-field
generator was defective; see `CHANGELOG.md`. `--legacy-scrambled`
reproduces the v0.1.0 value.

## Headline results (SYNTHETIC)

<!-- results:begin -->
Confirmation seeds 5000 to 5199 (200 random layouts), 95 % bootstrap intervals over layouts, all SYNTHETIC. Full tables, ablations, baselines and limits: `docs/RESULTS.md`.

| Quantity | Mean [95% interval] |
|---|---|
| Recognition accuracy, sigma 0.15 | 1.000 [0.999, 1.000] |
| Recognition accuracy, sigma 0.30 | 0.901 [0.896, 0.905] |
| Recognition accuracy, sigma 0.60 (chance 0.25) | 0.545 [0.539, 0.552] |
| Haar-random fields refused, sigma 0.15 | 0.996 [0.994, 0.997] |
| Scrambled-phase fields refused, sigma 0.15 | 0.998 [0.997, 0.999] |
| Label-shuffled recognition (chance 0.25) | 0.246 [0.240, 0.252] |
| Pure phase wave stored, recognition (null; chance 0.25) | 0.251 [0.247, 0.255] |
| Time-shifted wave between stored phases refused (noise-free) | 0.000 [0.000, 0.000] |
| Half-masked wave refused (noise-free) | 0.000 [0.000, 0.000] |
| Globally phase-rotated stored wave refused (blind spot) | 0.000 [0.000, 0.000] |
| Time-shifted wave refused, noise matched to in-library | 0.314 [0.299, 0.328] |

All nine pre-registered hypotheses were met on the confirmation seeds (`docs/RESULTS.md`, section 1). The gate separates random-like fields from stored waves and does not reliably refuse deformed stored waves; this is a finding about the toy, not about any heart.
<!-- results:end -->

## Studies

`docs/PROTOCOL.md` was committed before any study result existed and
states hypotheses, metrics, development and held-out confirmation seeds,
the stopping rule, Holm correction and bootstrap intervals.
`docs/RESULTS.md` reports every study, including null and negative
results, from committed scripts in `experiments/`:

```bash
python -m experiments.run_all --set dev --out docs/results/dev.json
python -m experiments.run_all --set confirm --out docs/results/confirm.json
python -m experiments.render_results
```

## Lineage

This repository joins four earlier ideas. Where a source is a published
repository it is linked; the others are described honestly.

- Heart geometry: the supplied package named a project called
  `holo-heart-neurons` (parametric heart curve, seeded neurons,
  nearest-neighbour edges, pacemaker, Dijkstra delays). No repository
  with that name exists under sparkainlp-x, public or private, and no
  copy was found, so its licence and authorship could not be checked.
  The geometry code here is the supplied module (with fixes listed in
  `CHANGELOG.md`).
- Memory and projection:
  [membrane-capacity](https://github.com/sparkainlp-x/membrane-capacity)
  (AGPL-3.0, J.-F. Brisson).
- Refusal gate with Youden-J calibration:
  [refusing-membrane](https://github.com/sparkainlp-x/refusing-membrane)
  (AGPL-3.0, J.-F. Brisson).
- Midpoint-of-best-tau rule: from `membrane-vs-hopfield`, a package by the
  same author that is not yet published as a GitHub repository (its
  `CITATION.cff` names J.-F. Brisson and AGPL-3.0-only).

## Acknowledgements

Mun Seok Lee is acknowledged for discussion only, in the same words as in
the lineage repositories membrane-capacity and refusing-membrane. We
cannot verify any specific contribution to this repository, and no file
here is known to derive from a package received under his name. He is not
an author of this release, and no endorsement of this code or its
conclusions is implied.

## How to cite

See `CITATION.cff`. Cite the repository URL, version 0.1.0 and the
release tag (a DOI is listed here once the Zenodo record exists):

Brisson, J.-F. (2026). membrane-heart (version 0.1.0) [SYNTHETIC toy
software]. https://github.com/sparkainlp-x/membrane-heart

## Files

- `membrane_heart/`: geometry, wave, memory and gate (`core.py`), probe
  generators and baseline gates (`probes.py`), statistics helpers
  (`stats.py`), demo and CLI (`demo.py`)
- `experiments/`: committed, seeded study scripts
- `docs/PROTOCOL.md`, `docs/RESULTS.md`, `docs/results/`: protocol,
  results and raw summaries
- `DESIGN.md`: decisions, falsified designs, limits
- `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CITATION.cff`,
  `.zenodo.json`
- `scripts/check_text.py`: wording checker run in CI
