# DESIGN.md — membrane-heart v0.1.0

## Decisions

- **Reuse, don't reinvent.** Geometry is holo-heart-neurons, memory
  is membrane-capacity, gate is refusing-membrane. The new work is
  only the joint: a travelling wave whose snapshots become the
  stored patterns. Each source rule is named in the module docstring
  so a reader can check it against the original package.
- **Travelling wave, not Kuramoto sync.** A heart beat is a wave
  that arrives at different places at different times, not a
  synchronised flash. Phase = 2*pi*(t - delay)/period captures
  exactly that, and nothing more. A Kuramoto model would add
  coupling dynamics this toy does not need — and would tempt a
  physiology claim.
- **Four phases, not a full cycle.** Four snapshots (quarter-period
  apart) are enough to show storage, recognition, and refusal.
  More snapshots would blur into each other (neighbouring phases
  overlap heavily) and teach nothing new.
- **Envelope, not pure phase — a bug caught by the tests.** The
  first version stored pure phase waves; snapshots then differed
  only by a global phase, which |overlap| cannot see, and noisy
  recognition came out 0.325 instead of 0.90. The wave now carries
  a Gaussian envelope (bright just after passage, fading behind),
  so snapshots have different amplitude profiles: recognition
  39/40, coherence 1.000 vs 0.146. The failed version is kept in
  this note, not hidden.
- **Midpoint tau.** Calibration picks the midpoint of the maximal-J
  taus, per membrane-vs-hopfield. First-best tau sits on the edge
  of the separation gap and is fragile; the midpoint is the honest
  frozen gate.
- **Scrambled = toy arrhythmia, labelled as such.** Random phases
  are not fibrillation, not tachycardia, not any named condition.
  The word used in code and docs is "scrambled", and the README
  forbids mapping it to a diagnosis.

## Falsified / rejected designs

- **ECG waveform output.** Rejected: synthesising an ECG-shaped
  trace would look clinical while being made up. Phasors and
  coherence numbers stay visibly synthetic.
- **Atria/ventricles as regions.** Rejected: splitting the curve
  into chambers would be anatomy theatre — the curve has no
  chambers, and naming regions would imply a model that is not
  there.
- **Learning the gate on the test data.** Rejected: calibration
  probes and fresh test probes are separate seeds and separate
  draws in both demo and tests. Calibrating and evaluating on the
  same data would inflate the refusal numbers.
- **Calling refusal "detection".** Rejected in copy: the gate
  refuses an out-of-library field. It does not detect a disease.
  The distinction is kept in every docstring and in the README.

## Limits, restated

Synthetic only. Period 40 time units, velocity 1.0, delays in
distance units — none of these are milliseconds, mm/s, or beats
per minute. Nothing here transfers to a real heart without a real
physiological model and real data, neither of which this package
has or claims.
