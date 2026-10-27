import math
import random
import unittest

from membrane_heart import MembraneHeart
from membrane_heart.probes import (BLIND_BY_DESIGN, GateScores, OOD_KINDS,
                                   make_ood)


def norm(f):
    return math.sqrt(sum(abs(c) ** 2 for c in f))


class TestProbes(unittest.TestCase):
    def setUp(self):
        self.h = MembraneHeart(n=64, seed=42)

    def test_every_kind_gives_unit_finite_field_of_right_length(self):
        for kind in OOD_KINDS:
            f = make_ood(self.h, kind, random.Random(1))
            self.assertEqual(len(f), 64, kind)
            self.assertAlmostEqual(norm(f), 1.0, places=9, msg=kind)
            self.assertTrue(all(math.isfinite(c.real) and
                                math.isfinite(c.imag) for c in f), kind)

    def test_every_kind_is_deterministic_given_rng(self):
        for kind in OOD_KINDS:
            a = make_ood(self.h, kind, random.Random(7))
            b = make_ood(self.h, kind, random.Random(7))
            self.assertEqual(a, b, kind)

    def test_unknown_kind_raises(self):
        with self.assertRaises(ValueError):
            make_ood(self.h, "bogus", random.Random(1))

    def test_make_ood_does_not_mutate_stored_patterns(self):
        before = [list(p) for p in self.h.patterns]
        for kind in OOD_KINDS:
            make_ood(self.h, kind, random.Random(2))
        self.assertEqual(before, [list(p) for p in self.h.patterns])

    def test_blind_by_design_kind_has_max_overlap_one(self):
        for kind in BLIND_BY_DESIGN:
            f = make_ood(self.h, kind, random.Random(3))
            self.assertAlmostEqual(self.h.max_overlap(f), 1.0, places=9)

    def test_time_shift_between_stored_phases_overlaps_strongly(self):
        f = make_ood(self.h, "time_shift_quarter_spacing", random.Random(4))
        self.assertGreater(self.h.max_overlap(f), 0.8)

    def test_partial_late_half_zeroes_far_neurons(self):
        f = make_ood(self.h, "partial_late_half", random.Random(5))
        zeros = sum(1 for c in f if c == 0)
        self.assertGreaterEqual(zeros, 20)

    def test_gate_scores_ranges_and_constant(self):
        gs = GateScores(self.h, scan_points=20)
        p = self.h.patterns[0]
        self.assertAlmostEqual(gs.score("max_overlap", p), 1.0, places=9)
        self.assertAlmostEqual(gs.score("wave_scan", p), 1.0, places=9)
        self.assertAlmostEqual(gs.score("magnitude_profile", p), 1.0,
                               places=9)
        self.assertEqual(gs.score("constant", p), 0.0)
        with self.assertRaises(ValueError):
            gs.score("bogus", p)

    def test_wave_scan_at_least_max_overlap_when_scan_covers_stored(self):
        gs = GateScores(self.h, scan_points=40)  # includes stored times
        f = make_ood(self.h, "haar", random.Random(6))
        self.assertGreaterEqual(gs.wave_scan(f) + 1e-12,
                                gs.max_overlap(f))

    def test_magnitude_profile_blind_to_phase_scramble_of_envelope(self):
        gs = GateScores(self.h, scan_points=10)
        f = make_ood(self.h, "phase_scramble_envelope", random.Random(8))
        self.assertAlmostEqual(gs.magnitude_profile(f), 1.0, places=9)
        self.assertLess(gs.max_overlap(f), 0.6)

    def test_magnitude_profile_zero_field(self):
        gs = GateScores(self.h, scan_points=10)
        self.assertEqual(gs.magnitude_profile([0j] * 64), 0.0)


if __name__ == "__main__":
    unittest.main()
