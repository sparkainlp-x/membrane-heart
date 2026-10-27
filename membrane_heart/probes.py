"""Out-of-library probe generators and baseline gate scores (SYNTHETIC).

Every generator takes a ``MembraneHeart`` and a ``random.Random``
and returns a unit-norm complex field of length ``heart.n``. None of
these models any physiological condition: they are labelled
synthetic perturbations of a stored synthetic wave.
"""

import cmath
import math

from .core import normalize, noisy, overlap, phase_scrambled_field, rand_field

OOD_KINDS = (
    "haar",
    "phase_scramble",
    "phase_scramble_envelope",
    "magnitude_permuted",
    "time_shift_half_spacing",
    "time_shift_quarter_spacing",
    "partial_random_half",
    "partial_late_half",
    "stored_plus_noise_0.6",
    "stored_plus_noise_1.0",
    "conjugate_wave",
    "global_phase_rotation",
)

# Kinds that, by construction of |overlap| (blind to global phase),
# are expected to be ACCEPTED; reported separately as design checks.
BLIND_BY_DESIGN = ("global_phase_rotation",)


def _stored(heart, rng):
    return heart.patterns[rng.randrange(heart.n_phases)]


def _renorm_or_fallback(field, rng, heart):
    try:
        return normalize(field)
    except ValueError:  # all-zero after masking: extremely unlikely
        return rand_field(heart.n, rng)


def make_ood(heart, kind, rng):
    """One out-of-library field of the named kind."""
    n = heart.n
    if kind == "haar":
        return rand_field(n, rng)
    if kind == "phase_scramble":
        return phase_scrambled_field(n, rng.getrandbits(48))
    p = _stored(heart, rng)
    if kind == "phase_scramble_envelope":
        return normalize([abs(c) * cmath.exp(1j * rng.uniform(0, 2 * math.pi))
                          for c in p])
    if kind == "magnitude_permuted":
        mags = [abs(c) for c in p]
        rng.shuffle(mags)
        return normalize([m * cmath.exp(1j * cmath.phase(c))
                          for m, c in zip(mags, p)])
    if kind in ("time_shift_half_spacing", "time_shift_quarter_spacing"):
        spacing = heart.period / heart.n_phases
        frac = 0.5 if kind == "time_shift_half_spacing" else 0.25
        i = rng.randrange(heart.n_phases)
        return heart.field(heart.phase_times[i] + frac * spacing)
    if kind == "partial_random_half":
        keep = set(rng.sample(range(n), n // 2))
        return _renorm_or_fallback(
            [c if i in keep else 0j for i, c in enumerate(p)], rng, heart)
    if kind == "partial_late_half":
        cut = sorted(heart.delays)[n // 2]
        return _renorm_or_fallback(
            [c if heart.delays[i] <= cut else 0j for i, c in enumerate(p)],
            rng, heart)
    if kind.startswith("stored_plus_noise_"):
        return noisy(p, float(kind.rsplit("_", 1)[1]), rng)
    if kind == "conjugate_wave":
        return [c.conjugate() for c in p]
    if kind == "global_phase_rotation":
        rot = cmath.exp(1j * rng.uniform(0, 2 * math.pi))
        return [c * rot for c in p]
    raise ValueError(f"unknown out-of-library kind: {kind!r}")


class GateScores:
    """Scores for the primary gate and simple baselines.

    All scores are 'higher = more library-like' so one AUC convention
    (in-library as the positive class) applies to each.

    - ``max_overlap``: the gate in this package.
    - ``wave_scan``: best |<field, wave(t)>| over ``scan_points``
      evenly spaced times in one period (a continuous-phase
      coherence gate; accepts waves at any phase, stored or not).
    - ``magnitude_profile``: best cosine similarity between |field|
      and a stored magnitude profile (phase-blind).
    - ``constant``: a trivial gate that gives every field the same
      score (AUC 0.5 by tie convention).
    """

    NAMES = ("max_overlap", "wave_scan", "magnitude_profile", "constant")

    def __init__(self, heart, scan_points=40):
        self.heart = heart
        self.scan_fields = [heart.field(i * heart.period / scan_points)
                            for i in range(scan_points)]
        self.mag_profiles = [normalize([abs(c) for c in p])
                             for p in heart.patterns]

    def max_overlap(self, field):
        return self.heart.max_overlap(field)

    def wave_scan(self, field):
        return max(abs(overlap(field, w)) for w in self.scan_fields)

    def magnitude_profile(self, field):
        mags = [abs(c) for c in field]
        norm = math.sqrt(math.fsum(m * m for m in mags))
        if norm == 0:
            return 0.0
        return max(math.fsum(a * b for a, b in zip(mags, prof)) / norm
                   for prof in self.mag_profiles)

    def classify_magnitude_only(self, field):
        """Phase-blind recognition: argmax cosine of |field| with the
        stored magnitude profiles (index, or None for a zero field)."""
        mags = [abs(c) for c in field]
        norm = math.sqrt(math.fsum(m * m for m in mags))
        if norm == 0:
            return None
        sims = [math.fsum(a * b for a, b in zip(mags, prof)) / norm
                for prof in self.mag_profiles]
        return max(range(len(sims)), key=lambda i: sims[i])

    def constant(self, field):
        return 0.0

    def score(self, name, field):
        if name not in self.NAMES:
            raise ValueError(f"unknown gate: {name!r}")
        return getattr(self, name)(field)
