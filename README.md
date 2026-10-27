# membrane-heart v0.1.0

**A sparkainlp-x membrane simulating a heart — as a toy, not a patient.**

Stdlib-only Python, seeded, reproducible, AGPL-3.0-only.

## What it reuses

- **Geometry** from `holo-heart-neurons`: classic parametric heart
  curve, 64 seeded neurons, 4-nearest-neighbour edges, pacemaker,
  Dijkstra delays.
- **Membrane** from `membrane-capacity`: complex oscillators, stored
  patterns as an outer-product holographic memory, one-shot projection
  (winner = argmax |overlap|).
- **Gate** from `refusing-membrane`: REJECT iff max |overlap| < tau,
  tau self-calibrated once via Youden's J and frozen — with the
  midpoint-of-best-taus improvement from `membrane-vs-hopfield`.

## Run

```bash
python demo.py    # numbers + gate + recognition + coherence
python tests.py   # 8 tests
```

## The simulation, in one paragraph

A pacemaker fires and a phase wave travels through the heart-shaped
network; each neuron's field is a unit phasor whose phase is set by
its delay. Four beat phases (rest, atrial, ventricular, recovery —
names for the four stored snapshots, not anatomy) are stored in the
membrane. A probe field is projected onto them: the membrane names
the phase, or the frozen gate refuses it. A scrambled field — same
magnitudes, random phases, the toy "arrhythmia" — collapses the
rhythm coherence and is refused instead of mislabelled.

## Measured (demo, seed 42)

- 64 neurons, 156 edges, pacemaker neuron 0
- Delays: first 0.00, median 17.52, last 31.90
- Gate calibrated: tau = 0.351, Youden J = 1.000 (frozen)
- Fresh noisy recognition (sigma = 0.15): 39/40
- Fresh scrambled fields refused: 50/50
- Coherence: perfect wave 1.000, scrambled 0.146

No number in this package is a medical measurement.

## Honest limits — read before any use

- **Not a human heart.** No atria, ventricles, valves, ionic currents,
  ECG, refractory period, or re-entry. The "heart" is a parametric
  curve; the "beat" is a phase wave; the "arrhythmia" is scrambled
  phases.
- **Not a medical device, not a diagnosis, not a measurement of any
  real person.** Do not use it for health decisions, and do not
  present its refusal rate as a clinical sensitivity or specificity.
- The four phase names are labels for stored snapshots. They are not
  the cardiac cycle.
- "Holographic" here = outer-product associative memory, the
  membrane meaning — not a laser hologram and not a display.

## Files

- `membrane_heart.py` — geometry, wave, membrane, gate
- `demo.py` — measured demo
- `tests.py` — 8 tests
- `DESIGN.md` — decisions, falsified designs, limits
- `LICENSE` — AGPL-3.0-only
