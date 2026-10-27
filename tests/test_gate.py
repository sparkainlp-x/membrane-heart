import math
import random
import unittest

from membrane_heart import (MembraneHeart, calibrate_tau, noisy,
                            rand_field)


def calibrated(seed=42, n=64):
    heart = MembraneHeart(n=n, seed=seed)
    rng = random.Random(11)
    ins = [noisy(heart.patterns[k % 4], 0.15, rng) for k in range(100)]
    ood = [rand_field(n, rng) for _ in range(100)]
    heart.calibrate(ins, ood)
    return heart


class TestCalibrateTau(unittest.TestCase):
    def test_separated_scores_midpoint(self):
        tau, j = calibrate_tau([0.8, 0.9, 0.85], [0.1, 0.2, 0.15])
        self.assertEqual(j, 1.0)
        self.assertAlmostEqual(tau, 0.5, delta=0.02)

    def test_first_vs_midpoint_on_gap(self):
        ins, ood = [0.8] * 5, [0.1] * 5
        first, _ = calibrate_tau(ins, ood, grid=100, strategy="first")
        mid, _ = calibrate_tau(ins, ood, grid=100, strategy="midpoint")
        self.assertAlmostEqual(first, 0.11, places=9)  # edge of the gap
        self.assertAlmostEqual(mid, 0.455, places=9)

    def test_non_contiguous_plateau_midpoint_stays_in_a_plateau(self):
        # Two plateaus of J = 0.5: tau in (0.1, 0.5] and (0.7, 0.9],
        # separated by a dip (J = 0 on (0.5, 0.7]). The v0.1.0 rule
        # (midpoint of the first and last maximal-J tau) lands at 0.505,
        # inside the dip.
        ins = [0.5] * 3 + [0.9] * 3
        ood = [0.1] * 3 + [0.7] * 3

        def j_at(tau):
            return (sum(v >= tau for v in ins) / 6
                    - sum(v >= tau for v in ood) / 6)

        tau_new, j_new = calibrate_tau(ins, ood, grid=100)
        tau_old, j_old = calibrate_tau(ins, ood, grid=100,
                                       strategy="midpoint_all")
        self.assertAlmostEqual(j_new, 0.5)
        self.assertAlmostEqual(j_at(tau_new), 0.5)
        self.assertAlmostEqual(tau_old, 0.505, places=9)
        self.assertAlmostEqual(j_at(tau_old), 0.0)
        self.assertGreater(tau_new, 0.1)
        self.assertLessEqual(tau_new, 0.5)

    def test_median_strategy_and_unknown_strategy(self):
        t, _ = calibrate_tau([0.9] * 4, [0.1] * 4, strategy="median")
        self.assertTrue(0.1 < t <= 0.9)
        with self.assertRaises(ValueError):
            calibrate_tau([1], [0], strategy="nope")

    def test_empty_and_nonfinite_raise(self):
        with self.assertRaises(ValueError):
            calibrate_tau([], [0.1])
        with self.assertRaises(ValueError):
            calibrate_tau([0.5], [])
        with self.assertRaises(ValueError):
            calibrate_tau([float("nan")], [0.1])
        with self.assertRaises(ValueError):
            calibrate_tau([0.5], [0.1], grid=0)

    def test_fully_overlapping_scores_give_low_j(self):
        tau, j = calibrate_tau([0.5] * 10, [0.5] * 10)
        self.assertEqual(j, 0.0)
        self.assertTrue(0.0 <= tau <= 1.0)

    def test_tie_semantics_accept_at_threshold(self):
        heart = MembraneHeart(n=16, seed=1)
        f = heart.patterns[0]
        heart.tau = heart.max_overlap(f)
        self.assertEqual(heart.decide(f)[0], "accept")
        heart.tau = heart.max_overlap(f) + 1e-9
        self.assertEqual(heart.decide(f)[0], "reject")

    def test_calibration_is_not_mutating_inputs(self):
        heart = MembraneHeart(n=32, seed=3)
        rng = random.Random(1)
        ins = [noisy(heart.patterns[0], 0.1, rng) for _ in range(10)]
        ood = [rand_field(32, rng) for _ in range(10)]
        before = [list(f) for f in ins + ood]
        heart.calibrate(ins, ood)
        self.assertEqual(before, [list(f) for f in ins + ood])
        self.assertIsNotNone(heart.tau)

    def test_calibrate_empty_probes_raises_value_error(self):
        heart = MembraneHeart(n=16, seed=1)
        with self.assertRaises(ValueError):
            heart.calibrate([], [rand_field(16, random.Random(1))])
        self.assertIsNone(heart.tau)


class TestGateInvariants(unittest.TestCase):
    def test_uncalibrated_gate_fails_closed(self):
        heart = MembraneHeart(n=32, seed=2)
        verdict, name, _ = heart.decide(heart.patterns[1])
        self.assertEqual((verdict, name), ("reject", None))
        self.assertEqual(heart.classify(heart.patterns[1]), "atrial")

    def test_zero_field_rejected_not_error(self):
        heart = calibrated(n=64)
        zero = [0j] * 64
        self.assertEqual(heart.decide(zero)[0], "reject")
        self.assertIsNone(heart.classify(zero))
        self.assertTrue(math.isfinite(heart.max_overlap(zero)))

    def test_nan_and_inf_fields_rejected(self):
        heart = calibrated()
        for bad in (complex(float("nan"), 0), complex(float("inf"), 0)):
            f = list(heart.patterns[0])
            f[3] = bad
            self.assertEqual(heart.decide(f)[0], "reject")
            self.assertIsNone(heart.classify(f))
            self.assertTrue(math.isnan(heart.max_overlap(f)))

    def test_wrong_length_raises(self):
        heart = calibrated()
        with self.assertRaises(ValueError):
            heart.decide([1 + 0j] * 10)
        with self.assertRaises(ValueError):
            heart.coherence([1 + 0j] * 63, 0.0)

    def test_decide_does_not_mutate_input(self):
        heart = calibrated()
        f = noisy(heart.patterns[2], 0.1, random.Random(4))
        before = list(f)
        heart.decide(f)
        heart.project(f)
        heart.max_overlap(f)
        self.assertEqual(before, f)

    def test_probabilities_sum_to_one(self):
        heart = calibrated()
        _, _, probs = heart.decide(noisy(heart.patterns[0], 0.1,
                                         random.Random(5)))
        self.assertAlmostEqual(sum(probs), 1.0, places=12)

    def test_global_phase_rotation_is_accepted_by_design(self):
        heart = calibrated()
        rot = [c * complex(math.cos(1.1), math.sin(1.1))
               for c in heart.patterns[3]]
        verdict, name, _ = heart.decide(rot)
        self.assertEqual((verdict, name), ("accept", "recovery"))

    def test_gate_threshold_monotone(self):
        heart = calibrated()
        rng = random.Random(8)
        probes = [rand_field(64, rng) for _ in range(30)]
        probes += [noisy(heart.patterns[1], 0.3, rng) for _ in range(30)]
        heart.tau = 0.2
        loose = sum(heart.decide(f)[0] == "accept" for f in probes)
        heart.tau = 0.6
        strict = sum(heart.decide(f)[0] == "accept" for f in probes)
        self.assertLessEqual(strict, loose)

    def test_pattern_gram_diagonal_and_symmetry(self):
        heart = MembraneHeart(n=32, seed=4)
        g = heart.pattern_gram()
        for i in range(4):
            self.assertAlmostEqual(g[i][i], 1.0, places=9)
            for j in range(4):
                self.assertAlmostEqual(g[i][j], g[j][i], places=9)
        self.assertLess(heart.max_neighbour_overlap(), 1.0)


class TestConstruction(unittest.TestCase):
    def test_parameters_validated(self):
        for kw in ({"period": 0}, {"period": float("inf")}, {"width": 0},
                   {"n_phases": 1}):
            with self.assertRaises(ValueError):
                MembraneHeart(n=16, seed=1, **kw)

    def test_n_phases_and_names(self):
        h6 = MembraneHeart(n=32, seed=1, n_phases=6)
        self.assertEqual(len(h6.patterns), 6)
        self.assertEqual(h6.phase_names[0], "phase_0")
        h4 = MembraneHeart(n=32, seed=1)
        self.assertEqual(h4.phase_names, MembraneHeart.PHASE_NAMES)
        self.assertEqual(h4.phase_times, (0.0, 10.0, 20.0, 30.0))

    def test_pure_phase_patterns_have_equal_gram_off_diagonal(self):
        # The documented failure: |overlap| cannot tell snapshots apart.
        h = MembraneHeart(n=32, seed=1, envelope=False)
        g = h.pattern_gram()
        for i in range(4):
            for j in range(4):
                self.assertAlmostEqual(g[i][j], 1.0, places=9)

    def test_enveloped_patterns_are_distinguishable(self):
        h = MembraneHeart(n=64, seed=42)
        self.assertLess(h.max_neighbour_overlap(), 0.9)

    def test_determinism_bit_identical(self):
        def run():
            h = MembraneHeart(n=48, seed=9)
            rng = random.Random(3)
            ins = [noisy(h.patterns[k % 4], 0.15, rng) for k in range(40)]
            ood = [rand_field(48, rng) for _ in range(40)]
            tau, j = h.calibrate(ins, ood)
            return (h.delays, h.patterns, tau, j,
                    [h.decide(f)[0] for f in ins + ood])
        self.assertEqual(run(), run())


if __name__ == "__main__":
    unittest.main()
