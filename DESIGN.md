# DESIGN.md: membrane-heart v0.1.0

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
  coupling dynamics this toy does not need  -  and would tempt a
  physiology claim.
- **Four phases, not a full cycle.** Four snapshots (quarter-period
  apart) are enough to show storage, recognition, and refusal.
  More snapshots would blur into each other (neighbouring phases
  overlap heavily) and teach nothing new.
- **Envelope, not pure phase  -  a bug caught by the tests.** The
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
- **Scrambled, not named after a condition.** Random phases are not
  fibrillation, not tachycardia, not any named condition. The word used
  in code and docs is "scrambled", and the README forbids mapping it to a
  diagnosis.

- **Defaults changed from the supplied package, and why.** Each is
  listed in `CHANGELOG.md` and pinned by a test. (1) The scrambled-field
  generator drew two independent angles, so it was not the unit-magnitude
  field its description claimed; the one-angle version is the default and
  the old one is kept as `legacy_scrambled_field` so the supplied numbers
  still reproduce. (2) `decide` fails closed: uncalibrated gate, zero
  field and non-finite field are all refused (the old code accepted any
  non-zero field before calibration, and NaN passed `max_overlap < tau`
  because every NaN comparison is false). (3) Wrong-length fields raise
  instead of being truncated by `zip`. (4) A disconnected k-nearest graph
  is bridged so delays stay finite. (5) The tau default is the midpoint
  of the longest contiguous maximal-J run; the supplied midpoint of the
  first and last point is kept as `midpoint_all`.
- **Calibration and evaluation never share a stream.** Experiments derive
  every random stream from `derive_seed(role, seed, ...)` with different
  roles for calibration and evaluation, so no probe that set tau is ever
  scored (tests check disjointness over all 400 dev and confirmation
  seeds).
- **The max-overlap gate is blind to a global phase.** |overlap| ignores
  a global phase factor, so a stored wave multiplied by a phase is
  always accepted. This is a consequence of the supplied gate rule, it is
  measured (hypothesis H8) and not hidden, and it is also why a pure
  phase wave cannot be stored.
- **Ties go to the lowest index.** With pure phase storage the four
  |overlap| values are equal up to rounding, so the winner is decided by
  rounding noise and the tie rule. The null study reports the fraction of
  probes assigned to index 0 so this cannot be mistaken for recognition.
- **Noise is absolute.** sigma is per real and imaginary component of a
  unit-norm field, so it does not scale with the number of neurons. Where
  size is ablated, a second variant scales sigma by sqrt(64/n).

## Falsified / rejected designs

- **ECG waveform output.** Rejected: synthesising an ECG-shaped
  trace would look clinical while being made up. Phasors and
  coherence numbers stay visibly synthetic.
- **Atria/ventricles as regions.** Rejected: splitting the curve
  into chambers would be anatomy theatre  -  the curve has no
  chambers, and naming regions would imply a model that is not
  there.
- **Learning the gate on the test data.** Rejected: calibration
  probes and fresh test probes are separate seeds and separate
  draws in both demo and tests. Calibrating and evaluating on the
  same data would inflate the refusal numbers.
- **Calling refusal "detection".** Rejected in copy: the gate
  refuses an out-of-library field. It does not detect a disease.
  The distinction is kept in every docstring and in the README.

- **Reading a high refusal rate as a good gate.** In the first multi-seed
  run, deformed stored waves (a half-masked wave, a wave between stored
  phases) were never refused. Part of that was a confound: in-library
  probes carried noise and these probes did not, so they out-scored the
  in-library probes. The noise-matched control (amendment A1 in
  `docs/PROTOCOL.md`) removes the confound; those kinds are then refused
  only partly. Both tables are kept. The gate separates wave-like fields
  from random fields, and that is all it is shown to do.
- **Claiming the gate beats a simpler gate.** The baselines show it does
  not: a continuous-time coherence scan gate performs about equally on
  random and scrambled fields and worse on waves between stored phases
  (which it correctly regards as waves). The max-overlap gate is the
  stored-phase gate, not a better wave detector.
- **A pure-phase memory.** Reproduced as a null: recognition is at chance
  (see `docs/RESULTS.md`, study E).
- **Making the width a free parameter to tune.** The envelope width sweep
  shows narrower envelopes recognise slightly better under heavy noise,
  because snapshots then light up different neurons and the task becomes
  a lookup of which neurons are bright. Width 8 is kept as the supplied
  default; it is not claimed to be optimal.
- **ECG-like output, chambers, and the word "detection"** remain rejected
  as in v0.1.0, above.

## Limits, restated

Synthetic only. Period 40 time units, velocity 1.0, delays in
distance units  -  none of these are milliseconds, mm/s, or beats
per minute. Nothing here transfers to a real heart without a real
physiological model and real data, neither of which this package
has or claims.
