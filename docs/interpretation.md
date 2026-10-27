## 9. Interpretation (hand-written)

All statements are about this SYNTHETIC toy and its seeded probes. They
are not about hearts, patients or any clinical quantity, and no rate here
is the accuracy of a clinical test. Numbers are from the confirmation set
and are checked against `docs/results/confirm.json` by a test.

### What the pre-registered results do show

- Recognition: with the envelope in place the memory names the stored
  phase of a noisy probe essentially always up to sigma 0.15 (mean
  accuracy 0.9995, H1), 0.901 at sigma 0.30, and 0.545 at sigma 0.60
  against a chance level of 0.25. The supplied single-seed "39/40" was
  not a lucky draw: the gate, not the memory, rejects the occasional
  probe (gated accuracy 0.996 at sigma 0.15).
- Refusal of random fields: the gate refuses Haar-random fields 0.996 of
  the time at sigma 0.15 (H2) and separates in-library from
  scrambled-phase fields with AUC 0.99998 (H5). Refusal gets worse as
  noise grows because the two score distributions overlap: at sigma 0.30
  the calibrated gate refuses 0.870 of Haar fields while accepting only
  0.821 of in-library probes.
- Controls behave: label-shuffled recognition sits at chance, 0.2464
  [0.2405, 0.2522] (H3), and a pure phase wave is recognised at chance,
  0.2505 (H4; ablation `envelope_off` confirms a 0.65 to 0.75 drop at sigma 0.30 and 0.15).

### What the results show about limits (read these as findings)

- The gate is blind to a global phase rotation of a stored wave (H8) and
  accepts a wave sitting between two stored phases (H9). With noise-free
  probes of the deformed kinds, nothing is refused except random-like
  kinds: time-shifted waves 0.000, half-masked waves 0.000 to 0.024,
  conjugate (reversed-phase) waves 0.007, magnitude-permuted waves 0.047,
  scrambled phases on the stored envelope 0.721 (PARTLY REFUSED).
- Part of that is a confound that the first multi-seed run exposed, so a
  noise-matched control was added (amendment A1): noise-free deformed
  waves out-score noisy in-library probes. With the same sigma 0.15 noise
  on both, those kinds become PARTLY REFUSED (time-shifted 0.31,
  conjugate 0.46, magnitude-permuted 0.73, scrambled phases on the
  envelope 0.89). So the gate is a partial, noise-sensitive separator for
  structured deformations; it is a reliable separator only for
  random-like fields.
- Because the noise-free AUCs for deformed kinds are far below 0.5
  (for example 0.076 for a time-shifted wave), H6, which asks whether the
  max-overlap gate beats the `wave_scan` gate there, is satisfied only in
  the sense that 0.076 exceeds 0.000. Neither gate separates those probes.
  With noise matched, max-overlap reaches AUC 0.873 on the time-shifted
  kind while `wave_scan` stays at 0.497, because `wave_scan` correctly
  treats a wave at any phase as a wave; it is a different question
  ("is this a wave?" versus "is this one of the stored phases?").
- On random and scrambled-phase fields the max-overlap gate is not better
  than the simple `wave_scan` gate (both AUC 1.000); it is far better than
  the phase-blind magnitude-profile gate there (0.709), and worse than it
  on magnitude-permuted fields noise-free (0.623 against 0.985), as
  expected for a gate that sees only magnitudes.
- The tau rule matters very little. The midpoint rule beats first-best by
  0.0022 in balanced accuracy against Haar fields (95% interval 0.0013 to
  0.0031; supported statistically in H7, tiny in size); the other rules
  agree with the midpoint rule to within 0.0001.
- A tau frozen at one noise level does not transfer: calibrated at sigma
  0.05 the gate accepts only 0.188 of in-library probes at sigma 0.15;
  calibrated at 0.15 it accepts 0.335 at sigma 0.30.

### Ablations (exploratory)

- The envelope is required: removing it drops recognition by 0.65 at
  sigma 0.30. A very wide envelope (width 64) behaves like a pure phase
  wave (0.298 at sigma 0.30).
- Narrower envelopes (width 4) are 0.021 more accurate than the default at
  sigma 0.30, because snapshots then light up different neurons; that is
  closer to a lookup of which neurons are bright than to phase storage.
  Wider envelopes (12) lose 0.072.
- More stored phases are harder: 8 phases give 0.951 at sigma 0.15 and
  0.753 at sigma 0.30. The supplied note that more snapshots would "blur
  and teach nothing new" is partly right: they overlap more (largest neighbour
  overlap 0.91 at 8 phases against 0.49 at 4) and lose accuracy under
  noise, but they stay well above chance.
- Network size matters through noise, not size: at the same absolute
  sigma, n = 128 changes accuracy by -0.003 (not distinguishable from 0);
  with sigma scaled to hold the per-neuron signal-to-noise ratio, n = 128
  gains 0.082 and n = 32 loses 0.170 at nominal sigma 0.30.
- Neighbour count k and pacemaker position move accuracy by about 0.01 or
  less at sigma 0.30. Several of these differences have Holm p below 0.05,
  but at that size they are not practically meaningful.

### Does the phase structure matter?

Yes, for this toy: a magnitude-only classifier is within 0.005 of complex
projection up to sigma 0.10, but at sigma 0.15 it reaches 0.817 against 0.9995 and at
sigma 0.30 it reaches 0.393 against 0.901 (difference 0.507). Under noise
the phase information is what keeps the stored snapshots apart.

### Limitations

- Everything is a seeded toy: a parametric curve, a phase wave with an
  invented envelope, absolute-sigma complex Gaussian noise, and
  hand-designed out-of-library fields. Other noise models, other probe
  kinds or another gate would give other numbers.
- Replicates share the same 64-neuron design and the same probe
  generators; the intervals describe variation over layouts and noise
  draws, not over model choices. Wilson intervals treat trials as
  independent and are optimistic.
- The 0.90 refusal classes and thresholds are reporting choices. The
  development set was looked at before the confirmation run, and
  amendments A1 to A3 in `docs/PROTOCOL.md` were made after that.
- The pure-phase null depends on floating-point tie behaviour, and the
  fraction assigned to phase 0 is not a recognition result.
- Nothing here transfers to real physiology. No term in the model
  corresponds to any biological quantity, and the toy was never compared
  with recorded data.
