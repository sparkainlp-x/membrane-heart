"""The eight tests supplied with v0.1.0 (adapted: see DESIGN.md)."""

import math
import unittest

from membrane_heart import (
    HeartGeometry,
    MembraneHeart,
    heart_curve_point,
    noisy,
    rand_field,
)
import random


class TestMembraneHeart(unittest.TestCase):
    def test_curve_at_zero(self):
        x, y = heart_curve_point(0.0)
        self.assertAlmostEqual(x, 0.0)
        self.assertAlmostEqual(y, 5.0)

    def test_geometry_and_delays(self):
        geo = HeartGeometry(n=64, seed=42)
        self.assertEqual(len(geo.neurons), 64)
        self.assertEqual(geo.delays[geo.pacemaker_id], 0.0)
        self.assertTrue(all(math.isfinite(d) for d in geo.delays))
        self.assertGreater(max(geo.delays), 0.0)

    def test_field_is_unit(self):
        heart = MembraneHeart(n=64, seed=42)
        for t in (0.0, 10.0, 33.3):
            f = heart.field(t)
            self.assertEqual(len(f), 64)
            self.assertAlmostEqual(
                math.sqrt(sum(abs(c) ** 2 for c in f)), 1.0, places=9)

    def test_clean_phase_recognition(self):
        heart = MembraneHeart(n=64, seed=42)
        # v0.1.0 used decide() with tau=None as ungated projection;
        # decide() now fails closed, so use classify() (see DESIGN.md).
        for i, t in enumerate((0.0, 10.0, 20.0, 30.0)):
            self.assertEqual(heart.classify(heart.field(t)),
                             heart.PHASE_NAMES[i])

    def test_noisy_recognition(self):
        heart = MembraneHeart(n=64, seed=42)
        rng = random.Random(7)
        ok = 0
        trials = 40
        for k in range(trials):
            t = (k % 4) * 10.0
            probe = noisy(heart.field(t), 0.15, rng)
            name = heart.classify(probe)
            ok += name == heart.PHASE_NAMES[k % 4]
        self.assertGreaterEqual(ok / trials, 0.90)

    def test_coherence_perfect_vs_scrambled(self):
        heart = MembraneHeart(n=64, seed=42)
        self.assertAlmostEqual(heart.coherence(heart.field(5.0), 5.0),
                               1.0, places=9)
        scr = heart.scrambled_field(123)
        self.assertLess(heart.coherence(scr, 5.0), 0.35)

    def test_gate_refuses_scrambled(self):
        heart = MembraneHeart(n=64, seed=42)
        rng = random.Random(11)
        in_probes = [noisy(heart.field((k % 4) * 10.0), 0.15, rng)
                     for k in range(100)]
        ood_probes = [rand_field(64, rng) for _ in range(100)]
        tau, j = heart.calibrate(in_probes, ood_probes)
        self.assertGreater(j, 0.90)
        self.assertGreater(tau, 0.3)
        self.assertLess(tau, 0.95)
        # Fresh probes, never used in calibration.
        rng2 = random.Random(99)
        accepted_in = sum(
            1 for k in range(50)
            if heart.decide(noisy(heart.field((k % 4) * 10.0), 0.15,
                                  rng2))[0] == "accept")
        rejected_scr = sum(
            1 for k in range(50)
            if heart.decide(heart.scrambled_field(1000 + k))[0] == "reject")
        self.assertGreaterEqual(accepted_in / 50, 0.90)
        self.assertGreaterEqual(rejected_scr / 50, 0.90)

    def test_determinism(self):
        a = MembraneHeart(n=48, seed=123)
        b = MembraneHeart(n=48, seed=123)
        self.assertEqual(a.geometry.delays, b.geometry.delays)
        self.assertEqual(a.patterns, b.patterns)


if __name__ == "__main__":
    unittest.main(verbosity=2)
