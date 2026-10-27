# Study protocol (pre-registration note)

Status: committed before any study result existed in this repository.
Everything below concerns a SYNTHETIC toy. Nothing here is a statement
about real hearts, patients or any clinical quantity, and none of the
studies can support such a statement.

## What was already known before this note

The supplied v0.1.0 package, its README numbers (seed 42: tau 0.351,
Youden J 1.000, 39/40 recognised, 50/50 scrambled fields refused) and its
tests were seen before this protocol was written. The 0.90 thresholds
below come from that package's own tests. Hypotheses H1 and H2 are
therefore confirmations of a known small-sample observation on new
seeds, not blind predictions. The other hypotheses were written without
looking at any multi-seed output.

## Units of analysis and seeds

- A replicate is one seed s. Seed s sets the geometry (neuron layout), so
  replicates differ in the heart-shaped layout as well as in noise.
- Development set DEV: seeds 1000 to 1199 (200 replicates). Used to
  debug the pipeline and to look at behaviour. Not used for any
  confirmatory claim.
- Confirmation set CONFIRM: seeds 5000 to 5199 (200 replicates), disjoint
  from DEV. Every confirmatory number in `docs/RESULTS.md` comes from
  CONFIRM, which is run once after the code is frozen. A smoke set
  (seeds 9001 to 9005) is used only in CI. Seed 42 is reserved for the
  demo and is in none of these sets.
- All random streams come from `membrane_heart.stats.derive_seed(role,
  ...)`, a SHA-256 hash of a role label and the replicate seed. Roles
  used: `cal` (calibration probes), `eval` (evaluation probes), `boot`
  (bootstrap resampling), `shuffle` (label shuffling). Calibration and
  evaluation therefore never share a stream, and no probe used to set a
  gate threshold is ever scored.

## Fixed setup (unless a study varies it)

n = 64 neurons, k = 4 neighbours, period 40, envelope width 8, 4 stored
phases at t = 0, 10, 20, 30, pacemaker nearest (0, 5), noise sigma 0.15
(absolute per real and imaginary component, see README), tau grid of 101
points, tau rule "midpoint" (longest contiguous run), accept iff
max |overlap| >= tau.

Per replicate and condition: calibration uses 100 in-library probes
(25 per stored phase, noisy at the calibration sigma) and 100 Haar-random
fields; evaluation uses 100 in-library probes (25 per phase) and 50
probes per out-of-library kind. The gate is calibrated once per
replicate and condition, then frozen. "Matched" calibration means the
calibration sigma equals the evaluation sigma.

## Metrics

Per replicate (then summarised over replicates):

- acc_ungated: fraction of in-library probes whose argmax phase is the
  true phase (no gate).
- acc_gated: fraction accepted by the gate and named correctly.
- accept_in: fraction of in-library probes accepted (true-accept rate).
- refuse_X: fraction of out-of-library probes of kind X refused.
- bal_acc_X: (accept_in + refuse_X) / 2.
- auc_X: area under the ROC curve for separating in-library probes
  (positive) from kind-X probes, from the gate score alone.
- tau, J_cal: the frozen threshold and its calibration Youden J.

Out-of-library kinds (`membrane_heart.probes.OOD_KINDS`): haar,
phase_scramble, phase_scramble_envelope, magnitude_permuted,
time_shift_half_spacing, time_shift_quarter_spacing, partial_random_half,
partial_late_half, stored_plus_noise_0.6, stored_plus_noise_1.0,
conjugate_wave, global_phase_rotation.

Classification of a kind, pre-registered: REFUSED if the mean refusal
over replicates is at least 0.90, NOT REFUSED if it is below 0.10,
otherwise PARTLY REFUSED.

Baseline gates compared with the max |overlap| gate (all calibrated the
same way, with Haar fields as the out-of-library class): `wave_scan`
(best overlap with a wave at any of 40 evenly spaced times),
`magnitude_profile` (phase-blind cosine similarity of magnitudes), and
`constant` (a trivial gate; AUC 0.5, balanced accuracy 0.5, and
accuracy equal to the in-library share of the evaluation mixture).

## Intervals and tests

- Descriptive 95 % intervals: percentile bootstrap over replicates of the
  mean, 5000 resamples, resampling seed from role `boot` and a label.
  This is the primary interval. A pooled Wilson interval over all
  trials is shown for proportions as a secondary figure; trials within a
  replicate share a layout and a threshold, so Wilson understates the
  uncertainty and is not used for any test.
- Tests: bootstrap p-value for the replicate-level mean against a null
  value (resampling under the null, 10000 resamples, +1 correction).
  Paired comparisons use per-replicate differences.
- Multiplicity: the nine confirmatory hypotheses below form one family
  and are Holm-adjusted together; a hypothesis is supported when its
  adjusted p is below 0.05. Everything else is exploratory: intervals are
  reported without a support claim, except the ablation differences,
  which are also Holm-adjusted as a second, separate family and labelled
  exploratory.

## Confirmatory hypotheses (CONFIRM seeds only)

| id | statement | test |
|----|-----------|------|
| H1 | acc_ungated at sigma 0.15 exceeds 0.90 | mean > 0.90, one-sided |
| H2 | refuse_haar at sigma 0.15, matched calibration, exceeds 0.90 | mean > 0.90, one-sided |
| H3 | label-shuffled recognition equals chance, 0.25 | mean = 0.25, two-sided |
| H4 | with a pure phase wave (envelope off), acc_ungated at sigma 0.15 is below 0.40 | mean < 0.40, one-sided |
| H5 | auc_phase_scramble of the max overlap gate exceeds 0.90 | mean > 0.90, one-sided |
| H6 | max overlap gate beats wave_scan on auc_time_shift_half_spacing | paired difference > 0, one-sided |
| H7 | balanced accuracy against haar differs between the midpoint and first-best tau rules | paired difference = 0, two-sided |
| H8 | accept_global_phase_rotation exceeds 0.99 (a design property, a known blind spot) | mean > 0.99, one-sided |
| H9 | refuse_time_shift_half_spacing is below 0.50 (the gate does not refuse a wave between stored phases) | mean < 0.50, one-sided |

Label shuffling (H3): each replicate's true labels are permuted uniformly
at random (role `shuffle`) and recognition is scored against the
permuted labels; the expected rate is 1 / number of phases.

## Studies

- A. Recognition and refusal across noise: sigma in 0, 0.05, 0.10, 0.15,
  0.20, 0.30, 0.45, 0.60; matched calibration.
- B. Ablations at sigma 0.15 and 0.30, paired by seed with the default:
  envelope off; width 2, 4, 6, 12, 16, 24, 64; 6 and 8 stored phases
  (chance 1/6 and 1/8); n = 32 and 128, each with the same absolute
  sigma and with sigma scaled by sqrt(64/n) to hold the per-neuron
  signal-to-noise ratio of a unit-norm field fixed; k = 2, 3, 6, 8;
  pacemaker nearest (0, -16), (-10, 8) or (0, -2). Recorded: acc_ungated,
  acc_gated, J_cal, largest cyclic neighbour overlap of stored patterns.
- C. Refusal quality: auc_X and bal_acc_X for the four gates over every
  kind, and the four tau rules (midpoint, first, midpoint_all, median)
  compared on held-out balanced accuracy.
- D. Negative controls: label shuffling (H3), and the refused/not
  refused table for every out-of-library kind at sigma 0.15.
- E. Null: pure phase wave stored (envelope off), sigma 0, 0.05, 0.15,
  with the fraction of probes assigned to phase index 0 (the exact-tie
  winner).
- F. Robustness map of the gate: calibration sigma 0.05, 0.15, 0.30
  against evaluation sigma 0, 0.05, 0.15, 0.30, 0.45, 0.60: tau, J_cal,
  accept_in and refuse_haar.

## Stopping rule

Fixed replicate count (200 per set), fixed resample counts. No optional
stopping, no extra seeds added after any CONFIRM output is seen, and no
change to a hypothesis, threshold or test after the CONFIRM run. CONFIRM
is run once. If CONFIRM is run again (for example after a crash), the
rerun must use unchanged code and the outputs must be identical; this is
checked by committing the result file and re-rendering it in CI.

## Amendments

Any change to this protocol after this commit is listed here with the
commit that made it, and must be committed before the CONFIRM run.
A1 (committed before the CONFIRM run; the DEV run had already been
looked at). The DEV output showed a confound: in-library probes carry
noise (sigma 0.15) while most out-of-library kinds were noise-free, so
a deformed stored wave could out-score a noisy in-library probe and be
accepted simply for being cleaner. Two exploratory additions, neither
touching H1 to H9 or any earlier key:

- Noise-matched control: every out-of-library kind is also generated with
  the same absolute noise as the in-library probes (sigma 0.15). New keys:
  `D/noisy/...` (refusal and mean max overlap) and `Cn/...` (AUC and
  balanced accuracy of the gates, as in C). The noise-free results remain
  the pre-registered ones; the noise-matched results are reported next to
  them, not instead of them.
- Study G: does the phase structure matter? Recognition by a phase-blind
  magnitude-only classifier (argmax cosine between the magnitude profile
  of the probe and each stored magnitude profile) compared with complex
  projection, at every sigma of study A, with the paired difference.

A2 (committed before the CONFIRM run). H3 is a null-retention control:
"supported" cannot mean a rejected null. The control passes if the
Holm-adjusted two-sided p is at least 0.05 AND the 95 % interval of the
mean lies inside 0.23 to 0.27; otherwise it fails and would indicate
leakage between labels and probes. For H7 (two-sided, null 0) the usual
rule applies (supported when the adjusted p is below 0.05), and the size
of the difference is reported next to it because a significant
difference of a fraction of a percentage point is not a practical one.
The ablation difference family is two-sided against 0 with the same
Holm rule. Bootstrap p-values cannot go below about 1/(resamples + 1),
so Holm-adjusted p-values are floored accordingly.

A3 (committed before the CONFIRM run). Smoke runs on Python 3.10 and 3.11
differed from 3.12 and 3.13 in 15 tie-dependent rows (the pure-phase null
and the sigma 0 threshold), because the built-in `sum` changed its float
summation in 3.12. The package now uses exactly rounded sums (`fsum`) in
the normalisation, overlap and projection, after which smoke outputs are
identical on 3.10, 3.11, 3.12 and 3.13. No hypothesis, threshold or test
changed.

The DEV result file was regenerated after these additions; the CONFIRM
file is produced only after these amendments.

## What results do and do not mean

Every result is a property of a seeded toy simulation: random layouts, a
synthetic wave, synthetic noise and synthetic out-of-library fields. A
refusal rate is the fraction of synthetic probes of one stated kind that a
frozen threshold refused. It says nothing about detecting any condition,
and nothing transfers to real physiology or real data. Null and negative
results are reported in full.
